# src/ui/views/code_editor/state.py
"""Centralized state for code editor components."""

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class OpenFile:
    """Represents an open file in the editor.

    Tracks file metadata, content, and editing state.
    """

    path: str
    content: str
    language: str
    is_dirty: bool = False
    scroll_position: int = 0
    cursor_position: int = 0


@dataclass
class EditorState:
    """Centralized state for code editor components.

    Follows the listener/notify pattern from AIHubState for reactive
    updates across editor components (tabs, file tree, status bar).

    Example:
        state = EditorState()
        state.add_listener(lambda: page.update())
        state.open_file("main.py", "print('hello')", "python")
    """

    open_files: list[OpenFile] = field(default_factory=list)
    active_file_index: int = -1
    file_tree_root: str | None = None
    sidebar_width: int = 250
    sidebar_visible: bool = True

    _listeners: list[Callable[[], None]] = field(default_factory=list, repr=False)

    def add_listener(self, callback: Callable[[], None]) -> None:
        """Register a callback to be notified of state changes."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[], None]) -> None:
        """Unregister a callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify(self) -> None:
        """Notify all listeners of state change."""
        for listener in self._listeners:
            listener()

    @property
    def active_file(self) -> OpenFile | None:
        """Get currently active file, or None if no file is open."""
        if 0 <= self.active_file_index < len(self.open_files):
            return self.open_files[self.active_file_index]
        return None

    def open_file(self, path: str, content: str, language: str) -> None:
        """Open file or focus if already open.

        If the file is already open, sets it as active without
        creating a duplicate. Otherwise, adds new file and sets active.

        Args:
            path: File path (used for identification and display).
            content: File content to display in editor.
            language: Language for syntax highlighting.
        """
        # Check for duplicate - focus if already open
        for i, f in enumerate(self.open_files):
            if f.path == path:
                self.active_file_index = i
                self.notify()
                return

        # Add new file
        new_file = OpenFile(path=path, content=content, language=language)
        self.open_files.append(new_file)
        self.active_file_index = len(self.open_files) - 1
        self.notify()

    def close_file(self, index: int) -> bool:
        """Close file at index.

        Args:
            index: Index of file to close.

        Returns:
            True if file was dirty (caller may want to prompt for save).
        """
        if not (0 <= index < len(self.open_files)):
            return False

        was_dirty = self.open_files[index].is_dirty
        self.open_files.pop(index)

        # Adjust active index
        if len(self.open_files) == 0:
            self.active_file_index = -1
        elif index <= self.active_file_index:
            self.active_file_index = max(0, self.active_file_index - 1)

        self.notify()
        return was_dirty

    def set_content(self, index: int, content: str) -> None:
        """Update file content and mark dirty.

        Args:
            index: Index of file to update.
            content: New content value.
        """
        if 0 <= index < len(self.open_files):
            self.open_files[index].content = content
            self.open_files[index].is_dirty = True
            self.notify()

    def mark_saved(self, index: int) -> None:
        """Mark file as saved (clear dirty flag).

        Args:
            index: Index of file to mark as saved.
        """
        if 0 <= index < len(self.open_files):
            self.open_files[index].is_dirty = False
            self.notify()

    def set_active(self, index: int) -> None:
        """Set active file by index.

        Args:
            index: Index of file to activate.
        """
        if 0 <= index < len(self.open_files):
            self.active_file_index = index
            self.notify()

    def set_sidebar_width(self, width: int) -> None:
        """Update sidebar width.

        Args:
            width: New sidebar width in pixels.
        """
        self.sidebar_width = width
        self.notify()

    def toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        self.sidebar_visible = not self.sidebar_visible
        self.notify()

    def set_file_tree_root(self, path: str) -> None:
        """Set root path for file tree.

        Args:
            path: Root directory path for file tree display.
        """
        self.file_tree_root = path
        self.notify()

    def dispose(self) -> None:
        """Clear all state and listeners."""
        self._listeners.clear()
        self.open_files.clear()
        self.active_file_index = -1
