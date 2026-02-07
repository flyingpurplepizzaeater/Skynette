# src/ui/views/code_editor/file_tree.py
"""File tree navigator for the code editor."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import flet as ft

from src.services.editor import FileService, get_file_icon
from src.ui.theme import SkynetteTheme


@dataclass
class FileTreeItem:
    """Represents a file or folder in the tree."""

    path: Path
    level: int
    is_expanded: bool = False

    @property
    def is_dir(self) -> bool:
        return self.path.is_dir()

    @property
    def name(self) -> str:
        return self.path.name


class FileTree(ft.Column):
    """File tree navigator with lazy loading.

    - Single click on folder: expand/collapse
    - Single click on file: trigger on_file_select callback
    - Lazy loads subdirectories on expand for performance
    """

    def __init__(
        self,
        root_path: str,
        on_file_select: Callable[[str], None],
        filter_text: str = "",
    ):
        super().__init__()
        self.root = Path(root_path)
        self.on_file_select = on_file_select
        self.filter_text = filter_text.lower()

        self.file_service = FileService()
        self.items: list[FileTreeItem] = []
        self.expanded_paths: set[str] = set()

        # Column settings
        self.expand = True
        self.spacing = 0

        # Reference to ListView for rebuilding
        self._list_view: ft.ListView | None = None

    def build(self) -> None:
        """Build file tree with filter input and list."""
        self._load_directory(self.root, level=0)

        # Filter input
        filter_input = ft.TextField(
            hint_text="Filter files...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=4,
            height=36,
            text_size=13,
            on_change=self._handle_filter_change,
        )

        # File list
        self._list_view = ft.ListView(
            controls=[self._build_item(item) for item in self.items],
            expand=True,
            spacing=0,
            item_extent=28,  # Fixed height for virtualization
        )

        self.controls = [
            ft.Container(
                content=filter_input,
                padding=ft.padding.all(8),
            ),
            ft.Container(
                content=self._list_view,
                expand=True,
            ),
        ]

    def _load_directory(self, path: Path, level: int) -> None:
        """Load directory contents at given level."""
        try:
            entries = self.file_service.list_directory(str(path))
            for entry in entries:
                entry_path = Path(entry.path)

                # Apply filter
                if self.filter_text and self.filter_text not in entry.name.lower():
                    if not entry.is_dir:  # Skip non-matching files
                        continue

                item = FileTreeItem(path=entry_path, level=level)
                self.items.append(item)

                # If directory is expanded, load children
                if entry.is_dir and str(entry_path) in self.expanded_paths:
                    item.is_expanded = True
                    self._load_directory(entry_path, level + 1)
        except PermissionError:
            pass  # Skip directories we can't access

    def _build_item(self, item: FileTreeItem) -> ft.Control:
        """Build a single tree item row."""
        indent = item.level * 16 + 8
        icon = get_file_icon(item.name, item.is_dir, item.is_expanded)

        # Expand/collapse indicator for folders
        expand_icon = None
        if item.is_dir:
            expand_icon = ft.Icon(
                ft.Icons.KEYBOARD_ARROW_DOWN if item.is_expanded else ft.Icons.KEYBOARD_ARROW_RIGHT,
                size=16,
                color=SkynetteTheme.TEXT_SECONDARY,
            )

        return ft.Container(
            content=ft.Row(
                controls=[
                    *([] if not expand_icon else [expand_icon]),
                    ft.Icon(icon, size=16, color=SkynetteTheme.TEXT_SECONDARY),
                    ft.Text(
                        item.name,
                        size=13,
                        color=SkynetteTheme.TEXT_PRIMARY,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.only(left=indent, top=4, bottom=4, right=8),
            on_click=lambda e, i=item: self._handle_click(i),
            on_hover=self._handle_hover,
            border_radius=4,
        )

    def _handle_click(self, item: FileTreeItem) -> None:
        """Handle click on tree item."""
        if item.is_dir:
            # Toggle expand/collapse
            path_str = str(item.path)
            if path_str in self.expanded_paths:
                self.expanded_paths.remove(path_str)
            else:
                self.expanded_paths.add(path_str)
            self._rebuild()
        else:
            # Select file
            self.on_file_select(str(item.path))

    def _handle_hover(self, e: ft.ControlEvent) -> None:
        """Highlight on hover."""
        e.control.bgcolor = SkynetteTheme.BG_SECONDARY if e.data == "true" else None
        e.control.update()

    def _handle_filter_change(self, e: ft.ControlEvent) -> None:
        """Handle filter text change."""
        self.filter_text = e.control.value.lower()
        self._rebuild()

    def _rebuild(self) -> None:
        """Rebuild tree with current expanded state and filter."""
        self.items.clear()
        self._load_directory(self.root, level=0)
        if self._list_view:
            self._list_view.controls = [self._build_item(item) for item in self.items]
            self._list_view.update()

    def set_root(self, path: str) -> None:
        """Change root directory."""
        self.root = Path(path)
        self.expanded_paths.clear()
        self._rebuild()

    def refresh(self) -> None:
        """Refresh current tree (e.g., after file creation)."""
        self._rebuild()

    def dispose(self) -> None:
        """Clean up file tree resources."""
        self.items.clear()
        self.expanded_paths.clear()
