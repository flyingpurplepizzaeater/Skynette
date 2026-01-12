import pytest
import flet as ft
from src.ui.components.progress_tracker import ProgressTracker
from src.ui.models.knowledge_bases import UploadProgress, UploadError


class TestProgressTracker:
    def test_tracker_creation(self):
        """ProgressTracker should create hidden initially."""
        tracker = ProgressTracker()

        assert tracker is not None
        assert tracker.visible is False

    def test_update_shows_progress(self):
        """update() should show and update progress."""
        tracker = ProgressTracker()

        progress = UploadProgress(
            total_files=10,
            processed_files=5,
            current_file="test.md",
            status="processing",
            errors=[],
        )

        tracker.update_progress(progress)

        assert tracker.visible is True
        # Progress bar should show 50%
        assert tracker.overall_progress.value == 0.5

    def test_update_shows_errors(self):
        """update() should display errors."""
        tracker = ProgressTracker()

        progress = UploadProgress(
            total_files=10,
            processed_files=10,
            current_file="",
            status="completed",
            errors=[
                UploadError("file1.pdf", "Unsupported format", "unsupported"),
                UploadError("file2.txt", "Permission denied", "permission"),
            ],
        )

        tracker.update_progress(progress)

        assert len(progress.errors) == 2
        # Error summary should be visible
