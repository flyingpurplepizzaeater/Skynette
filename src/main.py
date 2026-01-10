"""
Skynette - Main Entry Point

This is the entry point for the Skynette application.
Run with: python src/main.py or flet run src/main.py
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import flet as ft
from src.ui.app import SkynetteApp

# Test mode configuration
TEST_MODE = os.environ.get("SKYNETTE_TEST_MODE", "").lower() == "true"
MOCK_AI = os.environ.get("SKYNETTE_MOCK_AI", "").lower() == "true"
DATA_DIR = os.environ.get("SKYNETTE_DATA_DIR", None)


def configure_test_mode():
    """Configure the application for test mode."""
    if not TEST_MODE:
        return

    # Override data directory if specified
    if DATA_DIR:
        from src.data import storage
        storage._storage = storage.WorkflowStorage(data_dir=DATA_DIR)

    # Use mock AI providers if requested
    if MOCK_AI:
        from src.ai import providers
        # The mock providers will be registered when running in test mode
        # Tests can inject their own mock providers as needed
        pass


def main(page: ft.Page):
    """Main entry point for Flet application."""
    # Configure test mode before initializing the app
    configure_test_mode()

    app = SkynetteApp(page)
    app.initialize()


if __name__ == "__main__":
    ft.run(main)
