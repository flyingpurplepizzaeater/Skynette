# src/ui/views/code_editor/__init__.py
"""Code editor view components.

This package contains the main code editor view and its components:
- CodeEditorView: Main view assembling all editor components
- EditorState: Centralized state management
- OpenFile: File data container
- FileTree: File tree navigator with lazy loading
- CodeEditor: Main editing component with syntax highlighting
- EditorTabBar: Tab bar for open files
- EditorToolbar: Toolbar with editor actions
"""

import asyncio
from collections.abc import Awaitable

import flet as ft

from src.services.editor import FileService, PygmentsHighlighter
from src.ui.components.code_editor import ResizableSplitPanel
from src.ui.theme import SkynetteTheme
from src.ui.views.code_editor.editor import CodeEditor
from src.ui.views.code_editor.file_tree import FileTree
from src.ui.views.code_editor.state import EditorState, OpenFile
from src.ui.views.code_editor.tab_bar import EditorTabBar
from src.ui.views.code_editor.toolbar import EditorToolbar


class CodeEditorView(ft.Column):
    """Main code editor view.

    Layout:
    - Toolbar at top
    - Resizable split: File tree | Editor area
    - Tab bar above editor
    - Editor content below tabs

    Assembles all editor components and handles state management.

    Example:
        editor_view = CodeEditorView(page)
        page.add(editor_view)
    """

    def __init__(self, page: ft.Page):
        """Initialize code editor view.

        Args:
            page: Flet page reference for dialogs and overlays.
        """
        super().__init__()
        self.page = page
        self.state = EditorState()
        self.file_service = FileService()
        self.highlighter = PygmentsHighlighter()

        # Component references
        self._toolbar: EditorToolbar | None = None
        self._tab_bar: EditorTabBar | None = None
        self._file_tree: FileTree | None = None
        self._editor: CodeEditor | None = None
        self._split_panel: ResizableSplitPanel | None = None
        self._editor_area: ft.Column | None = None

        # Register state listener
        self.state.add_listener(self._on_state_change)

        # Column settings
        self.expand = True
        self.spacing = 0

    def build(self) -> None:
        """Build the complete editor layout."""
        # Toolbar
        self._toolbar = EditorToolbar(
            on_save=self._save_current,
            on_save_all=self._save_all,
            on_toggle_sidebar=self._toggle_sidebar,
            on_open_folder=self._open_folder,
            sidebar_visible=self.state.sidebar_visible,
        )

        # File tree (with placeholder root)
        self._file_tree = FileTree(
            root_path=self.state.file_tree_root or ".",
            on_file_select=self._on_file_select,
        )

        # Tab bar
        self._tab_bar = EditorTabBar(
            files=self.state.open_files,
            active_index=self.state.active_file_index,
            on_select=self._on_tab_select,
            on_close=self._on_tab_close,
        )

        # Editor (placeholder when no file open)
        editor_content = self._build_editor_content()

        # Editor area (tabs + editor)
        self._editor_area = ft.Column(
            controls=[
                self._tab_bar,
                editor_content,
            ],
            expand=True,
            spacing=0,
        )

        # Split panel
        self._split_panel = ResizableSplitPanel(
            left=self._file_tree,
            right=self._editor_area,
            initial_width=self.state.sidebar_width,
            on_resize=self._on_sidebar_resize,
        )

        self.controls = [
            self._toolbar,
            self._split_panel,
        ]

    def _build_editor_content(self) -> ft.Control:
        """Build editor content based on active file.

        Returns:
            Editor control or placeholder.
        """
        if self.state.active_file is None:
            # No file open - show placeholder
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.CODE,
                            size=64,
                            color=SkynetteTheme.TEXT_SECONDARY,
                        ),
                        ft.Text(
                            "No file open",
                            size=16,
                            color=SkynetteTheme.TEXT_SECONDARY,
                        ),
                        ft.Text(
                            "Open a folder and select a file from the tree",
                            size=13,
                            color=SkynetteTheme.TEXT_SECONDARY,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                expand=True,
                alignment=ft.alignment.center,
            )

        # Create editor for active file
        active = self.state.active_file
        self._editor = CodeEditor(
            content=active.content,
            language=active.language,
            on_change=self._on_content_change,
        )
        return self._editor

    # Event handlers
    def _on_file_select(self, path: str) -> None:
        """Handle file selection from tree.

        Args:
            path: Selected file path.
        """
        asyncio.create_task(self._open_file_async(path))

    async def _open_file_async(self, path: str) -> None:
        """Open file asynchronously.

        Args:
            path: File path to open.
        """
        try:
            content = await self.file_service.read_file(path)
            language = self.highlighter.get_language_from_filename(path)
            self.state.open_file(path, content, language)
        except ValueError as e:
            # File too large
            self._show_error(str(e))
        except Exception as e:
            self._show_error(f"Failed to open file: {e}")

    def _on_tab_select(self, index: int) -> None:
        """Handle tab selection.

        Args:
            index: Selected tab index.
        """
        self.state.set_active(index)

    def _on_tab_close(self, index: int) -> None:
        """Handle tab close - prompt if dirty.

        Args:
            index: Tab index to close.
        """
        file = self.state.open_files[index]
        if file.is_dirty:
            self._show_save_dialog(index)
        else:
            self.state.close_file(index)

    def _on_content_change(self, content: str) -> None:
        """Handle editor content change.

        Args:
            content: New content.
        """
        if self.state.active_file_index >= 0:
            self.state.set_content(self.state.active_file_index, content)

    def _on_sidebar_resize(self, width: int) -> None:
        """Handle sidebar resize.

        Args:
            width: New sidebar width.
        """
        self.state.set_sidebar_width(width)

    def _on_state_change(self) -> None:
        """Handle state changes - rebuild UI."""
        # Rebuild tab bar
        if self._tab_bar:
            self._tab_bar.files = self.state.open_files
            self._tab_bar.active_index = self.state.active_file_index

        # Rebuild editor content
        if self._editor_area:
            editor_content = self._build_editor_content()
            if len(self._editor_area.controls) > 1:
                self._editor_area.controls[1] = editor_content

        # Update toolbar
        if self._toolbar:
            has_unsaved = any(f.is_dirty for f in self.state.open_files)
            self._toolbar.has_unsaved = has_unsaved
            self._toolbar.sidebar_visible = self.state.sidebar_visible

        self.update()

    # Actions
    def _save_current(self) -> None:
        """Save current file."""
        asyncio.create_task(self._save_current_async())

    async def _save_current_async(self) -> None:
        """Save current file asynchronously."""
        if self.state.active_file:
            f = self.state.active_file
            try:
                await self.file_service.write_file(f.path, f.content)
                self.state.mark_saved(self.state.active_file_index)
            except Exception as e:
                self._show_error(f"Save failed: {e}")

    def _save_all(self) -> None:
        """Save all dirty files."""
        asyncio.create_task(self._save_all_async())

    async def _save_all_async(self) -> None:
        """Save all dirty files asynchronously."""
        for i, f in enumerate(self.state.open_files):
            if f.is_dirty:
                try:
                    await self.file_service.write_file(f.path, f.content)
                    self.state.mark_saved(i)
                except Exception as e:
                    self._show_error(f"Failed to save {f.path}: {e}")

    def _toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        self.state.toggle_sidebar()
        if self._split_panel:
            self._split_panel.set_left_visible(self.state.sidebar_visible)

    def _open_folder(self) -> None:
        """Open folder picker."""
        picker = ft.FilePicker(on_result=self._on_folder_picked)
        self.page.overlay.append(picker)
        self.page.update()
        picker.get_directory_path()

    def _on_folder_picked(self, e: ft.FilePickerResultEvent) -> None:
        """Handle folder picker result.

        Args:
            e: File picker result event.
        """
        if e.path:
            self.state.set_file_tree_root(e.path)
            if self._file_tree:
                self._file_tree.set_root(e.path)

    def _show_save_dialog(self, index: int) -> None:
        """Show save/discard/cancel dialog for dirty file.

        Args:
            index: Index of file with unsaved changes.
        """
        file = self.state.open_files[index]
        filename = file.path.split("/")[-1].split("\\")[-1]

        def handle_save(e: ft.ControlEvent) -> None:
            asyncio.create_task(self._save_and_close(index))
            dialog.open = False
            self.page.update()

        def handle_discard(e: ft.ControlEvent) -> None:
            self.state.close_file(index)
            dialog.open = False
            self.page.update()

        def handle_cancel(e: ft.ControlEvent) -> None:
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(f"Save changes to {filename}?"),
            content=ft.Text("Your changes will be lost if you don't save them."),
            actions=[
                ft.TextButton("Save", on_click=handle_save),
                ft.TextButton("Don't Save", on_click=handle_discard),
                ft.TextButton("Cancel", on_click=handle_cancel),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    async def _save_and_close(self, index: int) -> None:
        """Save file then close tab.

        Args:
            index: Index of file to save and close.
        """
        f = self.state.open_files[index]
        await self.file_service.write_file(f.path, f.content)
        self.state.close_file(index)

    def _show_error(self, message: str) -> None:
        """Show error snackbar.

        Args:
            message: Error message to display.
        """
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=SkynetteTheme.ERROR,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def dispose(self) -> None:
        """Clean up resources."""
        self.state.remove_listener(self._on_state_change)


# Export re-exports for backward compatibility
from src.ui.views.code_editor.file_tree import FileTreeItem

__all__ = [
    "CodeEditorView",
    "EditorState",
    "OpenFile",
    "FileTree",
    "FileTreeItem",
    "CodeEditor",
    "EditorTabBar",
    "EditorToolbar",
]
