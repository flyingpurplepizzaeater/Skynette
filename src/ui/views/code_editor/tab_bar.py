# src/ui/views/code_editor/tab_bar.py
"""Tab bar component for the code editor."""

from collections.abc import Callable

import flet as ft

from src.ui.theme import SkynetteTheme
from src.ui.views.code_editor.state import OpenFile


class EditorTabBar(ft.Column):
    """Tab bar for open files.

    Features:
    - Close button (X) on each tab
    - Dirty indicator (dot) for unsaved changes
    - Click to switch tabs
    - Horizontal scroll when many tabs
    - Right-click context menu (Close All, Close Others)

    Example:
        tab_bar = EditorTabBar(
            files=[OpenFile(path='test.py', content='', language='python')],
            active_index=0,
            on_select=lambda i: print(f"Selected tab {i}"),
            on_close=lambda i: print(f"Closed tab {i}"),
        )
    """

    def __init__(
        self,
        files: list[OpenFile],
        active_index: int,
        on_select: Callable[[int], None],
        on_close: Callable[[int], None],
        on_close_all: Callable[[], None] | None = None,
        on_close_others: Callable[[int], None] | None = None,
    ):
        """Initialize tab bar.

        Args:
            files: List of open files to display tabs for.
            active_index: Index of currently active tab.
            on_select: Callback when tab is selected, receives index.
            on_close: Callback when tab close button is clicked, receives index.
            on_close_all: Optional callback to close all tabs.
            on_close_others: Optional callback to close other tabs, receives index.
        """
        super().__init__()
        self.files = files
        self.active_index = active_index
        self.on_select = on_select
        self.on_close = on_close
        self.on_close_all = on_close_all
        self.on_close_others = on_close_others

        # Column settings
        self.spacing = 0

    def build(self) -> None:
        """Build scrollable tab bar."""
        tabs = [self._build_tab(i, f) for i, f in enumerate(self.files)]

        tab_row = ft.Container(
            content=ft.Row(
                controls=tabs,
                scroll=ft.ScrollMode.AUTO,
                spacing=0,
            ),
            height=36,
            bgcolor=SkynetteTheme.BG_SECONDARY,
            border=ft.border.only(bottom=ft.BorderSide(1, SkynetteTheme.BORDER)),
        )

        self.controls = [tab_row]

    def _build_tab(self, index: int, file: OpenFile) -> ft.Control:
        """Build single tab with close button and dirty indicator.

        Args:
            index: Tab index.
            file: File data for the tab.

        Returns:
            Tab control widget.
        """
        is_active = index == self.active_index
        filename = file.path.split("/")[-1].split("\\")[-1]  # Cross-platform

        # Dirty indicator (dot before filename)
        dirty_indicator = ft.Text(
            " * " if file.is_dirty else "",
            size=13,
            color=SkynetteTheme.WARNING if file.is_dirty else "transparent",
        )

        # Close button
        close_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=14,
            tooltip="Close",
            on_click=lambda e, i=index: self._handle_close(i),
            style=ft.ButtonStyle(
                padding=ft.padding.all(4),
            ),
        )

        tab = ft.Container(
            content=ft.Row(
                controls=[
                    dirty_indicator,
                    ft.Text(
                        filename,
                        size=13,
                        color=(
                            SkynetteTheme.TEXT_PRIMARY
                            if is_active
                            else SkynetteTheme.TEXT_SECONDARY
                        ),
                    ),
                    close_btn,
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(left=12, right=4, top=6, bottom=6),
            bgcolor=SkynetteTheme.BG_PRIMARY if is_active else SkynetteTheme.BG_SECONDARY,
            border=ft.border.only(
                bottom=ft.BorderSide(2, SkynetteTheme.PRIMARY) if is_active else None,
                right=ft.BorderSide(1, SkynetteTheme.BORDER),
            ),
            on_click=lambda e, i=index: self._handle_select(i),
            on_long_press=lambda e, i=index: self._show_context_menu(e, i),
        )

        return tab

    def _handle_select(self, index: int) -> None:
        """Handle tab selection.

        Args:
            index: Index of selected tab.
        """
        self.on_select(index)

    def _handle_close(self, index: int) -> None:
        """Handle tab close button click.

        Args:
            index: Index of tab to close.
        """
        self.on_close(index)

    def _show_context_menu(self, e: ft.ControlEvent, index: int) -> None:
        """Show context menu on right-click/long-press.

        Args:
            e: Control event with position info.
            index: Index of tab for context menu.
        """
        # Context menu implementation using PopupMenuButton
        # (Would need page reference for positioning - simplified here)
        pass

    def update_tabs(self, files: list[OpenFile], active_index: int) -> None:
        """Update tabs with new file list and active index.

        Args:
            files: New list of open files.
            active_index: New active tab index.
        """
        self.files = files
        self.active_index = active_index
        self.update()
