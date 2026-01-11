"""
Skynette Auto-Updater

Checks for updates from GitHub releases and applies them.
"""

import asyncio
import json
import os
import sys
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass

import httpx


@dataclass
class UpdateInfo:
    """Information about an available update."""
    version: str
    current_version: str
    download_url: str
    release_notes: str
    published_at: str
    size_bytes: int
    is_newer: bool


class Updater:
    """
    Handles checking for and applying updates from GitHub releases.
    """

    GITHUB_REPO = "skynette/skynette"  # Change to actual repo
    CURRENT_VERSION = "1.0.0"
    RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    def __init__(self, on_progress: Optional[Callable[[str, float], None]] = None):
        """
        Initialize updater.

        Args:
            on_progress: Callback for progress updates (message, percent)
        """
        self.on_progress = on_progress or (lambda msg, pct: None)
        self._update_info: Optional[UpdateInfo] = None

    def _report_progress(self, message: str, percent: float = 0):
        """Report progress to callback."""
        self.on_progress(message, percent)

    @staticmethod
    def _parse_version(version: str) -> tuple:
        """Parse version string into comparable tuple."""
        # Remove 'v' prefix if present
        version = version.lstrip('v')
        parts = version.split('.')
        result = []
        for part in parts:
            # Handle versions like 1.0.0-beta
            num = ''.join(c for c in part if c.isdigit())
            result.append(int(num) if num else 0)
        return tuple(result)

    def _is_newer_version(self, remote_version: str) -> bool:
        """Check if remote version is newer than current."""
        try:
            remote = self._parse_version(remote_version)
            current = self._parse_version(self.CURRENT_VERSION)
            return remote > current
        except Exception:
            return False

    async def check_for_updates(self) -> Optional[UpdateInfo]:
        """
        Check GitHub for available updates.

        Returns:
            UpdateInfo if update available, None otherwise
        """
        self._report_progress("Checking for updates...", 0)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.RELEASES_URL,
                    headers={"Accept": "application/vnd.github+json"},
                    timeout=30
                )

                if response.status_code != 200:
                    self._report_progress("Could not check for updates", 100)
                    return None

                data = response.json()

                version = data.get("tag_name", "").lstrip('v')
                is_newer = self._is_newer_version(version)

                # Find appropriate asset for this platform
                download_url = ""
                size_bytes = 0
                platform_name = self._get_platform_asset_name()

                for asset in data.get("assets", []):
                    if platform_name in asset.get("name", "").lower():
                        download_url = asset.get("browser_download_url", "")
                        size_bytes = asset.get("size", 0)
                        break

                # Fallback to source zip if no platform-specific asset
                if not download_url:
                    download_url = data.get("zipball_url", "")

                self._update_info = UpdateInfo(
                    version=version,
                    current_version=self.CURRENT_VERSION,
                    download_url=download_url,
                    release_notes=data.get("body", ""),
                    published_at=data.get("published_at", ""),
                    size_bytes=size_bytes,
                    is_newer=is_newer,
                )

                if is_newer:
                    self._report_progress(f"Update available: v{version}", 100)
                else:
                    self._report_progress("You're up to date!", 100)

                return self._update_info

        except Exception as e:
            self._report_progress(f"Update check failed: {e}", 100)
            return None

    def _get_platform_asset_name(self) -> str:
        """Get the expected asset name for current platform."""
        if sys.platform == "win32":
            return "windows"
        elif sys.platform == "darwin":
            return "macos"
        else:
            return "linux"

    async def download_update(self, url: Optional[str] = None) -> Optional[Path]:
        """
        Download update package.

        Args:
            url: Download URL (uses cached update info if not provided)

        Returns:
            Path to downloaded file, or None on failure
        """
        download_url = url or (self._update_info.download_url if self._update_info else None)

        if not download_url:
            self._report_progress("No download URL available", 100)
            return None

        self._report_progress("Downloading update...", 0)

        try:
            # Create temp directory for download
            temp_dir = Path(tempfile.mkdtemp(prefix="skynette_update_"))
            download_path = temp_dir / "update.zip"

            async with httpx.AsyncClient(follow_redirects=True) as client:
                async with client.stream("GET", download_url, timeout=300) as response:
                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0

                    with open(download_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)

                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                self._report_progress(
                                    f"Downloading: {downloaded // 1024 // 1024}MB / {total_size // 1024 // 1024}MB",
                                    percent
                                )

            self._report_progress("Download complete!", 100)
            return download_path

        except Exception as e:
            self._report_progress(f"Download failed: {e}", 100)
            return None

    async def apply_update(self, update_path: Path) -> bool:
        """
        Apply downloaded update.

        Args:
            update_path: Path to downloaded update archive

        Returns:
            True if update was applied successfully
        """
        self._report_progress("Preparing update...", 0)

        try:
            # Get application directory
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                app_dir = Path(sys.executable).parent
            else:
                # Running from source
                app_dir = Path(__file__).parent.parent

            # Create backup
            backup_dir = app_dir.parent / f"skynette_backup_{self.CURRENT_VERSION}"
            self._report_progress("Creating backup...", 10)

            if backup_dir.exists():
                shutil.rmtree(backup_dir)

            # Don't backup in development mode
            if getattr(sys, 'frozen', False):
                shutil.copytree(app_dir, backup_dir)

            # Extract update
            self._report_progress("Extracting update...", 30)
            extract_dir = update_path.parent / "extracted"
            extract_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(update_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # Find the actual content directory (GitHub zips have a root folder)
            contents = list(extract_dir.iterdir())
            if len(contents) == 1 and contents[0].is_dir():
                source_dir = contents[0]
            else:
                source_dir = extract_dir

            # Apply update based on what was downloaded
            self._report_progress("Applying update...", 60)

            if (source_dir / "Skynette.exe").exists():
                # Executable update
                new_exe = source_dir / "Skynette.exe"
                old_exe = app_dir / "Skynette.exe"
                old_exe_backup = app_dir / "Skynette.exe.old"

                if old_exe.exists():
                    old_exe.rename(old_exe_backup)

                shutil.copy(new_exe, old_exe)

            elif (source_dir / "src").exists():
                # Source update
                for item in source_dir.iterdir():
                    dest = app_dir / item.name
                    if item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy(item, dest)

            # Clean up
            self._report_progress("Cleaning up...", 90)
            shutil.rmtree(update_path.parent)

            self._report_progress("Update complete! Please restart.", 100)
            return True

        except Exception as e:
            self._report_progress(f"Update failed: {e}", 100)
            return False

    async def update(self) -> bool:
        """
        Full update process: check, download, and apply.

        Returns:
            True if update was successful
        """
        # Check for updates
        update_info = await self.check_for_updates()

        if not update_info or not update_info.is_newer:
            return False

        # Download
        update_path = await self.download_update()
        if not update_path:
            return False

        # Apply
        return await self.apply_update(update_path)


class UpdateDialog:
    """
    Flet-based update dialog UI component.
    """

    def __init__(self, page):
        import flet as ft
        self.page = page
        self.ft = ft
        self.updater = Updater(on_progress=self._on_progress)
        self.progress_text = ft.Text("", size=14)
        self.progress_bar = ft.ProgressBar(width=400, value=0)
        self.update_button = ft.Button(
            "Check for Updates",
            icon=ft.Icons.REFRESH,
            on_click=self._check_updates
        )
        self.download_button = ft.Button(
            "Download & Install",
            icon=ft.Icons.DOWNLOAD,
            on_click=self._download_update,
            visible=False,
        )
        self.release_notes = ft.Text("", size=12, selectable=True)
        self._update_info = None

    def _on_progress(self, message: str, percent: float):
        """Update progress display."""
        self.progress_text.value = message
        self.progress_bar.value = percent / 100
        self.page.update()

    async def _check_updates(self, e):
        """Handle check updates button click."""
        self.update_button.disabled = True
        self.page.update()

        self._update_info = await self.updater.check_for_updates()

        if self._update_info and self._update_info.is_newer:
            self.download_button.visible = True
            self.release_notes.value = f"Version {self._update_info.version}\n\n{self._update_info.release_notes[:500]}..."
        else:
            self.release_notes.value = "You're running the latest version!"

        self.update_button.disabled = False
        self.page.update()

    async def _download_update(self, e):
        """Handle download button click."""
        self.download_button.disabled = True
        self.update_button.disabled = True
        self.page.update()

        success = await self.updater.update()

        if success:
            # Show restart dialog
            def restart_app(e):
                import subprocess
                subprocess.Popen([sys.executable] + sys.argv)
                self.page.window.close()

            def close_dialog(e):
                dialog.open = False
                self.page.update()

            dialog = self.ft.AlertDialog(
                title=self.ft.Text("Update Complete"),
                content=self.ft.Text("Skynette has been updated. Restart now?"),
                actions=[
                    self.ft.TextButton("Later", on_click=close_dialog),
                    self.ft.Button("Restart Now", on_click=restart_app),
                ],
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

        self.download_button.disabled = False
        self.update_button.disabled = False
        self.page.update()

    def build(self):
        """Build the update dialog content."""
        return self.ft.Column(
            [
                self.ft.Text("Software Updates", size=20, weight=self.ft.FontWeight.BOLD),
                self.ft.Divider(),
                self.ft.Row([
                    self.update_button,
                    self.download_button,
                ]),
                self.progress_bar,
                self.progress_text,
                self.ft.Container(height=20),
                self.release_notes,
            ],
            spacing=10,
            width=450,
        )


# CLI interface for updates
async def main():
    """CLI update check."""
    def progress(msg, pct):
        print(f"[{pct:3.0f}%] {msg}")

    updater = Updater(on_progress=progress)

    print("Checking for updates...")
    update_info = await updater.check_for_updates()

    if update_info and update_info.is_newer:
        print(f"\nNew version available: v{update_info.version}")
        print(f"Current version: v{update_info.current_version}")
        print(f"\nRelease notes:\n{update_info.release_notes[:500]}")

        response = input("\nDownload and install? (y/n): ")
        if response.lower() == 'y':
            success = await updater.update()
            if success:
                print("\nUpdate complete! Please restart the application.")
            else:
                print("\nUpdate failed.")
    else:
        print("You're running the latest version!")


if __name__ == "__main__":
    asyncio.run(main())
