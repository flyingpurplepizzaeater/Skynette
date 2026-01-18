# src/ui/views/ai_hub/model_library.py
"""Model Library tab component.

Extracted from AIHubView to improve modularity and testability.
Contains My Models, Hugging Face, Ollama, and Import sub-tabs.
"""

import asyncio

import flet as ft

from src.ai.models.hub import DownloadProgress, ModelInfo, get_hub
from src.ui.theme import Theme

# Ollama library models
OLLAMA_LIBRARY_MODELS = [
    {"name": "llama3.2", "desc": "Meta's latest - fast and efficient", "size": "1B/3B"},
    {"name": "mistral", "desc": "Excellent reasoning", "size": "7B"},
    {"name": "codellama", "desc": "Code specialist", "size": "7B-70B"},
    {"name": "deepseek-coder", "desc": "Code generation", "size": "1.3B-33B"},
    {"name": "phi3", "desc": "Microsoft's efficient model", "size": "mini-medium"},
    {"name": "gemma2", "desc": "Google's open model", "size": "2B-27B"},
]


class ModelLibraryTab(ft.Column):
    """Model Library tab with sub-tabs for different model sources.

    Sub-tabs:
    - My Models: Locally downloaded models
    - Hugging Face: Search and download from HuggingFace
    - Ollama: Integration with local Ollama instance
    - Import: Import local GGUF files
    """

    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self.hub = get_hub()
        self.expand = True

        # UI state
        self.download_cards: dict[str, ft.Container] = {}
        self.installed_list = None
        self.recommended_list = None
        self.hf_search_field = None
        self.hf_url_field = None
        self.hf_search_results = None
        self.file_picker = None

        # Ollama status UI elements
        self.ollama_status_icon = None
        self.ollama_status_text = None

    def build(self):
        """Build the Model Library tab with sub-tabs."""
        # Create tab headers (Flet 0.80+ API: Tab only has label/icon, no content)
        tab_bar = ft.TabBar(
            tabs=[
                ft.Tab(label="My Models", icon=ft.Icons.FOLDER),
                ft.Tab(label="Hugging Face", icon=ft.Icons.CLOUD_DOWNLOAD),
                ft.Tab(label="Ollama", icon=ft.Icons.TERMINAL),
                ft.Tab(label="Import", icon=ft.Icons.UPLOAD_FILE),
            ],
        )

        # Create tab content view (each control corresponds to a tab)
        tab_view = ft.TabBarView(
            controls=[
                self._build_installed_tab(),
                self._build_huggingface_tab(),
                self._build_ollama_tab(),
                self._build_import_tab(),
            ],
            expand=True,
        )

        # Wrap in Tabs controller
        return ft.Container(
            content=ft.Tabs(
                content=ft.Column(
                    controls=[tab_bar, tab_view],
                    expand=True,
                ),
                length=4,
                expand=True,
            ),
            expand=True,
        )

    def refresh_models(self):
        """Refresh the model list."""
        self.hub.scan_local_models()

    # ==================== My Models Tab ====================

    def _build_installed_tab(self):
        """Build the My Models (installed) tab."""
        local_models = self.hub.get_local_models()

        if not local_models:
            self.installed_list = ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=Theme.TEXT_SECONDARY),
                                ft.Text(
                                    "No Models Downloaded",
                                    size=18,
                                    weight=ft.FontWeight.W_600,
                                    color=Theme.TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    "Download models from the Download tab to use local AI",
                                    size=14,
                                    color=Theme.TEXT_SECONDARY,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Container(height=16),
                                ft.Text(
                                    f"Models folder: {self.hub.models_dir}",
                                    size=11,
                                    color=Theme.TEXT_MUTED,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        padding=ft.Padding.all(48),
                        alignment=ft.alignment.Alignment(0, 0),
                        expand=True,
                    ),
                ],
                expand=True,
            )
        else:
            self.installed_list = ft.Column(
                controls=[self._build_installed_model_card(m) for m in local_models],
                scroll=ft.ScrollMode.AUTO,
                spacing=Theme.SPACING_SM,
            )

        return ft.Container(
            content=self.installed_list,
            padding=Theme.SPACING_MD,
            expand=True,
        )

    def _build_installed_model_card(self, model: ModelInfo):
        """Build a card for an installed model."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.MEMORY,
                        color=Theme.SUCCESS,
                        size=32,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                model.name,
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=Theme.TEXT_PRIMARY,
                            ),
                            ft.Text(
                                f"{model.quantization} - {model.size_display}",
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Ready",
                            size=11,
                            color=Theme.SUCCESS,
                        ),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        bgcolor=Theme.SUCCESS + "20",
                        border_radius=12,
                    ),
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            ft.PopupMenuItem(
                                content=ft.Text("Set as default"),
                                on_click=lambda e, m=model: self._set_default_model(m),
                            ),
                            ft.PopupMenuItem(
                                content=ft.Text("Delete"),
                                on_click=lambda e, m=model: self._delete_model(m),
                            ),
                        ],
                    ),
                ],
                spacing=Theme.SPACING_MD,
            ),
            bgcolor=Theme.SURFACE,
            padding=Theme.SPACING_MD,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(1, Theme.BORDER),
        )

    def _set_default_model(self, model: ModelInfo):
        """Set a model as the default for local inference."""
        from src.data.storage import get_storage

        storage = get_storage()
        storage.set_setting("default_local_model", model.id)

        if self._page:
            self._page.open(
                ft.SnackBar(
                    content=ft.Text(f"Default model set to: {model.name}"),
                    bgcolor=Theme.SUCCESS,
                )
            )

    def _delete_model(self, model: ModelInfo):
        """Delete a downloaded model."""
        self.hub.delete_model(model.id)
        self.refresh_models()
        if self._page:
            self._page.update()

    # ==================== Hugging Face Tab ====================

    def _build_huggingface_tab(self):
        """Build the Hugging Face tab with search and recommended models."""
        recommended = self.hub.get_recommended_models()

        model_cards = []
        for model in recommended:
            card = self._build_recommended_model_card(model)
            self.download_cards[model.id] = card
            model_cards.append(card)

        self.recommended_list = ft.Column(
            controls=model_cards,
            spacing=Theme.SPACING_SM,
        )

        # Search field for HF
        self.hf_search_field = ft.TextField(
            hint_text="Search Hugging Face for GGUF models...",
            expand=True,
            border_color=Theme.BORDER,
            on_submit=self._search_huggingface,
        )

        # URL paste field
        self.hf_url_field = ft.TextField(
            hint_text="Paste Hugging Face URL (e.g., TheBloke/Llama-2-7B-GGUF)...",
            expand=True,
            border_color=Theme.BORDER,
        )

        # Search results area
        self.hf_search_results = ft.Column(
            controls=[],
            spacing=Theme.SPACING_SM,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Search section
                    ft.Text(
                        "Search Hugging Face",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Row(
                        controls=[
                            self.hf_search_field,
                            ft.Button(
                                "Search",
                                icon=ft.Icons.SEARCH,
                                bgcolor=Theme.PRIMARY,
                                on_click=self._search_huggingface,
                            ),
                        ],
                        spacing=8,
                    ),
                    self.hf_search_results,
                    ft.Container(height=Theme.SPACING_MD),
                    ft.Divider(color=Theme.BORDER),
                    ft.Container(height=Theme.SPACING_MD),
                    # URL paste section
                    ft.Text(
                        "Add from URL",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Paste a Hugging Face model URL or repo ID",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Row(
                        controls=[
                            self.hf_url_field,
                            ft.Button(
                                "Add",
                                icon=ft.Icons.ADD,
                                bgcolor=Theme.PRIMARY,
                                on_click=self._add_from_hf_url,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Container(height=Theme.SPACING_MD),
                    ft.Divider(color=Theme.BORDER),
                    ft.Container(height=Theme.SPACING_MD),
                    # Recommended section
                    ft.Text(
                        "Recommended Models",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Popular open-source models optimized for local use",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Container(height=Theme.SPACING_SM),
                    self.recommended_list,
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_MD,
            expand=True,
        )

    def _build_recommended_model_card(self, model: ModelInfo):
        """Build a card for a recommended model."""
        is_downloaded = model.is_downloaded
        progress = self.hub.get_download_progress(model.id)
        is_downloading = progress and progress.status == "downloading"

        # Tags based on metadata
        tags = []
        for tag in model.metadata.get("recommended_for", [])[:3]:
            tags.append(
                ft.Container(
                    content=ft.Text(tag, size=10, color=Theme.PRIMARY),
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    bgcolor=Theme.PRIMARY + "20",
                    border_radius=8,
                )
            )

        status_control = None
        action_control = None

        if is_downloading:
            status_control = ft.Column(
                controls=[
                    ft.ProgressBar(
                        value=progress.percent / 100,
                        width=120,
                        color=Theme.PRIMARY,
                        bgcolor=Theme.BORDER,
                    ),
                    ft.Text(
                        f"{progress.percent:.0f}%",
                        size=11,
                        color=Theme.TEXT_SECONDARY,
                    ),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.END,
            )
            action_control = ft.IconButton(
                icon=ft.Icons.CANCEL,
                icon_color=Theme.ERROR,
                tooltip="Cancel",
            )
        elif is_downloaded:
            status_control = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color=Theme.SUCCESS),
                        ft.Text("Installed", size=11, color=Theme.SUCCESS),
                    ],
                    spacing=4,
                ),
            )
            action_control = ft.Container()
        else:
            action_control = ft.Button(
                "Download",
                icon=ft.Icons.DOWNLOAD,
                bgcolor=Theme.PRIMARY,
                on_click=lambda e, m=model: self._start_download(m),
            )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.AUTO_AWESOME if not is_downloaded else ft.Icons.CHECK_CIRCLE,
                        color=Theme.PRIMARY if not is_downloaded else Theme.SUCCESS,
                        size=32,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                model.name,
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=Theme.TEXT_PRIMARY,
                            ),
                            ft.Text(
                                model.description,
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                                max_lines=2,
                            ),
                            ft.Row(controls=tags, spacing=4) if tags else ft.Container(),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                model.size_display,
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                            ),
                            status_control if status_control else ft.Container(),
                        ],
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                    ),
                    action_control,
                ],
                spacing=Theme.SPACING_MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=Theme.SURFACE,
            padding=Theme.SPACING_MD,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(1, Theme.BORDER),
        )

    def _start_download(self, model: ModelInfo):
        """Start downloading a model."""
        async def do_download():
            def on_progress(progress: DownloadProgress):
                # Update UI
                if model.id in self.download_cards and self._page:
                    # Rebuild the card with new progress
                    new_card = self._build_recommended_model_card(model)
                    # Find and replace
                    if self.recommended_list:
                        for i, ctrl in enumerate(self.recommended_list.controls):
                            if ctrl == self.download_cards[model.id]:
                                self.recommended_list.controls[i] = new_card
                                self.download_cards[model.id] = new_card
                                break
                    self._page.update()

            try:
                await self.hub.download_model(model, on_progress)
                # Refresh after complete
                self.refresh_models()
                if self._page:
                    self._page.update()
            except Exception as ex:
                print(f"Download failed: {ex}")

        if self._page:
            asyncio.create_task(do_download())

    def _search_huggingface(self, e):
        """Search Hugging Face for models."""
        query = self.hf_search_field.value
        if not query:
            return

        async def do_search():
            from src.ai.models.sources.huggingface import HuggingFaceSource
            source = HuggingFaceSource()
            results = await source.search(query, limit=10)

            self.hf_search_results.controls.clear()
            if not results.models:
                self.hf_search_results.controls.append(
                    ft.Text("No models found", color=Theme.TEXT_SECONDARY)
                )
            else:
                for model in results.models:
                    self.hf_search_results.controls.append(
                        self._build_hf_search_result_card(model)
                    )
            if self._page:
                self._page.update()

        if self._page:
            asyncio.create_task(do_search())

    def _build_hf_search_result_card(self, model):
        """Build a search result card for HF models."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.AUTO_AWESOME, color=Theme.PRIMARY, size=24),
                    ft.Column(
                        controls=[
                            ft.Text(model.name, size=13, weight=ft.FontWeight.W_600, color=Theme.TEXT_PRIMARY),
                            ft.Text(
                                model.description[:80] + "..." if len(model.description) > 80 else model.description,
                                size=11,
                                color=Theme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Button(
                        "View",
                        icon=ft.Icons.VISIBILITY,
                        bgcolor=Theme.SURFACE,
                        on_click=lambda e, m=model: self._view_hf_model(m),
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
            bgcolor=Theme.SURFACE,
            padding=Theme.SPACING_SM,
            border_radius=Theme.RADIUS_SM,
            border=ft.Border.all(1, Theme.BORDER),
        )

    def _add_from_hf_url(self, e):
        """Add model from Hugging Face URL."""
        url = self.hf_url_field.value
        if not url:
            return

        async def do_add():
            from src.ai.models.sources.huggingface import HuggingFaceSource
            source = HuggingFaceSource()

            try:
                # Validate and get model info
                model_info = await source.validate_url(url)
                if model_info:
                    # Show model details dialog
                    self._show_hf_model_dialog(model_info)
                else:
                    if self._page:
                        self._page.open(
                            ft.SnackBar(
                                content=ft.Text("Could not find model. Check the URL."),
                                bgcolor=Theme.ERROR,
                            )
                        )
            except Exception as ex:
                if self._page:
                    self._page.open(
                        ft.SnackBar(
                            content=ft.Text(f"Error: {ex}"),
                            bgcolor=Theme.ERROR,
                        )
                    )

        if self._page:
            asyncio.create_task(do_add())

    def _view_hf_model(self, model):
        """View HF model details and select files to download."""
        self._show_hf_model_dialog(model)

    def _show_hf_model_dialog(self, model):
        """Show dialog with model details and file selection."""
        files_list = ft.Column(controls=[], spacing=8, scroll=ft.ScrollMode.AUTO)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(model.name),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            model.description[:200] + "..." if len(model.description) > 200 else model.description,
                            size=12,
                            color=Theme.TEXT_SECONDARY,
                        ),
                        ft.Container(height=8),
                        ft.Text("Available Files:", size=14, weight=ft.FontWeight.W_600),
                        ft.Container(height=4),
                        ft.Container(
                            content=files_list,
                            height=250,
                        ),
                    ],
                    tight=True,
                ),
                width=450,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._page.close(dialog) if self._page else None),
            ],
        )

        async def load_files():
            from src.ai.models.sources.huggingface import HuggingFaceSource
            source = HuggingFaceSource()

            files_list.controls.clear()
            files_list.controls.append(
                ft.Text("Loading files...", color=Theme.TEXT_SECONDARY)
            )
            if self._page:
                self._page.update()

            try:
                files = await source.get_model_files(model.source_url or model.id.replace("--", "/"))
                files_list.controls.clear()

                # Files are already filtered for GGUF by get_model_files
                if not files:
                    files_list.controls.append(
                        ft.Text("No GGUF files found in this repository", color=Theme.WARNING)
                    )
                else:
                    for f in files:
                        size_display = f.get("size_display", "")
                        filename = f.get("filename", "")
                        quant = f.get("quantization", "")
                        files_list.controls.append(
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.INSERT_DRIVE_FILE, size=20, color=Theme.PRIMARY),
                                        ft.Column(
                                            controls=[
                                                ft.Text(filename, size=12, weight=ft.FontWeight.W_500),
                                                ft.Text(f"{quant} - {size_display}", size=11, color=Theme.TEXT_MUTED),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                        ft.Button(
                                            "Download",
                                            icon=ft.Icons.DOWNLOAD,
                                            bgcolor=Theme.PRIMARY,
                                            on_click=lambda e, file=f: self._download_hf_file(model, file, dialog),
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                padding=8,
                                bgcolor=Theme.SURFACE,
                                border_radius=4,
                            )
                        )
                if self._page:
                    self._page.update()
            except Exception as ex:
                files_list.controls.clear()
                files_list.controls.append(
                    ft.Text(f"Error loading files: {ex}", color=Theme.ERROR)
                )
                if self._page:
                    self._page.update()

        if self._page:
            self._page.open(dialog)
            asyncio.create_task(load_files())

    def _download_hf_file(self, model, file_info, dialog):
        """Download a specific file from HF model."""
        async def do_download():
            from src.ai.models.sources.huggingface import HuggingFaceSource
            source = HuggingFaceSource()

            filename = file_info.get("filename", "")

            if self._page:
                self._page.close(dialog)
                self._page.open(
                    ft.SnackBar(
                        content=ft.Text(f"Downloading {filename}..."),
                        bgcolor=Theme.PRIMARY,
                    )
                )

            try:
                def on_progress(progress):
                    # Could show progress in a dialog, for now just track internally
                    pass

                await source.download(
                    model,
                    self.hub.models_dir,
                    on_progress,
                    filename=filename,
                )

                if self._page:
                    self._page.open(
                        ft.SnackBar(
                            content=ft.Text(f"Downloaded: {filename}"),
                            bgcolor=Theme.SUCCESS,
                        )
                    )
                    self.refresh_models()
                    self._page.update()

            except Exception as ex:
                if self._page:
                    self._page.open(
                        ft.SnackBar(
                            content=ft.Text(f"Download failed: {ex}"),
                            bgcolor=Theme.ERROR,
                        )
                    )

        if self._page:
            asyncio.create_task(do_download())

    # ==================== Ollama Tab ====================

    def _build_ollama_tab(self):
        """Build the Ollama integration tab."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Status section
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.INFO_OUTLINE, color=Theme.PRIMARY),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            "Ollama Integration",
                                            size=16,
                                            weight=ft.FontWeight.W_600,
                                            color=Theme.TEXT_PRIMARY,
                                        ),
                                        ft.Text(
                                            "Connect to your local Ollama instance to use and manage models",
                                            size=12,
                                            color=Theme.TEXT_SECONDARY,
                                        ),
                                    ],
                                    spacing=4,
                                    expand=True,
                                ),
                                ft.Button(
                                    "Check Status",
                                    icon=ft.Icons.REFRESH,
                                    bgcolor=Theme.SURFACE,
                                    on_click=self._check_ollama_status,
                                ),
                            ],
                            spacing=Theme.SPACING_MD,
                        ),
                        bgcolor=Theme.SURFACE,
                        padding=Theme.SPACING_MD,
                        border_radius=Theme.RADIUS_MD,
                        border=ft.Border.all(1, Theme.BORDER),
                    ),
                    ft.Container(height=Theme.SPACING_MD),
                    # Status indicator
                    self._build_ollama_status_indicator(),
                    ft.Container(height=Theme.SPACING_MD),
                    ft.Divider(color=Theme.BORDER),
                    ft.Container(height=Theme.SPACING_MD),
                    # Available models
                    ft.Text(
                        "Ollama Library",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Popular models available in the Ollama library",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Container(height=Theme.SPACING_SM),
                    self._build_ollama_library_list(),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_MD,
            expand=True,
        )

    def _build_ollama_status_indicator(self):
        """Build Ollama status indicator."""
        # Store references for dynamic updates
        self.ollama_status_icon = ft.Icon(ft.Icons.CIRCLE, color=Theme.TEXT_MUTED, size=12)
        self.ollama_status_text = ft.Text(
            "Status: Not checked - click 'Check Status'",
            size=12,
            color=Theme.TEXT_SECONDARY,
        )
        return ft.Container(
            content=ft.Row(
                controls=[self.ollama_status_icon, self.ollama_status_text],
                spacing=8,
            ),
            key="ollama_status",
        )

    def _build_ollama_library_list(self):
        """Build list of Ollama library models."""
        cards = []
        for m in OLLAMA_LIBRARY_MODELS:
            cards.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SMART_TOY, color=Theme.PRIMARY, size=28),
                            ft.Column(
                                controls=[
                                    ft.Text(m["name"], size=14, weight=ft.FontWeight.W_600, color=Theme.TEXT_PRIMARY),
                                    ft.Text(m["desc"], size=12, color=Theme.TEXT_SECONDARY),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Text(m["size"], size=12, color=Theme.TEXT_MUTED),
                            ft.Button(
                                "Pull",
                                icon=ft.Icons.DOWNLOAD,
                                bgcolor=Theme.PRIMARY,
                                on_click=lambda e, name=m["name"]: self._pull_ollama_model(name),
                            ),
                        ],
                        spacing=Theme.SPACING_MD,
                    ),
                    bgcolor=Theme.SURFACE,
                    padding=Theme.SPACING_MD,
                    border_radius=Theme.RADIUS_MD,
                    border=ft.Border.all(1, Theme.BORDER),
                )
            )

        return ft.Column(controls=cards, spacing=Theme.SPACING_SM)

    def _check_ollama_status(self, e):
        """Check if Ollama is running and update UI."""
        async def do_check():
            from src.ai.models.sources.ollama import OllamaSource
            source = OllamaSource()
            is_running = await source.is_running()

            # Update status indicator
            if self.ollama_status_icon and self.ollama_status_text:
                if is_running:
                    self.ollama_status_icon.color = Theme.SUCCESS
                    self.ollama_status_text.value = "Status: Running - Ollama is available"
                    self.ollama_status_text.color = Theme.SUCCESS
                else:
                    self.ollama_status_icon.color = Theme.ERROR
                    self.ollama_status_text.value = "Status: Not running - Start Ollama to use local models"
                    self.ollama_status_text.color = Theme.ERROR

                if self._page:
                    self._page.update()

        if self._page:
            asyncio.create_task(do_check())

    def _pull_ollama_model(self, model_name):
        """Pull a model from Ollama library with progress tracking."""
        async def do_pull():
            from src.ai.models.hub import ModelInfo
            from src.ai.models.sources.ollama import OllamaSource

            source = OllamaSource()

            # Show progress dialog
            progress_bar = ft.ProgressBar(width=300, value=0)
            status_text = ft.Text("Starting download...", size=12, color=Theme.TEXT_SECONDARY)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Pulling {model_name}"),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            status_text,
                            ft.Container(height=8),
                            progress_bar,
                        ],
                        tight=True,
                    ),
                    width=320,
                ),
            )

            if self._page:
                self._page.open(dialog)

            try:
                def on_progress(progress):
                    if progress.status == "downloading":
                        if progress.total_bytes > 0:
                            pct = progress.downloaded_bytes / progress.total_bytes
                            progress_bar.value = pct
                            status_text.value = f"Downloading: {pct*100:.1f}%"
                        else:
                            progress_bar.value = None  # Indeterminate
                            status_text.value = "Downloading..."
                    elif progress.status == "verifying":
                        status_text.value = "Verifying..."
                        progress_bar.value = None  # Indeterminate
                    elif progress.status == "complete":
                        status_text.value = "Complete!"
                        progress_bar.value = 1.0
                    if self._page:
                        self._page.update()

                # Create a minimal ModelInfo for the download
                model_info = ModelInfo(
                    id=f"ollama-{model_name}",
                    name=model_name,
                    description="",
                    size_bytes=0,
                    quantization="",
                    source="ollama",
                    source_url=model_name,
                )

                await source.download(model_info, self.hub.models_dir, on_progress)

                # Success
                status_text.value = "Download complete!"
                progress_bar.value = 1.0
                if self._page:
                    self._page.update()
                    await asyncio.sleep(1)
                    self._page.close(dialog)
                    self._page.open(
                        ft.SnackBar(
                            content=ft.Text(f"Model {model_name} pulled successfully"),
                            bgcolor=Theme.SUCCESS,
                        )
                    )

            except Exception as ex:
                if self._page:
                    self._page.close(dialog)
                    self._page.open(
                        ft.SnackBar(
                            content=ft.Text(f"Pull failed: {ex}"),
                            bgcolor=Theme.ERROR,
                        )
                    )

        if self._page:
            asyncio.create_task(do_pull())

    # ==================== Import Tab ====================

    def _build_import_tab(self):
        """Build the local file import tab."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.UPLOAD_FILE, size=48, color=Theme.PRIMARY),
                                ft.Text(
                                    "Import Local GGUF Files",
                                    size=18,
                                    weight=ft.FontWeight.W_600,
                                    color=Theme.TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    "Import GGUF model files from your computer",
                                    size=12,
                                    color=Theme.TEXT_SECONDARY,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Container(height=Theme.SPACING_MD),
                                ft.Button(
                                    "Select GGUF File",
                                    icon=ft.Icons.FOLDER_OPEN,
                                    bgcolor=Theme.PRIMARY,
                                    color=Theme.TEXT_PRIMARY,
                                    on_click=self._select_local_file,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        padding=ft.Padding.all(48),
                        bgcolor=Theme.SURFACE,
                        border_radius=Theme.RADIUS_MD,
                        border=ft.Border.all(2, Theme.BORDER),
                    ),
                    ft.Container(height=Theme.SPACING_LG),
                    ft.Text(
                        "Supported Sources",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "- Models downloaded from LM Studio\n"
                        "- Models from GPT4All\n"
                        "- Any GGUF file from the web\n"
                        "- Air-gapped environments",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Container(height=Theme.SPACING_MD),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.INFO_OUTLINE, color=Theme.WARNING, size=16),
                                ft.Text(
                                    "Files will be copied to the models folder. "
                                    f"Location: {self.hub.models_dir}",
                                    size=11,
                                    color=Theme.TEXT_MUTED,
                                ),
                            ],
                            spacing=8,
                        ),
                        padding=Theme.SPACING_SM,
                        bgcolor=Theme.WARNING + "10",
                        border_radius=Theme.RADIUS_SM,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_MD,
            expand=True,
        )

    def _select_local_file(self, e):
        """Open file picker for local GGUF import."""
        def on_file_picked(e_result: ft.FilePickerResultEvent):
            if e_result.files:
                for file in e_result.files:
                    self._import_local_gguf(file.path)

        if not self.file_picker:
            self.file_picker = ft.FilePicker(on_result=on_file_picked)
            if self._page:
                self._page.overlay.append(self.file_picker)
                self._page.update()

        # Open file picker for GGUF files
        self.file_picker.pick_files(
            dialog_title="Select GGUF Model File",
            allowed_extensions=["gguf"],
            allow_multiple=False,
        )

    def _import_local_gguf(self, file_path: str):
        """Import a local GGUF file."""
        async def do_import():
            from pathlib import Path

            from src.ai.models.sources.local import LocalFileSource

            source = LocalFileSource(self.hub.models_dir)
            source_path = Path(file_path)

            try:
                # Validate the GGUF file
                model_info = await source.validate_file(source_path)
                if not model_info:
                    if self._page:
                        self._page.open(
                            ft.SnackBar(
                                content=ft.Text("Invalid GGUF file"),
                                bgcolor=Theme.ERROR,
                            )
                        )
                    return

                # Copy the file to models directory
                await source.download(model_info, self.hub.models_dir)

                # Show success message
                if self._page:
                    self._page.open(
                        ft.SnackBar(
                            content=ft.Text(f"Model imported: {model_info.name}"),
                            bgcolor=Theme.SUCCESS,
                        )
                    )
                    # Refresh model list
                    self.refresh_models()
                    self._page.update()

            except Exception as ex:
                if self._page:
                    self._page.open(
                        ft.SnackBar(
                            content=ft.Text(f"Import failed: {ex}"),
                            bgcolor=Theme.ERROR,
                        )
                    )

        if self._page:
            asyncio.create_task(do_import())
