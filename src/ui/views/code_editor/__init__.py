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
import os
import tempfile
from collections.abc import Awaitable

import flet as ft

from src.ai.completions import CompletionService
from src.ai.gateway import get_gateway
from src.rag.chromadb_client import ChromaDBClient
from src.rag.embeddings import EmbeddingManager
from src.services.editor import FileService, PygmentsHighlighter
from src.ui.components.code_editor import ResizableSplitPanel
from src.ui.theme import SkynetteTheme
from src.ui.views.code_editor.ai_panel import (
    ChatPanel,
    ChatState,
    DiffPreview,
    GhostTextOverlay,
    Suggestion,
)
from src.ui.views.code_editor.ai_panel.rag_context import RAGContextProvider
from src.ui.views.code_editor.editor import CodeEditor
from src.ui.views.code_editor.file_tree import FileTree
from src.ui.views.code_editor.state import EditorState, OpenFile
from src.ui.views.code_editor.tab_bar import EditorTabBar
from src.ui.views.code_editor.toolbar import EditorToolbar
from src.ui.views.code_editor.workflow_bridge import WorkflowBridge, WorkflowFormat


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
        self._page_ref = page
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

        # AI assistance state
        self.chat_state = ChatState()
        self._ai_panel_visible = False
        self._ai_panel_width = 350  # Default width
        self._gateway = get_gateway()
        self._completion_service = CompletionService(self._gateway)

        # AI component references
        self._chat_panel: ChatPanel | None = None
        self._ai_panel_container: ft.Container | None = None
        self._editor_with_ai: ResizableSplitPanel | None = None

        # Diff preview state
        self._pending_diff: tuple[str, str] | None = None  # (original, modified)
        self._diff_dialog: ft.AlertDialog | None = None

        # Workflow editing state
        self._workflow_bridge: WorkflowBridge | None = None
        self._current_workflow_id: str | None = None
        self._workflow_format: WorkflowFormat = WorkflowFormat.YAML
        self._validation_task: asyncio.Task | None = None
        self._validation_errors: list[str] = []

        # RAG context for AI chat
        self._chromadb_client: ChromaDBClient | None = None
        self._embedding_manager: EmbeddingManager | None = None
        self._rag_provider: RAGContextProvider | None = None

        # File picker (must be added to page overlay before use)
        self._folder_picker = ft.FilePicker()
        if self._page_ref:
            self._page_ref.overlay.append(self._folder_picker)

        # Register state listener
        self.state.add_listener(self._on_state_change)

        # Register keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Column settings
        self.expand = True
        self.spacing = 0

    def build(self) -> None:
        """Build the complete editor layout."""
        # Toolbar with AI panel toggle and format selector
        self._toolbar = EditorToolbar(
            on_save=self._save_current,
            on_save_all=self._save_all,
            on_toggle_sidebar=self._toggle_sidebar,
            on_open_folder=self._open_folder,
            on_toggle_ai=self.toggle_ai_panel,
            on_format_change=self._on_format_change,
            sidebar_visible=self.state.sidebar_visible,
            ai_panel_visible=self._ai_panel_visible,
            workflow_mode=self._current_workflow_id is not None,
            current_format=self._workflow_format.value,
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

        # Initialize RAG components for AI chat context
        rag_persist_dir = os.path.join(tempfile.gettempdir(), "skynette_rag")
        self._chromadb_client = ChromaDBClient(rag_persist_dir)
        self._embedding_manager = EmbeddingManager()
        self._rag_provider = RAGContextProvider(
            chromadb_client=self._chromadb_client,
            embedding_manager=self._embedding_manager,
        )

        # Chat panel (initially hidden)
        self._chat_panel = ChatPanel(
            page=self._page_ref,
            state=self.chat_state,
            gateway=self._gateway,
            on_include_code=self._get_selected_code,
            on_code_suggestion=self.show_diff_from_ai,
            rag_provider=self._rag_provider,
            get_project_root=lambda: self.state.file_tree_root,
        )

        # AI panel container (for visibility toggle)
        self._ai_panel_container = ft.Container(
            content=self._chat_panel,
            visible=self._ai_panel_visible,
            width=self._ai_panel_width,
        )

        # Wrap editor area with AI panel split
        self._editor_with_ai = ResizableSplitPanel(
            left=self._editor_area,
            right=self._ai_panel_container,
            initial_width=None,  # No initial split - full editor
            on_resize=self._on_ai_panel_resize,
        )

        # Main split: file tree | (editor + AI panel)
        self._split_panel = ResizableSplitPanel(
            left=self._file_tree,
            right=self._editor_with_ai,
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
                alignment=ft.alignment.Alignment(0, 0),
            )

        # Create editor for active file
        active = self.state.active_file
        self._editor = CodeEditor(
            content=active.content,
            language=active.language,
            on_change=self._on_content_change,
            on_request_completion=self._handle_completion_request,
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

        # Check if closing a workflow file
        is_workflow_file = (
            self._current_workflow_id
            and file.path.startswith("workflows/")
        )

        if file.is_dirty:
            self._show_save_dialog(index)
        else:
            self.state.close_file(index)
            if is_workflow_file:
                self._close_workflow()

    def _on_content_change(self, content: str) -> None:
        """Handle editor content change.

        Args:
            content: New content.
        """
        if self.state.active_file_index >= 0:
            self.state.set_content(self.state.active_file_index, content)

        # Trigger workflow validation if editing workflow
        if self._current_workflow_id and self._workflow_bridge:
            self._schedule_validation(content)

    def _handle_completion_request(self, code: str, language: str) -> None:
        """Handle completion request from editor.

        Args:
            code: Current code content (before cursor).
            language: Programming language.
        """
        asyncio.create_task(self._fetch_completion(code, language))

    async def _fetch_completion(self, code: str, language: str) -> None:
        """Fetch AI completion asynchronously.

        Args:
            code: Current code content (before cursor).
            language: Programming language.
        """
        from src.ai.completions import CompletionRequest

        request = CompletionRequest(
            code_before=code,
            code_after="",
            language=language,
            provider=self.chat_state.selected_provider,
        )

        try:
            suggestion = await self._completion_service.get_completion(request)
            if suggestion and self._editor:
                self._editor.show_suggestion(suggestion)
        except Exception:
            # Silently fail - inline suggestions are optional
            pass

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

            # Check if editing a workflow
            if self._current_workflow_id and self._workflow_bridge:
                success, error = self._workflow_bridge.save_from_code(
                    self._current_workflow_id, f.content, self._workflow_format
                )
                if success:
                    self.state.mark_saved(self.state.active_file_index)
                else:
                    self._show_error(f"Workflow save failed: {error}")
                return

            # Normal file save
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

    def toggle_ai_panel(self) -> None:
        """Toggle AI chat panel visibility."""
        self._ai_panel_visible = not self._ai_panel_visible
        if self._ai_panel_container:
            self._ai_panel_container.visible = self._ai_panel_visible
        if self._toolbar:
            self._toolbar.ai_panel_visible = self._ai_panel_visible
        self.update()

    def _get_selected_code(self) -> str:
        """Get selected code from editor for context.

        Returns:
            Currently returns entire file content.
            TODO: Get actual selection when TextField supports it.
        """
        if self._editor and self.state.active_file:
            return self.state.active_file.content
        return ""

    def _on_ai_panel_resize(self, width: int) -> None:
        """Handle AI panel resize.

        Args:
            width: New AI panel width.
        """
        self._ai_panel_width = width

    # Workflow editing methods
    def open_workflow(
        self,
        workflow_id: str,
        format: WorkflowFormat = WorkflowFormat.YAML,
    ) -> bool:
        """Open a workflow for editing in code editor.

        Args:
            workflow_id: ID of workflow to open.
            format: Format to display (YAML, JSON, or Python DSL).

        Returns:
            True if workflow opened successfully.
        """
        # Create bridge if not exists
        if self._workflow_bridge is None:
            self._workflow_bridge = WorkflowBridge()

        # Load workflow as code
        code = self._workflow_bridge.load_as_code(workflow_id, format)
        if code is None:
            self._show_error(f"Workflow not found: {workflow_id}")
            return False

        # Get workflow name for virtual file path
        name = self._workflow_bridge.get_workflow_name(workflow_id) or "workflow"
        ext = {"yaml": "yaml", "json": "json", "python": "py"}[format.value]
        virtual_path = f"workflows/{name}.{ext}"

        # Determine language for highlighting
        language = {"yaml": "yaml", "json": "json", "python": "python"}[format.value]

        # Open in editor
        self.state.open_file(virtual_path, code, language)

        # Store workflow state
        self._current_workflow_id = workflow_id
        self._workflow_format = format

        # Update toolbar to show format dropdown
        if self._toolbar:
            self._toolbar.set_workflow_mode(True, format.value)

        return True

    def _on_format_change(self, format_value: str) -> None:
        """Handle workflow format change from dropdown.

        Args:
            format_value: New format value (yaml/json/python).
        """
        if not self._current_workflow_id or not self._workflow_bridge:
            return

        # Map string to enum
        format_map = {
            "yaml": WorkflowFormat.YAML,
            "json": WorkflowFormat.JSON,
            "python": WorkflowFormat.PYTHON_DSL,
        }
        new_format = format_map.get(format_value)
        if not new_format or new_format == self._workflow_format:
            return

        # Get current content and convert
        if self.state.active_file:
            current_content = self.state.active_file.content
            converted, error = self._workflow_bridge.convert_format(
                current_content, self._workflow_format, new_format
            )

            if error:
                self._show_error(f"Conversion failed: {error}")
                # Reset dropdown to previous value
                if self._toolbar and self._toolbar._format_dropdown:
                    self._toolbar._format_dropdown.value = self._workflow_format.value
                    self._toolbar.update()
                return

            # Update format and content
            self._workflow_format = new_format

            # Update file extension in path
            name = self._workflow_bridge.get_workflow_name(
                self._current_workflow_id
            ) or "workflow"
            ext = {"yaml": "yaml", "json": "json", "python": "py"}[new_format.value]
            new_path = f"workflows/{name}.{ext}"
            language = {"yaml": "yaml", "json": "json", "python": "python"}[
                new_format.value
            ]

            # Update the file in state
            if self.state.active_file_index >= 0:
                self.state.open_files[self.state.active_file_index].path = new_path
                self.state.open_files[self.state.active_file_index].language = language
                self.state.set_content(self.state.active_file_index, converted)

            # Update editor
            if self._editor:
                self._editor.set_content(converted)

    def _close_workflow(self) -> None:
        """Clear workflow editing state."""
        self._current_workflow_id = None
        self._workflow_format = WorkflowFormat.YAML
        self._validation_errors = []
        if self._validation_task:
            self._validation_task.cancel()
            self._validation_task = None
        if self._toolbar:
            self._toolbar.set_workflow_mode(False)

    def _schedule_validation(self, content: str) -> None:
        """Schedule debounced workflow validation.

        Args:
            content: Current editor content.
        """
        # Cancel any pending validation
        if self._validation_task:
            self._validation_task.cancel()

        # Schedule new validation after 500ms
        self._validation_task = asyncio.create_task(
            self._validate_after_delay(content, 0.5)
        )

    async def _validate_after_delay(self, content: str, delay: float) -> None:
        """Validate workflow content after delay.

        Args:
            content: Content to validate.
            delay: Delay in seconds.
        """
        try:
            await asyncio.sleep(delay)

            if not self._workflow_bridge:
                return

            # Run validation
            errors = self._workflow_bridge.validate_code(content, self._workflow_format)

            # Update validation state
            self._validation_errors = errors

            # Show validation status in snackbar if errors
            if errors:
                self._show_validation_warnings(errors)

        except asyncio.CancelledError:
            # Validation was cancelled - normal when typing continues
            pass
        except Exception as e:
            logger.warning(f"Validation error: {e}")

    def _show_validation_warnings(self, errors: list[str]) -> None:
        """Show validation warnings in snackbar.

        Args:
            errors: List of validation errors/warnings.
        """
        # Only show first few errors
        shown_errors = errors[:3]
        message = " | ".join(shown_errors)
        if len(errors) > 3:
            message += f" (+{len(errors) - 3} more)"

        self._page_ref.snack_bar = ft.SnackBar(
            content=ft.Text(f"Warnings: {message}"),
            bgcolor=SkynetteTheme.WARNING,
            duration=3000,
        )
        self._page_ref.snack_bar.open = True
        self._page_ref.update()

    async def _open_folder(self) -> None:
        """Open folder picker."""
        path = await self._folder_picker.get_directory_path()
        if path:
            self.state.set_file_tree_root(path)
            if self._file_tree:
                self._file_tree.set_root(path)

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
            self._page_ref.update()

        def handle_discard(e: ft.ControlEvent) -> None:
            self.state.close_file(index)
            dialog.open = False
            self._page_ref.update()

        def handle_cancel(e: ft.ControlEvent) -> None:
            dialog.open = False
            self._page_ref.update()

        dialog = ft.AlertDialog(
            title=ft.Text(f"Save changes to {filename}?"),
            content=ft.Text("Your changes will be lost if you don't save them."),
            actions=[
                ft.TextButton("Save", on_click=handle_save),
                ft.TextButton("Don't Save", on_click=handle_discard),
                ft.TextButton("Cancel", on_click=handle_cancel),
            ],
        )
        self._page_ref.overlay.append(dialog)
        dialog.open = True
        self._page_ref.update()

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
        self._page_ref.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=SkynetteTheme.ERROR,
        )
        self._page_ref.snack_bar.open = True
        self._page_ref.update()

    def _setup_keyboard_shortcuts(self) -> None:
        """Register keyboard shortcuts for AI features."""
        original_handler = self._page_ref.on_keyboard_event

        def on_keyboard(e: ft.KeyboardEvent) -> None:
            # Ctrl+Shift+A: Toggle AI panel
            if e.ctrl and e.shift and e.key == "A":
                self.toggle_ai_panel()
                return

            # Tab: Accept suggestion (when ghost text visible)
            if e.key == "Tab" and self._editor and self._editor._ghost_overlay:
                if self._editor._ghost_overlay.has_suggestion():
                    self._editor._ghost_overlay.accept()
                    return  # Don't let Tab propagate

            # Escape: Dismiss suggestion
            if e.key == "Escape" and self._editor and self._editor._ghost_overlay:
                if self._editor._ghost_overlay.has_suggestion():
                    self._editor._ghost_overlay.dismiss()
                    return

            # Ctrl+Shift+D: Show diff preview for last AI response
            if e.ctrl and e.shift and e.key == "D":
                self._show_diff_preview()
                return

            # Call original handler if any
            if original_handler:
                original_handler(e)

        self._page_ref.on_keyboard_event = on_keyboard

    def _cleanup_keyboard_shortcuts(self) -> None:
        """Remove keyboard shortcut handlers."""
        self._page_ref.on_keyboard_event = None

    def show_diff_from_ai(self, modified_code: str) -> None:
        """Show diff preview for AI-suggested changes.

        Called when AI response contains code that differs from current file.

        Args:
            modified_code: The modified code suggested by AI.
        """
        if not self.state.active_file:
            return

        original = self.state.active_file.content
        if original == modified_code:
            return  # No changes

        self._pending_diff = (original, modified_code)
        self._show_diff_preview()

    def _show_diff_preview(self) -> None:
        """Show diff preview dialog."""
        if not self._pending_diff:
            return

        original, modified = self._pending_diff
        filename = self.state.active_file.path if self.state.active_file else "file"

        diff_preview = DiffPreview(
            original=original,
            modified=modified,
            filename=filename.split("/")[-1].split("\\")[-1],
            on_accept=self._apply_diff,
            on_reject=self._cancel_diff,
        )

        self._diff_dialog = ft.AlertDialog(
            title=ft.Text("Review Changes"),
            content=ft.Container(
                content=diff_preview,
                width=700,
                height=500,
            ),
            actions=[],  # DiffPreview has its own buttons
            modal=True,
        )

        self._page_ref.overlay.append(self._diff_dialog)
        self._diff_dialog.open = True
        self._page_ref.update()

    def _apply_diff(self, content: str) -> None:
        """Apply diff changes to active file.

        Args:
            content: New content to apply.
        """
        if self.state.active_file_index >= 0:
            self.state.set_content(self.state.active_file_index, content)
            if self._editor:
                self._editor.set_content(content)

        self._close_diff_dialog()
        self._pending_diff = None

    def _cancel_diff(self) -> None:
        """Cancel diff preview."""
        self._close_diff_dialog()
        self._pending_diff = None

    def _close_diff_dialog(self) -> None:
        """Close diff dialog."""
        if self._diff_dialog:
            self._diff_dialog.open = False
            self._page_ref.update()

    def dispose(self) -> None:
        """Clean up all resources when view is destroyed."""
        # Remove keyboard shortcuts
        self._cleanup_keyboard_shortcuts()

        # Remove state listener
        self.state.remove_listener(self._on_state_change)

        # Dispose RAG components
        if self._embedding_manager:
            self._embedding_manager.shutdown()
        # ChromaDBClient and RAGContextProvider don't need explicit shutdown
        self._rag_provider = None
        self._chromadb_client = None
        self._embedding_manager = None

        # Dispose AI components
        if self._chat_panel:
            self._chat_panel.dispose()
        self.chat_state.dispose()
        self._completion_service.cancel_pending()

        # Dispose child components
        if self._editor:
            self._editor.dispose()
        if self._file_tree:
            self._file_tree.dispose()

        # Clear state
        self.state.dispose()

        # Clear component references
        self._toolbar = None
        self._tab_bar = None
        self._file_tree = None
        self._editor = None
        self._split_panel = None
        self._chat_panel = None
        self._ai_panel_container = None
        self._editor_with_ai = None


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
    "WorkflowBridge",
    "WorkflowFormat",
]
