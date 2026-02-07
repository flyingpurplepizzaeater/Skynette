# src/ui/components/code_editor/resizable_panel.py
"""Resizable two-panel layout component for the code editor."""

from collections.abc import Callable

import flet as ft

from src.ui.theme import SkynetteTheme


class ResizableSplitPanel(ft.Row):
    """Two-panel layout with draggable divider.

    Left panel has fixed width, right panel expands.
    Divider can be dragged to resize.
    """

    MIN_WIDTH = 150
    MAX_WIDTH = 500

    def __init__(
        self,
        left: ft.Control,
        right: ft.Control,
        initial_width: int = 250,
        on_resize: Callable[[int], None] | None = None,
    ):
        super().__init__()
        self.left_panel = left
        self.right_panel = right
        self.left_width = initial_width
        self.on_resize = on_resize

        self._left_container: ft.Container | None = None

        # Row settings
        self.expand = True
        self.spacing = 0

    def build(self) -> None:
        """Build split panel with draggable divider."""
        # Divider with drag handling
        divider = ft.GestureDetector(
            content=ft.Container(
                width=4,
                bgcolor=SkynetteTheme.BORDER,
            ),
            on_horizontal_drag_start=self._on_drag_start,
            on_horizontal_drag_update=self._on_drag_update,
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
        )

        self._left_container = ft.Container(
            content=self.left_panel,
            width=self.left_width,
            bgcolor=SkynetteTheme.BG_SECONDARY,
        )

        self.controls = [
            self._left_container,
            divider,
            ft.Container(
                content=self.right_panel,
                expand=True,
                bgcolor=SkynetteTheme.BG_PRIMARY,
            ),
        ]

    def _on_drag_start(self, e: ft.DragStartEvent) -> None:
        """Capture initial state on drag start."""
        pass  # Could add visual feedback here

    def _on_drag_update(self, e: ft.DragUpdateEvent) -> None:
        """Handle drag to resize."""
        new_width = self.left_width + e.delta_x
        new_width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, new_width))

        if new_width != self.left_width:
            self.left_width = int(new_width)
            if self._left_container:
                self._left_container.width = self.left_width
                self._left_container.update()

            if self.on_resize:
                self.on_resize(self.left_width)

    def set_left_width(self, width: int) -> None:
        """Programmatically set left panel width."""
        self.left_width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, width))
        if self._left_container:
            self._left_container.width = self.left_width
            self._left_container.update()

    def set_left_visible(self, visible: bool) -> None:
        """Show/hide left panel."""
        if self._left_container:
            self._left_container.visible = visible
            self._left_container.update()
