"""AI Hub view - Model management and downloads."""

import flet as ft
import asyncio
from src.ui.theme import Theme
from src.ai.models.hub import get_hub, ModelInfo, DownloadProgress


class AIHubView(ft.Column):
    """AI Model Hub for managing local and cloud AI models."""

    def __init__(self, page: ft.Page = None):
        super().__init__()
        self._page = page
        self.expand = True
        self.hub = get_hub()
        self.download_cards: dict[str, ft.Container] = {}
        self.installed_list = None
        self.recommended_list = None

    def build(self):
        return ft.Column(
            controls=[
                self._build_header(),
                ft.Tabs(
                    tabs=[
                        ft.Tab(
                            text="My Models",
                            icon=ft.Icons.FOLDER,
                            content=self._build_installed_tab(),
                        ),
                        ft.Tab(
                            text="Download",
                            icon=ft.Icons.DOWNLOAD,
                            content=self._build_download_tab(),
                        ),
                        ft.Tab(
                            text="Providers",
                            icon=ft.Icons.CLOUD,
                            content=self._build_providers_tab(),
                        ),
                    ],
                    expand=True,
                ),
            ],
            expand=True,
            spacing=Theme.SPACING_MD,
        )

    def _build_header(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "AI Model Hub",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Refresh",
                        icon=ft.Icons.REFRESH,
                        bgcolor=Theme.SURFACE,
                        color=Theme.TEXT_PRIMARY,
                        on_click=self._refresh_models,
                    ),
                ],
            ),
        )

    def _build_installed_tab(self):
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
                        padding=ft.padding.all(48),
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
                                f"{model.quantization} • {model.size_display}",
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
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
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
            border=ft.border.all(1, Theme.BORDER),
        )

    def _build_download_tab(self):
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

        return ft.Container(
            content=ft.Column(
                controls=[
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
                    ft.Container(height=Theme.SPACING_LG),
                    ft.Divider(color=Theme.BORDER),
                    ft.Container(height=Theme.SPACING_MD),
                    ft.Text(
                        "Download from URL",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Row(
                        controls=[
                            ft.TextField(
                                hint_text="Paste a GGUF model URL...",
                                expand=True,
                                border_color=Theme.BORDER,
                            ),
                            ft.ElevatedButton(
                                "Download",
                                icon=ft.Icons.DOWNLOAD,
                                bgcolor=Theme.PRIMARY,
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_MD,
            expand=True,
        )

    def _build_recommended_model_card(self, model: ModelInfo):
        is_downloaded = model.is_downloaded
        progress = self.hub.get_download_progress(model.id)
        is_downloading = progress and progress.status == "downloading"

        # Tags based on metadata
        tags = []
        for tag in model.metadata.get("recommended_for", [])[:3]:
            tags.append(
                ft.Container(
                    content=ft.Text(tag, size=10, color=Theme.PRIMARY),
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
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
            action_control = ft.ElevatedButton(
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
            border=ft.border.all(1, Theme.BORDER),
        )

    def _build_providers_tab(self):
        """Build My Providers management tab."""
        from src.ai.security import has_api_key

        # Check which providers are configured
        providers_data = [
            {
                "id": "openai",
                "name": "OpenAI",
                "icon": ft.Icons.CLOUD,
                "color": "#10a37f",
                "requires_key": True,
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "icon": ft.Icons.CLOUD,
                "color": "#d4a574",
                "requires_key": True,
            },
            {
                "id": "local",
                "name": "Local (llama.cpp)",
                "icon": ft.Icons.COMPUTER,
                "color": Theme.SUCCESS,
                "requires_key": False,
            },
        ]

        provider_cards = []
        for p in providers_data:
            # Check if configured
            if p["requires_key"]:
                try:
                    configured = has_api_key(p["id"])
                except Exception as e:
                    # If keyring fails, assume not configured and log error
                    print(f"Warning: Failed to check API key for {p['id']}: {e}")
                    configured = False

                status = "Configured ✓" if configured else "Not configured"
                status_color = Theme.SUCCESS if configured else Theme.TEXT_SECONDARY
                button_text = "Edit" if configured else "Configure"
                button_color = Theme.SURFACE if configured else Theme.PRIMARY
            else:
                configured = True
                status = "Ready (no key required)"
                status_color = Theme.SUCCESS
                button_text = "Settings"
                button_color = Theme.SURFACE

            provider_cards.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(p["icon"], size=24, color=p["color"]),
                            ft.Column(
                                controls=[
                                    ft.Text(p["name"], size=14, weight=ft.FontWeight.W_500),
                                    ft.Text(status, size=12, color=status_color),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.ElevatedButton(
                                button_text,
                                bgcolor=button_color,
                                on_click=lambda e, provider=p: self._open_provider_config_dialog(provider),
                            ),
                        ],
                        spacing=Theme.SPACING_MD,
                    ),
                    bgcolor=Theme.SURFACE,
                    padding=Theme.SPACING_MD,
                    border_radius=Theme.RADIUS_MD,
                    border=ft.border.all(1, Theme.BORDER),
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "My AI Providers",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Manage API keys and provider settings",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Container(height=Theme.SPACING_MD),
                    *provider_cards,
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_MD,
            expand=True,
        )

    def _refresh_models(self, e):
        """Refresh the model list."""
        self.hub.scan_local_models()
        if self._page:
            self._page.update()

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
                self._refresh_models(None)
            except Exception as ex:
                print(f"Download failed: {ex}")

        if self._page:
            asyncio.create_task(do_download())

    def _delete_model(self, model: ModelInfo):
        """Delete a downloaded model."""
        self.hub.delete_model(model.id)
        self._refresh_models(None)

    def _set_default_model(self, model: ModelInfo):
        """Set a model as the default."""
        # TODO: Implement default model setting
        print(f"Setting default: {model.name}")

    def _open_provider_config_dialog(self, provider: dict):
        """Open provider configuration dialog."""
        dialog = self._build_provider_config_dialog(provider)
        if self._page:
            self._page.overlay.append(dialog)
            dialog.open = True
            self._page.update()

    def _build_provider_config_dialog(self, provider: dict):
        """Build provider configuration dialog."""
        from src.ai.security import get_api_key, store_api_key, delete_api_key

        # Get existing API key if configured
        existing_key = get_api_key(provider["id"]) if provider.get("requires_key") else None
        masked_key = f"{existing_key[:8]}...{existing_key[-4:]}" if existing_key else ""

        api_key_field = ft.TextField(
            label="API Key",
            password=True,
            can_reveal_password=True,
            value=existing_key or "",
            hint_text="Enter your API key",
        )

        status_text = ft.Text("", size=12)

        def save_config(e):
            """Save provider configuration."""
            try:
                api_key = api_key_field.value
                if api_key:
                    store_api_key(provider["id"], api_key)
                    status_text.value = "✓ API key saved successfully"
                    status_text.color = Theme.SUCCESS
                else:
                    delete_api_key(provider["id"])
                    status_text.value = "API key removed"
                    status_text.color = Theme.TEXT_SECONDARY

                if self._page:
                    self._page.update()
                    # Refresh providers tab
                    # Close dialog after 1 second
                    import time
                    time.sleep(1)
                    close_dialog(e)
            except Exception as ex:
                status_text.value = f"Error: {ex}"
                status_text.color = Theme.ERROR
                if self._page:
                    self._page.update()

        def close_dialog(e):
            """Close the dialog."""
            if self._page:
                dialog.open = False
                self._page.update()
                # Rebuild providers tab to show updated status
                # (Parent will handle this)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Configure {provider['name']}"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "API Key Configuration",
                            size=14,
                            weight=ft.FontWeight.W_600,
                        ),
                        api_key_field,
                        ft.Container(height=4),
                        ft.Text(
                            "Your API key is stored securely in your system keyring.",
                            size=11,
                            color=Theme.TEXT_MUTED,
                            italic=True,
                        ),
                        ft.Container(height=8),
                        status_text,
                    ],
                    tight=True,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Save", bgcolor=Theme.PRIMARY, on_click=save_config),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        return dialog
