"""Test that core modules can be imported successfully."""

import pytest


def test_main_module_imports():
    """Test that main module can be imported."""
    try:
        import src.main
        assert src.main is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src.main: {e}")


def test_ui_module_structure():
    """Test that UI module structure exists."""
    import src.ui
    assert hasattr(src.ui, '__file__'), "UI module should exist"


def test_data_module_structure():
    """Test that data module structure exists."""
    import src.data
    assert hasattr(src.data, '__file__'), "Data module should exist"


def test_cli_module_imports():
    """Test that CLI module can be imported."""
    try:
        import src.cli
        assert src.cli is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src.cli: {e}")
