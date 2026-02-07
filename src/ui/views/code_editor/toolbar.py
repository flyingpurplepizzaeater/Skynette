# src/ui/views/code_editor/toolbar.py
"""Toolbar component for the code editor."""

from collections.abc import Callable

import flet as ft

from src.ui.theme import SkynetteTheme


class EditorToolbar(ft.Column):
    """Toolbar for code editor actions.

    Actions: Save, Save All, Toggle Sidebar, Open Folder, Toggle AI Panel

    Example:
        toolbar = EditorToolbar(
            on_save=lambda: print("Save"),
            on_save_all=lambda: print("Save all"),
            on_toggle_sidebar=lambda: print("Toggle sidebar"),
            on_open_folder=lambda: print("Open folder"),
            on_toggle_ai=lambda: print("Toggle AI panel"),
        )
    """

    def __init__(
        self,
        on_save: Callable[[], None],
        on_save_all: Callable[[], None],
        on_toggle_sidebar: Callable[[], None],
        on_open_folder: Callable[[], None],
        on_toggle_ai: Callable[[], None] | None = None,
        on_format_change: Callable[[str], None] | None = None,
        sidebar_visible: bool = True,
        has_unsaved: bool = False,
        ai_panel_visible: bool = False,
        workflow_mode: bool = False,
        current_format: str = "yaml",
    ):
        """Initialize toolbar.

        Args:
            on_save: Callback for save action.
            on_save_all: Callback for save all action.
            on_toggle_sidebar: Callback for toggle sidebar action.
            on_open_folder: Callback for open folder action.
            on_toggle_ai: Callback for toggle AI panel action.
            on_format_change: Callback for workflow format change.
            sidebar_visible: Whether sidebar is currently visible.
            has_unsaved: Whether there are unsaved files (highlights Save All).
            ai_panel_visible: Whether AI panel is currently visible.
            workflow_mode: Whether editing a workflow (shows format dropdown).
            current_format: Current workflow format (yaml/json/python).
        """
        super().__init__()
        self.on_save = on_save
        self.on_save_all = on_save_all
        self.on_toggle_sidebar = on_toggle_sidebar
        self.on_open_folder = on_open_folder
        self.on_toggle_ai = on_toggle_ai
        self.on_format_change = on_format_change
        self.sidebar_visible = sidebar_visible
        self.has_unsaved = has_unsaved
        self.ai_panel_visible = ai_panel_visible
        self.workflow_mode = workflow_mode
        self.current_format = current_format

        # Format dropdown reference
        self._format_dropdown: ft.Dropdown | None = None

        # Column settings
        self.spacing = 0

    def build(self) -> None:
        """Build toolbar row."""
        # Format dropdown for workflow mode
        self._format_dropdown = ft.Dropdown(
            value=self.current_format,
            options=[
                ft.dropdown.Option("yaml", "YAML"),
                ft.dropdown.Option("json", "JSON"),
                ft.dropdown.Option("python", "Python DSL"),
            ],
            on_change=lambda e: (
                self.on_format_change(e.control.value) if self.on_format_change else None
            ),
            width=120,
            height=32,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            text_size=12,
            visible=self.workflow_mode,
        )

        toolbar_row = ft.Container(
            content=ft.Row(
                controls=[
                    # Toggle sidebar
                    ft.IconButton(
                        icon=(ft.Icons.MENU_OPEN if self.sidebar_visible else ft.Icons.MENU),
                        tooltip="Toggle Sidebar",
                        on_click=lambda e: self.on_toggle_sidebar(),
                    ),
                    ft.VerticalDivider(width=1),
                    # Open folder
                    ft.IconButton(
                        icon=ft.Icons.FOLDER_OPEN,
                        tooltip="Open Folder",
                        on_click=lambda e: self.on_open_folder(),
                    ),
                    # Workflow format dropdown (visible only in workflow mode)
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.SCHEMA,
                                    size=16,
                                    color=SkynetteTheme.TEXT_SECONDARY,
                                ),
                                self._format_dropdown,
                            ],
                            spacing=4,
                        ),
                        visible=self.workflow_mode,
                        padding=ft.padding.only(left=8),
                    ),
                    ft.Container(expand=True),  # Spacer
                    # Toggle AI Panel
                    ft.IconButton(
                        icon=(
                            ft.Icons.SMART_TOY
                            if self.ai_panel_visible
                            else ft.Icons.SMART_TOY_OUTLINED
                        ),
                        tooltip="Toggle AI Assistant (Ctrl+Shift+A)",
                        on_click=lambda e: self.on_toggle_ai() if self.on_toggle_ai else None,
                        icon_color=SkynetteTheme.PRIMARY if self.ai_panel_visible else None,
                    ),
                    ft.VerticalDivider(width=1),
                    # Save
                    ft.IconButton(
                        icon=ft.Icons.SAVE,
                        tooltip="Save (Ctrl+S)",
                        on_click=lambda e: self.on_save(),
                    ),
                    # Save All
                    ft.IconButton(
                        icon=ft.Icons.SAVE_ALT,
                        tooltip="Save All",
                        on_click=lambda e: self.on_save_all(),
                        icon_color=SkynetteTheme.WARNING if self.has_unsaved else None,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            height=40,
            padding=ft.padding.symmetric(horizontal=8),
            bgcolor=SkynetteTheme.BG_SECONDARY,
            border=ft.border.only(bottom=ft.BorderSide(1, SkynetteTheme.BORDER)),
        )

        self.controls = [toolbar_row]

    def update_state(self, sidebar_visible: bool, has_unsaved: bool) -> None:
        """Update toolbar button states.

        Args:
            sidebar_visible: Whether sidebar is currently visible.
            has_unsaved: Whether there are unsaved files.
        """
        self.sidebar_visible = sidebar_visible
        self.has_unsaved = has_unsaved
        self.update()

    def set_workflow_mode(self, enabled: bool, current_format: str = "yaml") -> None:
        """Enable or disable workflow editing mode.

        Args:
            enabled: Whether to enable workflow mode.
            current_format: Current format to show in dropdown.
        """
        self.workflow_mode = enabled
        self.current_format = current_format
        if self._format_dropdown:
            self._format_dropdown.visible = enabled
            self._format_dropdown.value = current_format
        self.update()
