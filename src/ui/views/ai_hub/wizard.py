# src/ui/views/ai_hub/wizard.py
"""AI Provider setup wizard component.

Extracted from AIHubView to improve modularity and testability.
Uses AIHubState for centralized state management.
"""

import flet as ft

from src.ui.theme import Theme

from .state import AIHubState

# Provider definitions
AVAILABLE_PROVIDERS = [
    {
        "id": "openai",
        "name": "OpenAI",
        "description": "GPT-4, GPT-3.5 Turbo",
        "cost": "$$$",
        "type": "Cloud - Requires API key",
    },
    {
        "id": "anthropic",
        "name": "Anthropic",
        "description": "Claude 3 Opus, Sonnet, Haiku",
        "cost": "$$",
        "type": "Cloud - Requires API key",
    },
    {
        "id": "local",
        "name": "Local Models",
        "description": "llama.cpp - Run models on your computer",
        "cost": "Free",
        "type": "Private - No API key needed",
    },
]

PROVIDER_NAMES = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "local": "Local Models",
}


class SetupWizard(ft.Column):
    """AI Provider setup wizard.

    A multi-step wizard for configuring AI providers:
    - Step 0: Select providers to configure
    - Step 1: Configure each selected provider (API keys)
    - Step 2: Completion summary

    Uses AIHubState for state management, enabling state preservation
    when navigating back and forth between steps.
    """

    def __init__(self, page: ft.Page, state: AIHubState, on_complete=None):
        super().__init__()
        self._page = page
        self.state = state
        self.on_complete = on_complete
        self.expand = True

        # Listen for state changes
        self.state.add_listener(self._on_state_change)

    def _on_state_change(self):
        """Rebuild when state changes."""
        if self._page:
            self._page.update()

    def build(self):
        """Build the wizard UI based on current step."""
        if self.state.wizard_step == 0:
            return self._build_step1_provider_selection()
        elif self.state.wizard_step == 1:
            return self._build_step2_configure_providers()
        elif self.state.wizard_step == 2:
            return self._build_step3_completion()
        else:
            return ft.Container(content=ft.Text("Setup complete!"))

    def _on_provider_checked(self, e, provider_id: str):
        """Handle provider checkbox changes."""
        self.state.toggle_provider(provider_id)

    def _build_step1_provider_selection(self):
        """Step 1: Select AI providers to configure."""
        provider_cards = []
        for p in AVAILABLE_PROVIDERS:
            provider_cards.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Checkbox(
                                label=p["name"],
                                value=p["id"] in self.state.selected_providers,
                                on_change=lambda e, pid=p["id"]: self._on_provider_checked(e, pid),
                            ),
                            ft.Container(expand=True),
                            ft.Column(
                                controls=[
                                    ft.Text(p["description"], size=12, color=Theme.TEXT_SECONDARY),
                                    ft.Text(
                                        f"{p['type']} - {p['cost']}",
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
            )

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
                    *provider_cards,
                    ft.Container(expand=True),
                    ft.Row(
                        controls=[
                            ft.TextButton("Skip Setup", on_click=lambda e: self._skip_wizard()),
                            ft.Container(expand=True),
                            ft.Button(
                                "Next: Configure ->",
                                bgcolor=Theme.PRIMARY,
                                on_click=lambda e: self._wizard_next_step(),
                                disabled=len(self.state.selected_providers) == 0,
                            ),
                        ],
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
            padding=Theme.SPACING_LG,
            expand=True,
        )

    def _build_step2_configure_providers(self):
        """Step 2: Configure selected providers."""
        if not self.state.selected_providers:
            # No providers selected, skip to step 3
            self.state.set_wizard_step(2)
            return self.build()

        # Configure first provider in list
        provider_id = self.state.selected_providers[0]
        provider_name = PROVIDER_NAMES.get(provider_id, provider_id)

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
                                ft.TextButton("<- Back", on_click=lambda e: self._wizard_prev_step()),
                                ft.Container(expand=True),
                                ft.Button(
                                    "Next ->",
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
                            ft.TextButton("<- Back", on_click=lambda e: self._wizard_prev_step()),
                            ft.Container(expand=True),
                            ft.Button(
                                "Next ->",
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

    def _build_step3_completion(self):
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
                        f"Configured {len(self.state.selected_providers)} AI provider(s)",
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
                                ft.Text("- Download local models in Model Library tab"),
                                ft.Text("- Add AI nodes to your workflows"),
                                ft.Text("- Monitor usage and costs in Dashboard"),
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
                            ft.TextButton("<- Back", on_click=lambda e: self._wizard_prev_step()),
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
        self.state.set_wizard_step(self.state.wizard_step + 1)

    def _wizard_prev_step(self):
        """Go back to previous wizard step."""
        if self.state.wizard_step > 0:
            self.state.set_wizard_step(self.state.wizard_step - 1)

    def _update_provider_config(self, provider_id: str, key: str, value: str):
        """Update provider configuration in state."""
        self.state.update_provider_config(provider_id, key, value)

    def _test_provider_connection(self, provider_id: str):
        """Test provider connection (mock for now)."""
        # TODO: Implement actual API test
        print(f"Testing {provider_id} connection...")

    def _skip_wizard(self):
        """Skip wizard and go to providers tab."""
        # Reset wizard state and notify parent
        self.state.reset_wizard()
        if self.on_complete:
            self.on_complete(skipped=True)

    def _complete_wizard(self):
        """Complete wizard and save configurations."""
        import json

        from src.ai.security import store_api_key
        from src.data.storage import get_storage

        storage = get_storage()

        # Save API keys to system keyring
        for provider_id, config in self.state.provider_configs.items():
            if "api_key" in config:
                try:
                    store_api_key(provider_id, config["api_key"])
                except Exception as e:
                    print(f"Failed to store API key for {provider_id}: {e}")

        # Save selected providers list to settings
        storage.set_setting("configured_providers", json.dumps(self.state.selected_providers))

        # Save individual provider configs (without API keys, those are in keyring)
        for provider_id in self.state.selected_providers:
            config_data = {
                k: v
                for k, v in self.state.provider_configs.get(provider_id, {}).items()
                if k != "api_key"
            }
            storage.set_setting(f"provider_config_{provider_id}", json.dumps(config_data))

        # Mark wizard as completed
        storage.set_setting("ai_wizard_completed", "true")

        # Reset wizard state
        self.state.reset_wizard()

        # Notify parent
        if self.on_complete:
            self.on_complete(skipped=False)
