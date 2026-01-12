"""Upload dialog for adding documents to RAG collections."""

import flet as ft
import asyncio
from pathlib import Path
from typing import Optional, Callable, Awaitable
from src.ui.theme import Theme
from src.rag.service import RAGService
from src.ui.components.progress_tracker import ProgressTracker
from src.ui.models.knowledge_bases import UploadProgress, UploadError


class UploadDialog(ft.AlertDialog):
    """Dialog for uploading documents to a collection."""

    def __init__(
        self,
        rag_service: RAGService,
        collection_id: str,
        page: ft.Page,
        on_complete: Optional[Callable[[], Awaitable[None]]] = None,
    ):
        super().__init__()
        self.rag_service = rag_service
        self.collection_id = collection_id
        self._page_ref = page
        self.on_complete = on_complete
        self.selected_files = []
        self.upload_progress = None

        # File picker
        self.file_picker = ft.FilePicker()
        self.file_picker.on_result = self._on_file_picker_result
        # Add file picker to page overlay
        if self._page_ref:
            self._page_ref.overlay.append(self.file_picker)

        # Selected files list
        self.files_list = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.AUTO,
            height=300,
        )

        # Progress tracker
        self.progress_tracker = ProgressTracker()

        # Build tabs (simple version - just file picker for now)
        self.upload_tabs = ft.Column(
            controls=[
                self._build_file_picker_header(),
                self.files_list,
            ],
            spacing=16,
        )

        # Build dialog
        self.modal = True
        self.title = ft.Text("Add Documents")

        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    self.upload_tabs,
                    ft.Container(height=16),
                    self.progress_tracker,
                ],
                spacing=0,
            ),
            width=600,
            height=500,
            padding=16,
        )

        self.actions = [
            ft.TextButton("Cancel", on_click=self._on_cancel),
            ft.Button(
                "Upload",
                on_click=self._on_start_upload,
                disabled=True,
            ),
        ]

        # Upload button reference
        self.upload_button = self.actions[1]

    def _build_file_picker_header(self) -> ft.Column:
        """Build file picker header with browse button."""
        return ft.Column(
            controls=[
                ft.Text(
                    "Select .md or .txt files to upload",
                    size=14,
                    color=Theme.TEXT_SECONDARY,
                ),
                ft.Container(height=8),
                ft.Button(
                    "Browse Files",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=self._on_browse_files,
                ),
                ft.Container(height=8),
                ft.Text("Selected Files:", weight=ft.FontWeight.BOLD),
            ],
            spacing=0,
        )

    def _on_browse_files(self, e):
        """Open file picker."""
        self.file_picker.pick_files(
            allowed_extensions=["md", "txt"],
            allow_multiple=True,
            dialog_title="Select Documents",
        )

    def _on_file_picker_result(self, e: ft.FilePickerResultEvent):
        """Handle file picker result."""
        if e.files:
            # Add selected files
            for file in e.files:
                file_path = file.path
                if file_path not in [f["path"] for f in self.selected_files]:
                    self.selected_files.append({
                        "path": file_path,
                        "name": file.name,
                        "size": file.size,
                    })

            # Update UI
            self._update_files_list()

            # Enable upload button if files selected
            self.upload_button.disabled = len(self.selected_files) == 0
            if self._page_ref:
                self._page_ref.update()

    def _update_files_list(self):
        """Update the files list display."""
        self.files_list.controls.clear()

        if not self.selected_files:
            self.files_list.controls.append(
                ft.Text(
                    "No files selected",
                    size=14,
                    color=Theme.TEXT_SECONDARY,
                    italic=True,
                )
            )
        else:
            for idx, file_info in enumerate(self.selected_files):
                self.files_list.controls.append(
                    self._build_file_item(idx, file_info)
                )

        if self._page_ref:
            self._page_ref.update()

    def _build_file_item(self, idx: int, file_info: dict) -> ft.Container:
        """Build a file list item."""
        # Format file size
        size_kb = file_info["size"] / 1024
        if size_kb < 1024:
            size_str = f"{size_kb:.1f} KB"
        else:
            size_mb = size_kb / 1024
            size_str = f"{size_mb:.1f} MB"

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.DESCRIPTION,
                        size=20,
                        color=Theme.PRIMARY,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                file_info["name"],
                                weight=ft.FontWeight.W_500,
                                size=14,
                            ),
                            ft.Text(
                                size_str,
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=16,
                        tooltip="Remove",
                        on_click=lambda e, i=idx: self._on_remove_file(i),
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=8,
            border=ft.border.all(1, Theme.BORDER),
            border_radius=8,
            margin=ft.margin.only(bottom=8),
        )

    def _on_remove_file(self, idx: int):
        """Remove file from selection."""
        if 0 <= idx < len(self.selected_files):
            self.selected_files.pop(idx)
            self._update_files_list()

            # Disable upload button if no files
            self.upload_button.disabled = len(self.selected_files) == 0
            if self._page_ref:
                self._page_ref.update()

    async def _on_start_upload(self, e):
        """Handle upload button click."""
        if not self.selected_files:
            return

        self.upload_progress = UploadProgress(
            total_files=len(self.selected_files),
            processed_files=0,
            current_file="",
            status="processing",
            errors=[],
        )

        # Show progress
        self.progress_tracker.update_progress(self.upload_progress)

        # Disable upload button
        self.upload_button.disabled = True
        if self._page_ref:
            self._page_ref.update()

        # Process files with concurrency limit
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent
        upload_lock = asyncio.Lock()  # Thread-safe error collection

        async def process_file(file_info: dict):
            async with semaphore:
                self.upload_progress.current_file = file_info["name"]
                self.progress_tracker.update_progress(self.upload_progress)

                try:
                    # Ingest document
                    await self.rag_service.ingest_document(
                        file_path=file_info["path"],
                        collection_id=self.collection_id,
                    )

                except Exception as ex:
                    # Thread-safe error collection
                    async with upload_lock:
                        self.upload_progress.errors.append(
                            UploadError(
                                file_path=file_info["path"],
                                error_message=str(ex),
                                error_type=self._classify_error(ex),
                            )
                        )
                finally:
                    # Count ALL files (success and error) - moved from try block
                    self.upload_progress.processed_files += 1
                    self.progress_tracker.update_progress(self.upload_progress)

        # Process all files in parallel
        await asyncio.gather(*[process_file(f) for f in self.selected_files])

        # Mark completed
        self.upload_progress.status = "completed"
        self.progress_tracker.update_progress(self.upload_progress)

        # Show summary
        self._show_completion_summary()

    def _classify_error(self, ex: Exception) -> str:
        """Classify error type."""
        error_str = str(ex).lower()
        if "unsupported" in error_str or "pdf" in error_str:
            return "unsupported"
        elif "permission" in error_str or "not found" in error_str:
            return "permission"
        elif "corrupt" in error_str or "parse" in error_str:
            return "corrupted"
        else:
            return "embedding_failed"

    def _show_completion_summary(self):
        """Show completion message."""
        success_count = self.upload_progress.processed_files - len(self.upload_progress.errors)
        error_count = len(self.upload_progress.errors)

        if self._page_ref:
            self._page_ref.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(
                        f"Upload complete: {success_count} succeeded, {error_count} failed"
                    ),
                    bgcolor=Theme.SUCCESS if error_count == 0 else Theme.WARNING,
                )
            )

        # Callback
        if self.on_complete:
            asyncio.create_task(self.on_complete())

    def _on_cancel(self, e):
        """Handle Cancel button click."""
        self.open = False
        if self._page_ref:
            self._page_ref.update()
