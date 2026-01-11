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

        # Wizard state
        self.wizard_step = 0
        self.selected_providers = []
        self.provider_configs = {}

    def build(self):
        # Import usage dashboard
        from src.ui.views.usage_dashboard import UsageDashboardView

        # Create tabs
        setup_tab = ft.Tab(label="Setup", icon=ft.Icons.ROCKET_LAUNCH)
        setup_tab.content = self._build_wizard_tab()

        providers_tab = ft.Tab(label="My Providers", icon=ft.Icons.CLOUD)
        providers_tab.content = self._build_providers_tab()

        library_tab = ft.Tab(label="Model Library", icon=ft.Icons.FOLDER)
        library_tab.content = self._build_model_library_tab()

        usage_tab = ft.Tab(label="Usage", icon=ft.Icons.ANALYTICS)
        usage_dashboard = UsageDashboardView(page=self._page)
        usage_tab.content = usage_dashboard.build()

        return ft.Column(
            controls=[
                self._build_header(),
                ft.Tabs(
                    length=4,
                    content=[setup_tab, providers_tab, library_tab, usage_tab],
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
                    ft.Button(
                        "Refresh",
                        icon=ft.Icons.REFRESH,
                        bgcolor=Theme.SURFACE,
                        color=Theme.TEXT_PRIMARY,
                        on_click=self._refresh_models,
                    ),
                ],
            ),
        )

    def _build_wizard_tab(self):
        """Build setup wizard tab."""
        if self.wizard_step == 0:
            return self._build_wizard_step1_provider_selection()
        elif self.wizard_step == 1:
            return self._build_wizard_step2_configure_providers()
        elif self.wizard_step == 2:
            return self._build_wizard_step3_completion()
        else:
            return ft.Container(content=ft.Text("Setup complete!"))

    def _on_provider_checked(self, e, provider_id):
        """Handle provider checkbox changes."""
        if e.control.value:
            if provider_id not in self.selected_providers:
                self.selected_providers.append(provider_id)
        else:
            if provider_id in self.selected_providers:
                self.selected_providers.remove(provider_id)

        # Trigger UI update to enable/disable Next button
        if self._page:
            self._page.update()

    def _build_wizard_step1_provider_selection(self):
        """Step 1: Select AI providers to configure."""
        providers = [
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "GPT-4, GPT-3.5 Turbo",
                "cost": "$$$",
                "type": "Cloud • Requires API key",
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "description": "Claude 3 Opus, Sonnet, Haiku",
                "cost": "$$",
                "type": "Cloud • Requires API key",
            },
            {
                "id": "local",
                "name": "Local Models",
                "description": "llama.cpp - Run models on your computer",
                "cost": "Free",
                "type": "Private • No API key needed",
            },
        ]

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Welcome to Skynette AI Setup",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Select which AI providers you want to use:",
                        size=14,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Container(height=Theme.SPACING_LG),
                    *[
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Checkbox(
                                        label=p["name"],
                                        value=p["id"] in self.selected_providers,
                                        on_change=lambda e, pid=p["id"]: self._on_provider_checked(e, pid),
                                    ),
                                    ft.Container(expand=True),
                                    ft.Column(
                                        controls=[
                                            ft.Text(p["description"], size=12, color=Theme.TEXT_SECONDARY),
                                            ft.Text(
                                                f"{p['type']} • {p['cost']}",
                                                size=11,
                                                color=Theme.TEXT_MUTED,
                                            ),
                                        ],
                                        spacing=2,
                                    ),
                                ],
                            ),
                            bgcolor=Theme.SURFACE,
                            padding=Theme.SPACING_MD,
                            border_radius=Theme.RADIUS_MD,
                            border=ft.Border.all(1, Theme.BORDER),
                        )
                        for p in providers
                    ],
                    ft.Container(expand=True),
                    ft.Row(
                        controls=[
                            ft.TextButton("Skip Setup", on_click=lambda e: self._skip_wizard()),
                            ft.Container(expand=True),
                            ft.Button(
                                "Next: Configure →",
                                bgcolor=Theme.PRIMARY,
                                on_click=lambda e: self._wizard_next_step(),
                                disabled=len(self.selected_providers) == 0,
                            ),
                        ],
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_LG,
            expand=True,
        )

    def _build_wizard_step2_configure_providers(self):
        """Step 2: Configure selected providers."""
        if not self.selected_providers:
            # No providers selected, skip to step 3
            self.wizard_step = 2
            return self._build_wizard_tab()

        # Configure first provider in list
        provider_id = self.selected_providers[0]
        provider_names = {
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "local": "Local Models",
        }

        provider_name = provider_names.get(provider_id, provider_id)

        # For local provider, no API key needed
        if provider_id == "local":
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"Configure {provider_name}",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "Local models run on your computer. No API key required!",
                            size=14,
                            color=Theme.SUCCESS,
                        ),
                        ft.Container(height=Theme.SPACING_LG),
                        ft.Text("Local models will be available after downloading them in the Model Library."),
                        ft.Container(expand=True),
                        ft.Row(
                            controls=[
                                ft.TextButton("← Back", on_click=lambda e: self._wizard_prev_step()),
                                ft.Container(expand=True),
                                ft.Button(
                                    "Next →",
                                    bgcolor=Theme.PRIMARY,
                                    on_click=lambda e: self._wizard_next_step(),
                                ),
                            ],
                        ),
                    ],
                ),
                padding=Theme.SPACING_LG,
                expand=True,
            )

        # Cloud providers need API key
        api_key_field = ft.TextField(
            label="API Key",
            password=True,
            can_reveal_password=True,
            hint_text=f"Enter your {provider_name} API key",
            on_change=lambda e, pid=provider_id: self._update_provider_config(pid, "api_key", e.control.value),
        )

        test_button = ft.Button(
            "Test Connection",
            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
            on_click=lambda e, pid=provider_id: self._test_provider_connection(pid),
        )

        status_text = ft.Text("", size=12)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"Configure {provider_name}",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Container(height=Theme.SPACING_MD),
                    api_key_field,
                    ft.Container(height=Theme.SPACING_SM),
                    test_button,
                    status_text,
                    ft.Container(expand=True),
                    ft.Row(
                        controls=[
                            ft.TextButton("← Back", on_click=lambda e: self._wizard_prev_step()),
                            ft.Container(expand=True),
                            ft.Button(
                                "Next →",
                                bgcolor=Theme.PRIMARY,
                                on_click=lambda e: self._wizard_next_step(),
                            ),
                        ],
                    ),
                ],
            ),
            padding=Theme.SPACING_LG,
            expand=True,
        )

    def _build_wizard_step3_completion(self):
        """Step 3: Setup completion and summary."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE,
                        size=64,
                        color=Theme.SUCCESS,
                    ),
                    ft.Text(
                        "Setup Complete!",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        f"Configured {len(self.selected_providers)} AI provider(s)",
                        size=14,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Container(height=Theme.SPACING_LG),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "What's Next:",
                                    size=16,
                                    weight=ft.FontWeight.W_600,
                                ),
                                ft.Text("• Download local models in Model Library tab"),
                                ft.Text("• Add AI nodes to your workflows"),
                                ft.Text("• Monitor usage and costs in Dashboard"),
                            ],
                            spacing=8,
                        ),
                        bgcolor=Theme.SURFACE,
                        padding=Theme.SPACING_MD,
                        border_radius=Theme.RADIUS_MD,
                    ),
                    ft.Container(expand=True),
                    ft.Row(
                        controls=[
                            ft.TextButton("← Back", on_click=lambda e: self._wizard_prev_step()),
                            ft.Container(expand=True),
                            ft.Button(
                                "Get Started",
                                bgcolor=Theme.SUCCESS,
                                on_click=lambda e: self._complete_wizard(),
                            ),
                        ],
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_LG,
            expand=True,
        )

    def _wizard_next_step(self):
        """Advance wizard to next step."""
        self.wizard_step += 1
        if self._page:
            self._page.update()

    def _wizard_prev_step(self):
        """Go back to previous wizard step."""
        if self.wizard_step > 0:
            self.wizard_step -= 1
        if self._page:
            self._page.update()

    def _update_provider_config(self, provider_id: str, key: str, value: str):
        """Update provider configuration.

        TODO: Use secure keyring storage instead of plain memory (see src/ai/security.py)
        """
        if provider_id not in self.provider_configs:
            self.provider_configs[provider_id] = {}
        self.provider_configs[provider_id][key] = value

    def _test_provider_connection(self, provider_id: str):
        """Test provider connection (mock for now)."""
        # TODO: Implement actual API test
        print(f"Testing {provider_id} connection...")

    def _skip_wizard(self):
        """Skip wizard and go to providers tab."""
        # Switch to My Providers tab (index 1)
        if self._page:
            # TODO: Implement tab switching
            pass

    def _complete_wizard(self):
        """Complete wizard and save configurations."""
        from src.ai.security import store_api_key
        from src.data.storage import get_storage
        import json

        storage = get_storage()

        # Save API keys to system keyring
        for provider_id, config in self.provider_configs.items():
            if "api_key" in config:
                try:
                    store_api_key(provider_id, config["api_key"])
                except Exception as e:
                    print(f"Failed to store API key for {provider_id}: {e}")

        # Save selected providers list to settings
        storage.set_setting("configured_providers", json.dumps(self.selected_providers))

        # Save individual provider configs (without API keys, those are in keyring)
        for provider_id in self.selected_providers:
            config_data = {k: v for k, v in self.provider_configs.get(provider_id, {}).items() if k != "api_key"}
            storage.set_setting(f"provider_config_{provider_id}", json.dumps(config_data))

        # Mark wizard as completed
        storage.set_setting("ai_wizard_completed", "true")

        # Reset wizard state
        self.wizard_step = 0
        self.selected_providers = []
        self.provider_configs = {}

        # Navigate to My Providers tab
        if self._page:
            # TODO: Switch to tab 1 (My Providers)
            self._page.update()

    def _build_model_library_tab(self):
        """Model Library tab containing My Models and Download as subtabs."""
        # Create subtabs for My Models and Download
        my_models_tab = ft.Tab(label="My Models", icon=ft.Icons.FOLDER)
        my_models_tab.content = self._build_installed_tab()

        download_tab = ft.Tab(label="Download", icon=ft.Icons.DOWNLOAD)
        download_tab.content = self._build_download_tab()

        return ft.Container(
            content=ft.Tabs(
                length=2,
                content=[my_models_tab, download_tab],
                expand=True,
            ),
            expand=True,
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
                            ft.Button(
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

    def _build_providers_tab(self):
        """My Providers management tab."""
        from src.ai.security import has_api_key

        # Define providers with base info
        provider_defs = [
            {"id": "openai", "name": "OpenAI", "icon": ft.Icons.CLOUD, "color": "#10a37f"},
            {"id": "anthropic", "name": "Anthropic", "icon": ft.Icons.CLOUD, "color": "#d4a574"},
            {"id": "google", "name": "Google AI", "icon": ft.Icons.CLOUD, "color": "#4285f4"},
            {"id": "groq", "name": "Groq", "icon": ft.Icons.BOLT, "color": "#f55036"},
            {"id": "local", "name": "Local (llama.cpp)", "icon": ft.Icons.COMPUTER, "color": Theme.SUCCESS},
        ]

        # Build providers list with dynamic status
        providers = []
        for p_def in provider_defs:
            if p_def["id"] == "local":
                # Local is always available
                providers.append({
                    **p_def,
                    "status": "Ready (Demo mode)",
                    "configured": True,
                })
            elif p_def["id"] == "groq":
                # Groq has free tier
                configured = has_api_key(p_def["id"])
                providers.append({
                    **p_def,
                    "status": "Configured" if configured else "Free tier available",
                    "configured": configured,
                })
            else:
                # Cloud providers need API key
                configured = has_api_key(p_def["id"])
                providers.append({
                    **p_def,
                    "status": "Configured" if configured else "Not configured",
                    "configured": configured,
                })


        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "AI Providers",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Configure API keys to use cloud AI services",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Container(height=Theme.SPACING_MD),
                    *[
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(p["icon"], size=24, color=p["color"]),
                                    ft.Column(
                                        controls=[
                                            ft.Text(p["name"], size=14, weight=ft.FontWeight.W_500),
                                            ft.Text(
                                                p["status"],
                                                size=12,
                                                color=Theme.SUCCESS if p["configured"] else Theme.TEXT_SECONDARY,
                                            ),
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                    ft.Button(
                                        "Configure" if not p["configured"] else "Edit",
                                        bgcolor=Theme.SURFACE if p["configured"] else Theme.PRIMARY,
                                        on_click=lambda e, provider=p: self._configure_provider(provider),
                                    ),
                                ],
                                spacing=Theme.SPACING_MD,
                            ),
                            bgcolor=Theme.SURFACE,
                            padding=Theme.SPACING_MD,
                            border_radius=Theme.RADIUS_MD,
                            border=ft.Border.all(1, Theme.BORDER),
                        )
                        for p in providers
                    ],
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

    def _build_provider_config_dialog(self, provider: dict) -> ft.AlertDialog:
        """Build provider configuration dialog.

        Args:
            provider: Provider dict with 'id', 'name', 'requires_key' fields

        Returns:
            AlertDialog for configuring the provider
        """
        from src.ai.security import store_api_key, has_api_key, get_api_key

        # Get existing API key if any
        existing_key = ""
        provider_id = provider.get("id", provider.get("name", "").lower())
        if has_api_key(provider_id):
            existing_key = get_api_key(provider_id) or ""

        # Create API key text field
        api_key_field = ft.TextField(
            label=f"{provider['name']} API Key",
            hint_text="sk-..." if provider_id == "openai" else "Enter your API key",
            password=True,
            can_reveal_password=True,
            value=existing_key,
            width=400,
        )

        def save_config(e):
            """Save provider configuration."""
            if api_key_field.value and api_key_field.value.strip():
                store_api_key(provider_id, api_key_field.value.strip())
                if self._page:
                    self._page.close(dialog)
                    # Rebuild providers tab to show updated status
                    self._page.update()

        def cancel_config(e):
            """Cancel configuration."""
            if self._page:
                self._page.close(dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Configure {provider['name']}"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"Enter your {provider['name']} API key to enable cloud AI features.",
                            size=12,
                            color=Theme.TEXT_SECONDARY,
                        ),
                        ft.Container(height=Theme.SPACING_SM),
                        api_key_field,
                    ],
                    tight=True,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_config),
                ft.Button(
                    "Save",
                    bgcolor=Theme.PRIMARY,
                    color=Theme.TEXT_PRIMARY,
                    on_click=save_config,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        return dialog

    def _configure_provider(self, provider: dict):
        """Open provider configuration dialog."""
        dialog = self._build_provider_config_dialog(provider)
        if self._page:
            self._page.open(dialog)
