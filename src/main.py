"""
Skynette - Main Entry Point

This is the entry point for the Skynette application.
Run with: python src/main.py or flet run src/main.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import flet as ft
from src.ui.app import SkynetteApp


def main(page: ft.Page):
    """Main entry point for Flet application."""
    app = SkynetteApp(page)
    app.initialize()


if __name__ == "__main__":
    ft.run(main)
