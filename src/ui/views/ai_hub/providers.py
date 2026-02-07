# src/ui/views/ai_hub/providers.py
"""Provider management tab component.

Extracted from AIHubView to improve modularity and testability.
Handles provider configuration including API key management.
"""

import asyncio

import flet as ft

from src.ui.theme import Theme

from .state import AIHubState

# Provider definitions with branding
PROVIDER_DEFINITIONS = [
    {"id": "openai", "name": "OpenAI", "icon": ft.Icons.CLOUD, "color": "#10a37f"},
    {"id": "anthropic", "name": "Anthropic", "icon": ft.Icons.CLOUD, "color": "#d4a574"},
    {"id": "google", "name": "Google AI", "icon": ft.Icons.CLOUD, "color": "#4285f4"},
    {"id": "groq", "name": "Groq", "icon": ft.Icons.BOLT, "color": "#f55036"},
    {"id": "ollama", "name": "Ollama (Local)", "icon": ft.Icons.MEMORY, "color": "#0ea5e9"},
    {"id": "local", "name": "Local (llama.cpp)", "icon": ft.Icons.COMPUTER, "color": Theme.SUCCESS},
]


class ProvidersTab(ft.Column):
    """Provider management tab.

    Displays configured providers with their status and allows
    configuration/editing of API keys through a dialog.
    """

    def __init__(self, page: ft.Page, state: AIHubState):
        super().__init__()
        self._page = page
        self.state = state
        self.expand = True

    def did_mount(self):
        """Called when component is mounted. Trigger Ollama status refresh."""
        # Schedule the async refresh
        asyncio.create_task(self._refresh_ollama_status())

    async def _refresh_ollama_status(self):
        """Refresh Ollama connection status asynchronously."""
        self.state.set_ollama_refreshing(True)
        if self._page:
            self._page.update()

        from src.ai.providers.ollama import OllamaProvider

        provider = OllamaProvider()
        connected, models, error = await provider.check_status()

        self.state.set_ollama_refreshing(False)
        self.state.set_ollama_status(connected, models, error)
        if self._page:
            self._page.update()

    def _on_refresh_ollama(self, e):
        """Handle refresh button click."""
        asyncio.create_task(self._refresh_ollama_status())

    def _build_ollama_status(self) -> ft.Control:
        """Build Ollama status indicator with refresh button."""
        if self.state.ollama_refreshing:
            status_icon = ft.ProgressRing(width=16, height=16, stroke_width=2)
            status_text = "Refreshing..."
            status_color = ft.Colors.BLUE
        elif self.state.ollama_connected:
            status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=16)
            model_count = len(self.state.ollama_models)
            status_text = f"Connected ({model_count} model{'s' if model_count != 1 else ''})"
            status_color = ft.Colors.GREEN
        else:
            status_icon = ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED, size=16)
            status_text = self.state.ollama_error or "Not connected"
            status_color = ft.Colors.RED

        refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Refresh models",
            on_click=self._on_refresh_ollama,
            disabled=self.state.ollama_refreshing,
            icon_size=20,
        )

        return ft.Row(
            controls=[
                status_icon,
                ft.Text(status_text, color=status_color, size=12),
                refresh_btn,
            ],
            spacing=4,
        )

    def build(self):
        """Build the providers tab UI."""
        from src.ai.security import has_api_key

        # Build providers list with dynamic status
        providers = []
        for p_def in PROVIDER_DEFINITIONS:
            if p_def["id"] == "local":
                # Local is always available
                providers.append(
                    {
                        **p_def,
                        "status": "Ready (Demo mode)",
                        "configured": True,
                    }
                )
            elif p_def["id"] == "ollama":
                # Ollama handled specially with status indicator
                providers.append(
                    {
                        **p_def,
                        "status": None,  # Status shown via _build_ollama_status
                        "configured": self.state.ollama_connected,
                        "is_ollama": True,
                    }
                )
            elif p_def["id"] == "groq":
                # Groq has free tier
                configured = has_api_key(p_def["id"])
                providers.append(
                    {
                        **p_def,
                        "status": "Configured" if configured else "Free tier available",
                        "configured": configured,
                    }
                )
            else:
                # Cloud providers need API key
                configured = has_api_key(p_def["id"])
                providers.append(
                    {
                        **p_def,
                        "status": "Configured" if configured else "Not configured",
                        "configured": configured,
                    }
                )

        provider_cards = []
        for p in providers:
            # Build status content - special handling for Ollama
            if p.get("is_ollama"):
                status_content = self._build_ollama_status()
            else:
                status_content = ft.Text(
                    p["status"],
                    size=12,
                    color=Theme.SUCCESS if p["configured"] else Theme.TEXT_SECONDARY,
                )

            # Build card content
            card_content = [
                ft.Icon(p["icon"], size=24, color=p["color"]),
                ft.Column(
                    controls=[
                        ft.Text(p["name"], size=14, weight=ft.FontWeight.W_500),
                        status_content,
                    ],
                    spacing=2,
                    expand=True,
                ),
            ]

            # Add configure button only for non-Ollama providers
            # (Ollama doesn't need API key configuration)
            if not p.get("is_ollama"):
                card_content.append(
                    ft.Button(
                        "Configure" if not p["configured"] else "Edit",
                        bgcolor=Theme.SURFACE if p["configured"] else Theme.PRIMARY,
                        on_click=lambda e, provider=p: self._configure_provider(provider),
                    )
                )

            provider_cards.append(
                ft.Container(
                    content=ft.Row(
                        controls=card_content,
                        spacing=Theme.SPACING_MD,
                    ),
                    bgcolor=Theme.SURFACE,
                    padding=Theme.SPACING_MD,
                    border_radius=Theme.RADIUS_MD,
                    border=ft.Border.all(1, Theme.BORDER),
                )
            )

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
                    *provider_cards,
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_MD,
            expand=True,
        )

    def _build_provider_config_dialog(self, provider: dict) -> ft.AlertDialog:
        """Build provider configuration dialog.

        Args:
            provider: Provider dict with 'id', 'name' fields

        Returns:
            AlertDialog for configuring the provider
        """
        from src.ai.security import get_api_key, has_api_key, store_api_key

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
