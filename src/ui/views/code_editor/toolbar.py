# src/ui/views/code_editor/toolbar.py
"""Toolbar component for the code editor."""

from collections.abc import Callable

import flet as ft

from src.ui.theme import SkynetteTheme


class EditorToolbar(ft.Column):
    """Toolbar for code editor actions.

    Actions: Save, Save All, Toggle Sidebar, Open Folder

    Example:
        toolbar = EditorToolbar(
            on_save=lambda: print("Save"),
            on_save_all=lambda: print("Save all"),
            on_toggle_sidebar=lambda: print("Toggle sidebar"),
            on_open_folder=lambda: print("Open folder"),
        )
    """

    def __init__(
        self,
        on_save: Callable[[], None],
        on_save_all: Callable[[], None],
        on_toggle_sidebar: Callable[[], None],
        on_open_folder: Callable[[], None],
        sidebar_visible: bool = True,
        has_unsaved: bool = False,
    ):
        """Initialize toolbar.

        Args:
            on_save: Callback for save action.
            on_save_all: Callback for save all action.
            on_toggle_sidebar: Callback for toggle sidebar action.
            on_open_folder: Callback for open folder action.
            sidebar_visible: Whether sidebar is currently visible.
            has_unsaved: Whether there are unsaved files (highlights Save All).
        """
        super().__init__()
        self.on_save = on_save
        self.on_save_all = on_save_all
        self.on_toggle_sidebar = on_toggle_sidebar
        self.on_open_folder = on_open_folder
        self.sidebar_visible = sidebar_visible
        self.has_unsaved = has_unsaved

        # Column settings
        self.spacing = 0

    def build(self) -> None:
        """Build toolbar row."""
        toolbar_row = ft.Container(
            content=ft.Row(
                controls=[
                    # Toggle sidebar
                    ft.IconButton(
                        icon=(
                            ft.Icons.MENU_OPEN
                            if self.sidebar_visible
                            else ft.Icons.MENU
                        ),
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
                    ft.Container(expand=True),  # Spacer
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
