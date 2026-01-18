# src/ui/views/ai_hub/__init__.py
"""AI Hub view - Modular model management.

This package provides the refactored AIHubView with:
- Centralized state management (state.py)
- Extracted wizard component (wizard.py)
- Extracted providers tab (providers.py)
- Extracted model library tab (model_library.py)
"""

import flet as ft

from src.ui.theme import Theme

from .model_library import ModelLibraryTab
from .providers import ProvidersTab
from .state import AIHubState

# Import extracted components
from .wizard import SetupWizard


class AIHubView(ft.Column):
    """AI Model Hub - coordinates tabs, delegates to specialized components.

    This is a thin coordinator that:
    1. Owns the shared state container
    2. Instantiates specialized components
    3. Wires up the tab structure
    4. Handles cross-component coordination

    Components:
    - SetupWizard: Initial provider configuration wizard
    - ProvidersTab: Provider management and API key configuration
    - ModelLibraryTab: Model browsing, downloading, and management
    - UsageDashboard: Usage statistics and cost tracking (from usage_dashboard.py)
    - KnowledgeBasesView: RAG knowledge base management (from knowledge_bases.py)
    """

    def __init__(self, page: ft.Page = None):
        super().__init__()
        self._page = page
        self.expand = True
        self.state = AIHubState()

        # Components will be instantiated in build()
        self._wizard = None
        self._providers = None
        self._library = None

    def build(self):
        """Build the AI Hub view with all tabs."""
        # Import views that aren't part of the refactored package
        from src.ui.views.knowledge_bases import KnowledgeBasesView
        from src.ui.views.usage_dashboard import UsageDashboardView

        # Instantiate extracted components with shared state
        self._wizard = SetupWizard(page=self._page, state=self.state)
        self._providers = ProvidersTab(page=self._page, state=self.state)
        self._library = ModelLibraryTab(page=self._page)
        usage_dashboard = UsageDashboardView(page=self._page)
        knowledge_bases_view = KnowledgeBasesView(page=self._page)

        # Create tab headers (Flet 0.80+ API: Tab only has label/icon, no content)
        tab_bar = ft.TabBar(
            tabs=[
                ft.Tab(label="Setup", icon=ft.Icons.ROCKET_LAUNCH),
                ft.Tab(label="My Providers", icon=ft.Icons.CLOUD),
                ft.Tab(label="Model Library", icon=ft.Icons.FOLDER),
                ft.Tab(label="Usage", icon=ft.Icons.ANALYTICS),
                ft.Tab(label="Knowledge Bases", icon=ft.Icons.LIBRARY_BOOKS),
            ],
        )

        # Create tab content view (each control corresponds to a tab)
        tab_view = ft.TabBarView(
            controls=[
                self._wizard.build(),
                self._providers.build(),
                self._library.build(),
                usage_dashboard.build(),
                knowledge_bases_view.build(),
            ],
            expand=True,
        )

        # Wrap in Tabs controller
        tabs_control = ft.Tabs(
            content=ft.Column(
                controls=[tab_bar, tab_view],
                expand=True,
            ),
            length=5,
            expand=True,
        )

        return ft.Column(
            controls=[
                self._build_header(),
                tabs_control,
            ],
            expand=True,
            spacing=Theme.SPACING_MD,
        )

    def _build_header(self):
        """Build the AI Hub header with title and refresh button."""
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

    def _refresh_models(self, e):
        """Refresh the model list."""
        if self._library:
            self._library.refresh_models()
        if self._page:
            self._page.update()


# Re-export for backwards compatibility
__all__ = ["AIHubView", "AIHubState"]
