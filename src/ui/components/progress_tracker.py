"""Progress tracker component for upload operations."""

import flet as ft

from src.ui.models.knowledge_bases import UploadProgress
from src.ui.theme import Theme


class ProgressTracker(ft.Column):
    """Displays upload/processing progress."""

    def __init__(self):
        super().__init__()
        self.visible = False
        self.spacing = 8

        # Progress bar
        self.overall_progress = ft.ProgressBar(width=500, value=0)

        # Current file text
        self.current_file_text = ft.Text("", size=14)

        # File status list (recent 5 files)
        self.file_status_list = ft.Column(spacing=4)

        # Error summary
        self.error_summary = ft.Column(spacing=4)

        self.controls = [
            ft.Text("Upload Progress", weight=ft.FontWeight.BOLD),
            self.overall_progress,
            self.current_file_text,
            ft.Container(height=8),
            ft.Text("Recent Files:", size=12, color=Theme.TEXT_SECONDARY),
            self.file_status_list,
            self.error_summary,
        ]

    def update_progress(self, progress: UploadProgress):
        """Update progress display."""
        self.visible = True

        # Overall progress
        self.overall_progress.value = progress.percentage / 100

        # Current file
        if progress.status == "processing" and progress.current_file:
            self.current_file_text.value = (
                f"Processing {progress.current_file} "
                f"({progress.processed_files}/{progress.total_files})..."
            )
        elif progress.status == "completed":
            self.current_file_text.value = (
                f"Completed: {progress.processed_files}/{progress.total_files} files"
            )
        else:
            self.current_file_text.value = ""

        # File status list (not implemented in this basic version)
        # Would show last 5 files with ✅/⏳/❌ icons

        # Error summary
        if progress.errors:
            self.error_summary.controls = [
                ft.Container(height=8),
                ft.Text(
                    f"⚠️ {len(progress.errors)} file(s) failed:",
                    color=Theme.ERROR,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            f"  • {error.file_path}: {error.error_message}",
                            size=12,
                            color=Theme.ERROR,
                        )
                        for error in progress.errors[:5]  # Show first 5
                    ],
                    spacing=2,
                ),
            ]
            if len(progress.errors) > 5:
                self.error_summary.controls.append(
                    ft.Text(
                        f"  ... and {len(progress.errors) - 5} more",
                        size=12,
                        italic=True,
                        color=Theme.TEXT_SECONDARY,
                    )
                )
        else:
            self.error_summary.controls = []

        try:
            if self.page:
                self.page.update()
        except RuntimeError:
            # Control not added to page yet (e.g., in tests)
            pass
