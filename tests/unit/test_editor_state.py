# tests/unit/test_editor_state.py
"""Unit tests for code editor state management."""

import pytest
from src.ui.views.code_editor.state import EditorState, OpenFile


class TestOpenFile:
    """Tests for OpenFile dataclass."""

    def test_defaults(self):
        """OpenFile has sensible defaults."""
        f = OpenFile(path="/test.py", content="x = 1", language="python")
        assert f.is_dirty is False
        assert f.scroll_position == 0
        assert f.cursor_position == 0

    def test_dirty_flag(self):
        """Dirty flag can be set."""
        f = OpenFile(path="/test.py", content="", language="python", is_dirty=True)
        assert f.is_dirty is True


class TestEditorState:
    """Tests for EditorState container."""

    def setup_method(self):
        self.state = EditorState()
        self.listener_called = False

    def _listener(self):
        self.listener_called = True

    def test_initial_state(self):
        """Initial state has no open files."""
        assert len(self.state.open_files) == 0
        assert self.state.active_file_index == -1
        assert self.state.active_file is None

    def test_add_listener(self):
        """Listener is added and notified."""
        self.state.add_listener(self._listener)
        self.state.notify()
        assert self.listener_called

    def test_remove_listener(self):
        """Listener can be removed."""
        self.state.add_listener(self._listener)
        self.state.remove_listener(self._listener)
        self.state.notify()
        assert not self.listener_called

    def test_open_file_adds_to_list(self):
        """Opening file adds to open_files."""
        self.state.open_file("/test.py", "content", "python")
        assert len(self.state.open_files) == 1
        assert self.state.open_files[0].path == "/test.py"

    def test_open_file_sets_active(self):
        """Opening file sets it as active."""
        self.state.open_file("/test.py", "content", "python")
        assert self.state.active_file_index == 0
        assert self.state.active_file.path == "/test.py"

    def test_open_same_file_focuses_existing(self):
        """Opening already-open file focuses it instead of duplicating."""
        self.state.open_file("/test.py", "content", "python")
        self.state.open_file("/other.py", "other", "python")
        self.state.open_file("/test.py", "content", "python")

        assert len(self.state.open_files) == 2
        assert self.state.active_file_index == 0

    def test_close_file(self):
        """Closing file removes from list."""
        self.state.open_file("/test.py", "content", "python")
        result = self.state.close_file(0)
        assert len(self.state.open_files) == 0
        assert result is False  # Was not dirty

    def test_close_dirty_file_returns_true(self):
        """Closing dirty file returns True."""
        self.state.open_file("/test.py", "content", "python")
        self.state.set_content(0, "new content")
        result = self.state.close_file(0)
        assert result is True  # Was dirty

    def test_set_content_marks_dirty(self):
        """Setting content marks file as dirty."""
        self.state.open_file("/test.py", "content", "python")
        self.state.set_content(0, "new content")
        assert self.state.open_files[0].is_dirty is True
        assert self.state.open_files[0].content == "new content"

    def test_mark_saved_clears_dirty(self):
        """Marking saved clears dirty flag."""
        self.state.open_file("/test.py", "content", "python")
        self.state.set_content(0, "new content")
        self.state.mark_saved(0)
        assert self.state.open_files[0].is_dirty is False

    def test_set_active(self):
        """Can set active file by index."""
        self.state.open_file("/a.py", "a", "python")
        self.state.open_file("/b.py", "b", "python")
        self.state.set_active(0)
        assert self.state.active_file_index == 0

    def test_toggle_sidebar(self):
        """Sidebar visibility can be toggled."""
        assert self.state.sidebar_visible is True
        self.state.toggle_sidebar()
        assert self.state.sidebar_visible is False
        self.state.toggle_sidebar()
        assert self.state.sidebar_visible is True

    def test_set_sidebar_width(self):
        """Sidebar width can be set."""
        self.state.set_sidebar_width(300)
        assert self.state.sidebar_width == 300

    def test_set_file_tree_root(self):
        """File tree root can be set."""
        self.state.set_file_tree_root("/projects")
        assert self.state.file_tree_root == "/projects"

    def test_dispose_clears_everything(self):
        """Dispose clears state and listeners."""
        self.state.add_listener(self._listener)
        self.state.open_file("/test.py", "content", "python")
        self.state.dispose()

        assert len(self.state._listeners) == 0
        assert len(self.state.open_files) == 0
        assert self.state.active_file_index == -1

    def test_operations_notify_listeners(self):
        """State-changing operations notify listeners."""
        self.state.add_listener(self._listener)

        operations = [
            lambda: self.state.open_file("/t.py", "x", "python"),
            lambda: self.state.set_content(0, "y"),
            lambda: self.state.set_active(0),
            lambda: self.state.toggle_sidebar(),
            lambda: self.state.set_sidebar_width(200),
        ]

        for op in operations:
            self.listener_called = False
            op()
            assert self.listener_called, f"Listener not called for {op}"

    def test_close_file_adjusts_active_index(self):
        """Closing file before active adjusts active index."""
        self.state.open_file("/a.py", "a", "python")
        self.state.open_file("/b.py", "b", "python")
        self.state.open_file("/c.py", "c", "python")
        self.state.set_active(2)  # c.py is active

        self.state.close_file(0)  # Close a.py

        # Active should shift from 2 to 1
        assert self.state.active_file_index == 1
        assert self.state.active_file.path == "/c.py"

    def test_close_active_file_selects_previous(self):
        """Closing active file selects previous file."""
        self.state.open_file("/a.py", "a", "python")
        self.state.open_file("/b.py", "b", "python")
        assert self.state.active_file_index == 1

        self.state.close_file(1)

        assert self.state.active_file_index == 0
        assert self.state.active_file.path == "/a.py"

    def test_close_only_file_resets_active(self):
        """Closing the only open file resets active index to -1."""
        self.state.open_file("/a.py", "a", "python")
        self.state.close_file(0)

        assert self.state.active_file_index == -1
        assert self.state.active_file is None
