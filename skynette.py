"""
Skynette - Main Entry Point

This is the root entry point for the Skynette application.
Run with: python main.py
"""

import sys
import os
import traceback
import logging
from pathlib import Path
from datetime import datetime

# Setup logging first - before any other imports
def setup_logging():
    """Setup logging to file for debugging frozen apps."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_dir = Path(sys.executable).parent
    else:
        # Running from source
        app_dir = Path(__file__).parent

    log_dir = app_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"skynette_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()
logger.info("=" * 50)
logger.info("Skynette starting...")
logger.info(f"Python version: {sys.version}")
logger.info(f"Executable: {sys.executable}")
logger.info(f"Frozen: {getattr(sys, 'frozen', False)}")

try:
    # Add project root and src to path for imports
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        PROJECT_ROOT = Path(sys.executable).parent
    else:
        # Running from source
        PROJECT_ROOT = Path(__file__).parent

    SRC_ROOT = PROJECT_ROOT / "src"

    logger.info(f"PROJECT_ROOT: {PROJECT_ROOT}")
    logger.info(f"SRC_ROOT: {SRC_ROOT}")

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))

    logger.info("Importing flet...")
    import flet as ft
    logger.info("Flet imported successfully")

    logger.info("Importing SkynetteApp...")
    from src.ui.app import SkynetteApp
    logger.info("SkynetteApp imported successfully")

except Exception as e:
    logger.error(f"Error during imports: {e}")
    logger.error(traceback.format_exc())
    raise


def main(page: ft.Page):
    """Main entry point for Flet application."""
    try:
        logger.info("Creating SkynetteApp instance...")
        app = SkynetteApp(page)
        logger.info("Initializing app...")
        app.initialize()
        logger.info("App initialized successfully!")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    try:
        logger.info("Starting Flet app...")

        # Support web mode for automated testing (Selenium/Playwright)
        if "--web-test" in sys.argv:
            port = 8550
            logger.info(f"Starting in web test mode on port {port}...")
            ft.run(main, view=ft.AppView.WEB_BROWSER, port=port)
        elif "--web" in sys.argv:
            port = 8550
            logger.info(f"Starting in web mode on port {port}...")
            ft.run(main, view=ft.AppView.WEB_BROWSER, port=port)
        else:
            ft.run(main)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())

        # Show error dialog on Windows
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Skynette failed to start:\n\n{str(e)}\n\nCheck logs folder for details.",
                "Skynette Error",
                0x10  # MB_ICONERROR
            )
        raise
