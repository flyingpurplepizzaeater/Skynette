"""Upload dialog for adding documents to RAG collections."""

import flet as ft
from pathlib import Path
from typing import Optional, Callable, Awaitable
from src.ui.theme import Theme
from src.rag.service import RAGService


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
            content=self.upload_tabs,
            width=600,
            height=500,
            padding=16,
        )

        self.actions = [
            ft.TextButton("Cancel", on_click=self._on_cancel),
            ft.Button(
                "Upload",
                on_click=self._on_upload,
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

    async def _on_upload(self, e):
        """Handle Upload button click."""
        if not self.selected_files:
            return

        # Show progress
        progress_bar = ft.ProgressBar()
        self.content.content = ft.Column(
            controls=[
                ft.Text("Uploading documents...", size=16),
                ft.Container(height=16),
                progress_bar,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.upload_button.disabled = True
        if self._page_ref:
            self._page_ref.update()

        # Upload each file
        success_count = 0
        errors = []

        for file_info in self.selected_files:
            try:
                result = await self.rag_service.ingest_document(
                    file_path=file_info["path"],
                    collection_id=self.collection_id,
                )

                if result["status"] == "success":
                    success_count += 1
                else:
                    errors.append(f"{file_info['name']}: {result.get('error', 'Unknown error')}")
            except Exception as ex:
                errors.append(f"{file_info['name']}: {str(ex)}")

        # Show result
        if errors:
            error_text = "\n".join(errors)
            if self._page_ref:
                self._page_ref.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Uploaded {success_count} files. Errors:\n{error_text}"),
                        bgcolor=red if success_count == 0 else orange,
                    )
                )
        else:
            if self._page_ref:
                self._page_ref.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Successfully uploaded {success_count} files"),
                        bgcolor=green,
                    )
                )

        # Close dialog
        self.open = False
        if self._page_ref:
            self._page_ref.update()

        # Callback
        if self.on_complete:
            await self.on_complete()

    def _on_cancel(self, e):
        """Handle Cancel button click."""
        self.open = False
        if self._page_ref:
            self._page_ref.update()
