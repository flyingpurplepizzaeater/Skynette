# src/ui/views/ai_hub/providers.py
"""Provider management tab component.

Extracted from AIHubView to improve modularity and testability.
Handles provider configuration including API key management.
"""

import flet as ft

from src.ui.theme import Theme

from .state import AIHubState

# Provider definitions with branding
PROVIDER_DEFINITIONS = [
    {"id": "openai", "name": "OpenAI", "icon": ft.Icons.CLOUD, "color": "#10a37f"},
    {"id": "anthropic", "name": "Anthropic", "icon": ft.Icons.CLOUD, "color": "#d4a574"},
    {"id": "google", "name": "Google AI", "icon": ft.Icons.CLOUD, "color": "#4285f4"},
    {"id": "groq", "name": "Groq", "icon": ft.Icons.BOLT, "color": "#f55036"},
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

    def build(self):
        """Build the providers tab UI."""
        from src.ai.security import has_api_key

        # Build providers list with dynamic status
        providers = []
        for p_def in PROVIDER_DEFINITIONS:
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

        provider_cards = []
        for p in providers:
            provider_cards.append(
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
