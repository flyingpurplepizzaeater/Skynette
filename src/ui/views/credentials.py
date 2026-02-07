"""Credentials view - Manage API keys and OAuth connections."""

import flet as ft
from datetime import datetime
from typing import Optional, Callable
from src.ui.theme import Theme


class CredentialsView(ft.Column):
    """Manage API keys, OAuth tokens, and other credentials."""

    def __init__(self, on_credential_selected: Optional[Callable] = None):
        super().__init__()
        self.expand = True
        self.on_credential_selected = on_credential_selected
        self._credentials_list = ft.Column(spacing=Theme.SPACING_SM)
        self._vault = None
        self._oauth_manager = None

    def did_mount(self):
        """Called when view is mounted - load credentials."""
        self._init_vault()
        self._refresh_credentials()

    def _init_vault(self):
        """Initialize the credential vault."""
        try:
            from src.data.credentials import CredentialVault, OAuth2Manager
            self._vault = CredentialVault()
            self._oauth_manager = OAuth2Manager(vault=self._vault)
        except Exception as e:
            print(f"Failed to initialize vault: {e}")

    def _refresh_credentials(self):
        """Refresh the credentials list."""
        if not self._vault:
            return

        self._credentials_list.controls.clear()

        try:
            credentials = self._vault.list_credentials()

            if not credentials:
                self._credentials_list.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.KEY_OFF,
                                    size=48,
                                    color=Theme.TEXT_MUTED,
                                ),
                                ft.Text(
                                    "No credentials saved",
                                    size=16,
                                    color=Theme.TEXT_SECONDARY,
                                ),
                                ft.Text(
                                    "Add API keys or connect OAuth services to get started",
                                    size=12,
                                    color=Theme.TEXT_MUTED,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=Theme.SPACING_SM,
                        ),
                        padding=Theme.SPACING_XL,
                        alignment=ft.Alignment.CENTER,
                    )
                )
            else:
                for cred in credentials:
                    self._credentials_list.controls.append(
                        self._build_credential_card(cred)
                    )

            if self.page:
                self._credentials_list.update()
        except Exception as e:
            print(f"Failed to load credentials: {e}")

    def build(self):
        return ft.Column(
            controls=[
                self._build_header(),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self._build_add_section(),
                            ft.Divider(height=1, color=Theme.BORDER),
                            self._build_oauth_section(),
                            ft.Divider(height=1, color=Theme.BORDER),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            "Saved Credentials",
                                            size=16,
                                            weight=ft.FontWeight.W_600,
                                            color=Theme.TEXT_PRIMARY,
                                        ),
                                        self._credentials_list,
                                    ],
                                    spacing=Theme.SPACING_MD,
                                ),
                            ),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        spacing=Theme.SPACING_LG,
                    ),
                    expand=True,
                    padding=ft.padding.only(right=Theme.SPACING_SM),
                ),
            ],
            expand=True,
            spacing=Theme.SPACING_MD,
        )

    def _build_header(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(
                                "Credentials",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=Theme.TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Manage API keys and service connections",
                                size=14,
                                color=Theme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=4,
                    ),
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                icon_color=Theme.TEXT_SECONDARY,
                                tooltip="Refresh",
                                on_click=lambda _: self._refresh_credentials(),
                            ),
                        ],
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )

    def _build_add_section(self):
        """Build section for adding new API key credentials."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Add API Key",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.TextField(
                                            ref=ft.Ref[ft.TextField](),
                                            label="Name",
                                            hint_text="e.g., OpenAI Production",
                                            expand=True,
                                            border_color=Theme.BORDER,
                                            data="name_field",
                                        ),
                                        ft.Dropdown(
                                            label="Service",
                                            width=180,
                                            options=[
                                                ft.dropdown.Option("openai", "OpenAI"),
                                                ft.dropdown.Option("anthropic", "Anthropic"),
                                                ft.dropdown.Option("cohere", "Cohere"),
                                                ft.dropdown.Option("huggingface", "Hugging Face"),
                                                ft.dropdown.Option("slack", "Slack"),
                                                ft.dropdown.Option("discord", "Discord"),
                                                ft.dropdown.Option("telegram", "Telegram"),
                                                ft.dropdown.Option("github", "GitHub"),
                                                ft.dropdown.Option("aws", "AWS"),
                                                ft.dropdown.Option("custom", "Custom"),
                                            ],
                                            border_color=Theme.BORDER,
                                            data="service_field",
                                        ),
                                    ],
                                    spacing=Theme.SPACING_MD,
                                ),
                                ft.TextField(
                                    label="API Key",
                                    hint_text="Enter your API key",
                                    password=True,
                                    can_reveal_password=True,
                                    border_color=Theme.BORDER,
                                    data="api_key_field",
                                ),
                                ft.Row(
                                    controls=[
                                        ft.ElevatedButton(
                                            "Save Credential",
                                            icon=ft.Icons.SAVE,
                                            bgcolor=Theme.PRIMARY,
                                            color=Theme.TEXT_PRIMARY,
                                            on_click=self._on_save_api_key,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.END,
                                ),
                            ],
                            spacing=Theme.SPACING_MD,
                        ),
                        bgcolor=Theme.SURFACE,
                        padding=Theme.SPACING_MD,
                        border_radius=Theme.RADIUS_MD,
                        border=ft.Border.all(1, Theme.BORDER),
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
        )

    def _build_oauth_section(self):
        """Build section for OAuth connections."""
        oauth_providers = [
            {
                "id": "google",
                "name": "Google",
                "icon": ft.Icons.CLOUD,
                "color": "#4285F4",
                "description": "Drive, Sheets, Gmail",
            },
            {
                "id": "microsoft",
                "name": "Microsoft",
                "icon": ft.Icons.WINDOW,
                "color": "#00A4EF",
                "description": "Teams, OneDrive, Outlook",
            },
            {
                "id": "github",
                "name": "GitHub",
                "icon": ft.Icons.CODE,
                "color": "#333333",
                "description": "Repos, Issues, PRs",
            },
            {
                "id": "slack",
                "name": "Slack",
                "icon": ft.Icons.CHAT,
                "color": "#4A154B",
                "description": "Messages, Channels",
            },
            {
                "id": "notion",
                "name": "Notion",
                "icon": ft.Icons.ARTICLE,
                "color": "#000000",
                "description": "Databases, Pages",
            },
        ]

        provider_cards = []
        for provider in oauth_providers:
            is_connected = self._is_oauth_connected(provider["id"])
            provider_cards.append(
                self._build_oauth_provider_card(provider, is_connected)
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "OAuth Connections",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Connect services using OAuth for secure access",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Row(
                        controls=provider_cards,
                        wrap=True,
                        spacing=Theme.SPACING_MD,
                        run_spacing=Theme.SPACING_MD,
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
        )

    def _build_oauth_provider_card(self, provider: dict, is_connected: bool):
        """Build a card for an OAuth provider."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(
                                    provider["icon"],
                                    size=24,
                                    color=Theme.TEXT_PRIMARY,
                                ),
                                width=40,
                                height=40,
                                bgcolor=provider["color"],
                                border_radius=Theme.RADIUS_SM,
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        provider["name"],
                                        size=14,
                                        weight=ft.FontWeight.W_600,
                                        color=Theme.TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        provider["description"],
                                        size=11,
                                        color=Theme.TEXT_SECONDARY,
                                    ),
                                ],
                                spacing=2,
                            ),
                        ],
                        spacing=Theme.SPACING_SM,
                    ),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.CHECK_CIRCLE if is_connected else ft.Icons.RADIO_BUTTON_UNCHECKED,
                                            size=14,
                                            color=Theme.SUCCESS if is_connected else Theme.TEXT_MUTED,
                                        ),
                                        ft.Text(
                                            "Connected" if is_connected else "Not connected",
                                            size=11,
                                            color=Theme.SUCCESS if is_connected else Theme.TEXT_MUTED,
                                        ),
                                    ],
                                    spacing=4,
                                ),
                            ),
                            ft.TextButton(
                                "Disconnect" if is_connected else "Connect",
                                style=ft.ButtonStyle(
                                    color=Theme.ERROR if is_connected else Theme.PRIMARY,
                                ),
                                on_click=lambda e, p=provider["id"]: self._on_oauth_action(p, is_connected),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=Theme.SPACING_SM,
            ),
            width=220,
            padding=Theme.SPACING_MD,
            bgcolor=Theme.SURFACE,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(1, Theme.BORDER),
        )

    def _build_credential_card(self, cred: dict):
        """Build a card for a saved credential."""
        # Determine credential type icon
        service = cred.get("service", "custom")
        is_oauth = service.endswith("_oauth")

        service_icons = {
            "openai": ft.Icons.AUTO_AWESOME,
            "anthropic": ft.Icons.PSYCHOLOGY,
            "slack": ft.Icons.CHAT,
            "discord": ft.Icons.GAMEPAD,
            "github": ft.Icons.CODE,
            "telegram": ft.Icons.SEND,
            "google_oauth": ft.Icons.CLOUD,
            "microsoft_oauth": ft.Icons.WINDOW,
            "aws": ft.Icons.CLOUD_QUEUE,
        }
        icon = service_icons.get(service, ft.Icons.KEY)

        # Format dates
        created = cred.get("created_at", "")
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                created = dt.strftime("%b %d, %Y")
            except:
                pass

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon, size=20, color=Theme.TEXT_PRIMARY),
                        width=36,
                        height=36,
                        bgcolor=Theme.PRIMARY if is_oauth else Theme.SECONDARY,
                        border_radius=Theme.RADIUS_SM,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                cred.get("name", "Unnamed"),
                                size=14,
                                weight=ft.FontWeight.W_500,
                                color=Theme.TEXT_PRIMARY,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        service.replace("_oauth", " (OAuth)").replace("_", " ").title(),
                                        size=12,
                                        color=Theme.TEXT_SECONDARY,
                                    ),
                                    ft.Text(
                                        f"Added {created}",
                                        size=11,
                                        color=Theme.TEXT_MUTED,
                                    ),
                                ],
                                spacing=Theme.SPACING_MD,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.BOLT,
                                icon_size=18,
                                icon_color=Theme.WARNING,
                                tooltip="Test connection",
                                on_click=lambda e, c=cred: self._on_test_credential(c),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_size=18,
                                icon_color=Theme.ERROR,
                                tooltip="Delete",
                                on_click=lambda e, c=cred: self._on_delete_credential(c),
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=Theme.SPACING_MD,
            ),
            padding=Theme.SPACING_MD,
            bgcolor=Theme.SURFACE,
            border_radius=Theme.RADIUS_MD,
            border=ft.Border.all(1, Theme.BORDER),
        )

    def _is_oauth_connected(self, provider: str) -> bool:
        """Check if an OAuth provider is connected."""
        if not self._oauth_manager:
            return False
        try:
            tokens = self._oauth_manager.get_oauth_tokens(provider)
            return tokens is not None
        except:
            return False

    def _on_save_api_key(self, e):
        """Handle saving a new API key credential."""
        if not self._vault:
            self._show_snackbar("Vault not initialized", is_error=True)
            return

        # Find the form fields
        parent = e.control.parent.parent
        name_field = None
        service_field = None
        api_key_field = None

        for control in parent.controls:
            if isinstance(control, ft.Row):
                for child in control.controls:
                    if isinstance(child, ft.TextField) and child.data == "name_field":
                        name_field = child
                    elif isinstance(child, ft.Dropdown) and child.data == "service_field":
                        service_field = child
            elif isinstance(control, ft.TextField) and control.data == "api_key_field":
                api_key_field = control

        if not all([name_field, service_field, api_key_field]):
            # Fallback: search more broadly
            self._show_snackbar("Form fields not found", is_error=True)
            return

        name = name_field.value
        service = service_field.value
        api_key = api_key_field.value

        if not name or not service or not api_key:
            self._show_snackbar("Please fill in all fields", is_error=True)
            return

        try:
            from src.data.credentials import CredentialType
            self._vault.save_credential(
                name=name,
                service=service,
                data={
                    "type": CredentialType.API_KEY.value,
                    "api_key": api_key,
                }
            )

            # Clear form
            name_field.value = ""
            service_field.value = None
            api_key_field.value = ""
            name_field.update()
            service_field.update()
            api_key_field.update()

            self._show_snackbar(f"Saved credential: {name}")
            self._refresh_credentials()
        except Exception as ex:
            self._show_snackbar(f"Failed to save: {ex}", is_error=True)

    def _on_oauth_action(self, provider: str, is_connected: bool):
        """Handle OAuth connect/disconnect action."""
        if is_connected:
            # Disconnect
            if self._oauth_manager:
                try:
                    self._oauth_manager.delete_oauth(provider)
                    self._show_snackbar(f"Disconnected from {provider.title()}")
                    self._refresh_credentials()
                    # Rebuild the view to update OAuth section
                    if self.page:
                        self.page.update()
                except Exception as ex:
                    self._show_snackbar(f"Failed to disconnect: {ex}", is_error=True)
        else:
            # Show OAuth setup dialog
            self._show_oauth_dialog(provider)

    def _show_oauth_dialog(self, provider: str):
        """Show dialog for OAuth setup."""
        if not self.page:
            return

        from src.data.credentials import OAuth2Manager
        config = OAuth2Manager.get_provider_config(provider)

        if not config:
            self._show_snackbar(f"Provider {provider} not configured", is_error=True)
            return

        client_id_field = ft.TextField(
            label="Client ID",
            hint_text="Your OAuth client ID",
            border_color=Theme.BORDER,
        )
        client_secret_field = ft.TextField(
            label="Client Secret",
            hint_text="Your OAuth client secret",
            password=True,
            can_reveal_password=True,
            border_color=Theme.BORDER,
        )

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def start_oauth(e):
            client_id = client_id_field.value
            client_secret = client_secret_field.value

            if not client_id:
                self._show_snackbar("Client ID is required", is_error=True)
                return

            # Generate auth URL
            auth_url = OAuth2Manager.get_auth_url(
                provider=provider,
                client_id=client_id,
                redirect_uri="http://localhost:8765/callback",
                scope_set="default",
            )

            if auth_url:
                # Store client credentials temporarily for callback
                if self._vault:
                    self._vault.save_credential(
                        name=f"{provider}_oauth_pending",
                        service=f"{provider}_oauth_pending",
                        data={
                            "client_id": client_id,
                            "client_secret": client_secret,
                        }
                    )

                # Show instructions
                dialog.open = False
                self.page.update()

                self._show_snackbar(
                    f"Opening browser for {provider.title()} authorization...",
                )

                # Open browser (in real implementation)
                try:
                    import webbrowser
                    webbrowser.open(auth_url)
                except:
                    self._show_snackbar(f"Please visit: {auth_url}", is_error=False)
            else:
                self._show_snackbar("Failed to generate auth URL", is_error=True)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Connect to {provider.title()}"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"Enter your OAuth credentials for {provider.title()}.",
                            size=14,
                            color=Theme.TEXT_SECONDARY,
                        ),
                        ft.Text(
                            "You can get these from the developer console.",
                            size=12,
                            color=Theme.TEXT_MUTED,
                        ),
                        ft.Container(height=Theme.SPACING_SM),
                        client_id_field,
                        client_secret_field,
                    ],
                    spacing=Theme.SPACING_SM,
                    tight=True,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton(
                    "Authorize",
                    bgcolor=Theme.PRIMARY,
                    color=Theme.TEXT_PRIMARY,
                    on_click=start_oauth,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _on_test_credential(self, cred: dict):
        """Test a credential connection."""
        service = cred.get("service", "")
        self._show_snackbar(f"Testing {service} connection...")

        # In a real implementation, this would test the actual API
        # For now, just show success
        self._show_snackbar(f"{cred.get('name', 'Credential')} is valid")

    def _on_delete_credential(self, cred: dict):
        """Delete a credential with confirmation."""
        if not self.page:
            return

        def confirm_delete(e):
            if self._vault:
                try:
                    self._vault.delete_credential(cred["id"])
                    self._show_snackbar(f"Deleted: {cred.get('name', 'credential')}")
                    self._refresh_credentials()
                except Exception as ex:
                    self._show_snackbar(f"Failed to delete: {ex}", is_error=True)
            dialog.open = False
            self.page.update()

        def cancel(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Credential?"),
            content=ft.Text(
                f"Are you sure you want to delete '{cred.get('name', 'this credential')}'? "
                "This action cannot be undone.",
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.ElevatedButton(
                    "Delete",
                    bgcolor=Theme.ERROR,
                    color=Theme.TEXT_PRIMARY,
                    on_click=confirm_delete,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _show_snackbar(self, message: str, is_error: bool = False):
        """Show a snackbar notification."""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=Theme.ERROR if is_error else Theme.SURFACE,
            )
            self.page.snack_bar.open = True
            self.page.update()
