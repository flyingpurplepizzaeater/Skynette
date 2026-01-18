# tests/unit/test_editor_services.py
"""Unit tests for code editor services."""

import pytest
import tempfile
import os
from pathlib import Path

from src.services.editor import (
    PygmentsHighlighter,
    FileService,
    get_file_icon,
    LANGUAGE_ICONS,
    FOLDER_ICON,
    FOLDER_OPEN_ICON,
)


class TestPygmentsHighlighter:
    """Tests for syntax highlighting service."""

    def setup_method(self):
        self.highlighter = PygmentsHighlighter()

    def test_highlight_python_returns_spans(self):
        """Highlighting Python code returns multiple TextSpans."""
        code = "def hello():\n    print('world')"
        spans = self.highlighter.highlight(code, "python")
        assert len(spans) > 1
        assert all(hasattr(s, 'text') for s in spans)

    def test_highlight_unknown_language_returns_unstyled(self):
        """Unknown language returns single unstyled span."""
        code = "some random text"
        spans = self.highlighter.highlight(code, "not_a_language")
        assert len(spans) == 1
        assert spans[0].text == code

    def test_highlight_empty_string(self):
        """Empty string returns empty list or single empty span."""
        spans = self.highlighter.highlight("", "python")
        # Should handle gracefully
        assert isinstance(spans, list)

    def test_highlight_javascript(self):
        """JavaScript code is highlighted."""
        code = "const x = () => { return 42; };"
        spans = self.highlighter.highlight(code, "javascript")
        assert len(spans) > 1

    def test_get_language_from_filename_python(self):
        """Python files detected correctly."""
        assert self.highlighter.get_language_from_filename("test.py") == "python"

    def test_get_language_from_filename_javascript(self):
        """JavaScript files detected correctly."""
        lang = self.highlighter.get_language_from_filename("app.js")
        assert lang in ("javascript", "js")

    def test_get_language_from_filename_unknown(self):
        """Unknown extension returns text."""
        lang = self.highlighter.get_language_from_filename("file.xyz123")
        assert lang == "text"

    def test_token_colors_are_hex(self):
        """Token colors are valid hex color codes."""
        for token, color in PygmentsHighlighter.TOKEN_COLORS.items():
            assert color.startswith("#")
            assert len(color) == 7  # #RRGGBB


class TestFileService:
    """Tests for file I/O service."""

    def setup_method(self):
        self.service = FileService()

    def test_file_exists_true(self):
        """Existing file returns True."""
        # Use this test file itself
        assert self.service.file_exists(__file__)

    def test_file_exists_false(self):
        """Non-existent file returns False."""
        assert not self.service.file_exists("/nonexistent/path/file.txt")

    def test_get_file_size(self):
        """File size returns positive integer for existing file."""
        size = self.service.get_file_size(__file__)
        assert size > 0

    def test_list_directory_returns_fileinfo(self):
        """List directory returns FileInfo objects."""
        entries = self.service.list_directory(os.path.dirname(__file__))
        assert len(entries) > 0
        assert all(hasattr(e, 'name') for e in entries)
        assert all(hasattr(e, 'is_dir') for e in entries)

    def test_list_directory_sorts_folders_first(self):
        """Directories appear before files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file and a folder
            Path(tmpdir, "aaa_file.txt").touch()
            Path(tmpdir, "zzz_folder").mkdir()

            entries = self.service.list_directory(tmpdir)
            # Folder should come first despite alphabetical order
            assert entries[0].is_dir
            assert entries[0].name == "zzz_folder"

    @pytest.mark.asyncio
    async def test_read_file(self):
        """Read file returns content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            f.flush()
            path = f.name

        try:
            content = await self.service.read_file(path)
            assert content == "test content"
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_write_file(self):
        """Write file creates/updates content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            path = f.name

        try:
            await self.service.write_file(path, "new content")
            content = await self.service.read_file(path)
            assert content == "new content"
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_read_large_file_raises(self):
        """Reading file over size limit raises ValueError."""
        # Create a file larger than MAX_FILE_SIZE
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Write more than 500KB
            f.write("x" * (FileService.MAX_FILE_SIZE + 1000))
            path = f.name

        try:
            with pytest.raises(ValueError, match="too large"):
                await self.service.read_file(path)
        finally:
            os.unlink(path)


class TestFileIcons:
    """Tests for file icon mapping."""

    def test_python_icon(self):
        """Python files get code icon."""
        icon = get_file_icon("test.py")
        assert icon is not None

    def test_folder_icon(self):
        """Folders get folder icon."""
        icon = get_file_icon("folder", is_dir=True)
        assert icon == FOLDER_ICON

    def test_expanded_folder_icon(self):
        """Expanded folders get different icon."""
        icon = get_file_icon("folder", is_dir=True, is_expanded=True)
        assert icon == FOLDER_OPEN_ICON
        assert icon != FOLDER_ICON

    def test_unknown_extension_gets_default(self):
        """Unknown extensions get default file icon."""
        icon = get_file_icon("file.xyz123abc")
        assert icon is not None

    def test_common_extensions_mapped(self):
        """Common file types are mapped."""
        test_cases = [".py", ".js", ".json", ".md", ".html", ".css"]
        for ext in test_cases:
            icon = get_file_icon(f"file{ext}")
            assert icon is not None, f"No icon for {ext}"
