"""Collection creation/editing dialog."""

import flet as ft
import re
from typing import Optional, Callable, Awaitable
from src.ui.theme import Theme
from src.rag.service import RAGService


class CollectionDialog(ft.AlertDialog):
    """Dialog for creating or editing a collection."""

    def __init__(
        self,
        rag_service: RAGService,
        collection_id: Optional[str] = None,
        on_save: Optional[Callable[[], Awaitable[None]]] = None,
    ):
        super().__init__()
        self.rag_service = rag_service
        self.collection_id = collection_id
        self.on_save = on_save
        self.is_edit = collection_id is not None

        # Form fields
        self.name_field = ft.TextField(
            label="Name",
            hint_text="e.g., ProjectDocs",
            autofocus=True,
        )

        self.description_field = ft.TextField(
            label="Description (optional)",
            hint_text="What documents are in this collection?",
            multiline=True,
            min_lines=2,
            max_lines=4,
        )

        # Embedding model selection
        self.embedding_radio = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(
                    value="local",
                    label="Local (all-MiniLM-L6-v2) - Free, private",
                ),
                ft.Radio(
                    value="openai",
                    label="OpenAI (text-embedding-3-small) - Higher quality",
                ),
                ft.Radio(
                    value="cohere",
                    label="Cohere (embed-english-v3.0) - Alternative",
                ),
            ]),
            value="local",
        )

        # Chunking settings
        self.chunk_size_field = ft.TextField(
            label="Chunk size (tokens)",
            value="1024",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.chunk_overlap_field = ft.TextField(
            label="Overlap (tokens)",
            value="128",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.max_chunk_field = ft.TextField(
            label="Max chunk size (tokens)",
            value="2048",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Build dialog
        self.modal = True
        self.title = ft.Text(
            "New Collection" if not self.is_edit else "Edit Collection"
        )

        self.content = ft.Column(
            controls=[
                ft.Text("Basic Information", weight=ft.FontWeight.BOLD),
                self.name_field,
                self.description_field,
                ft.Container(height=16),
                ft.Text("Embedding Model", weight=ft.FontWeight.BOLD),
                self.embedding_radio,
                ft.Container(height=16),
                ft.Text("Chunking Settings", weight=ft.FontWeight.BOLD),
                self.chunk_size_field,
                self.chunk_overlap_field,
                self.max_chunk_field,
            ],
            width=500,
            height=600,
            scroll=ft.ScrollMode.AUTO,
        )

        self.actions = [
            ft.TextButton("Cancel", on_click=self._on_cancel),
            ft.Button("Save", on_click=self._on_save_click),
        ]

    def _validate_name(self, name: str) -> bool:
        """Validate collection name."""
        if not name:
            return False
        # Must have at least one letter
        if not re.search(r'[a-zA-Z]', name):
            return False
        # Only alphanumeric and underscores
        return bool(re.match(r'^[a-zA-Z0-9_]+$', name))

    def _validate_chunk_size(self, size: int) -> bool:
        """Validate chunk size."""
        return 256 <= size <= 4096

    def _validate_fields(self) -> dict:
        """Validate all fields, return dict of errors."""
        errors = {}

        # Name validation
        if not self._validate_name(self.name_field.value):
            errors['name'] = "Name must be alphanumeric and underscores only"

        # Chunk size validation
        try:
            chunk_size = int(self.chunk_size_field.value)
            if not self._validate_chunk_size(chunk_size):
                errors['chunk_size'] = "Must be 256-4096"
        except ValueError:
            errors['chunk_size'] = "Must be a number"

        # Overlap validation
        try:
            overlap = int(self.chunk_overlap_field.value)
            chunk_size = int(self.chunk_size_field.value)
            if overlap >= chunk_size:
                errors['chunk_overlap'] = "Must be less than chunk size"
            if overlap < 0:
                errors['chunk_overlap'] = "Must be non-negative"
        except ValueError:
            errors['chunk_overlap'] = "Must be a number"

        # Max chunk validation
        try:
            max_chunk = int(self.max_chunk_field.value)
            chunk_size = int(self.chunk_size_field.value)
            if max_chunk < chunk_size:
                errors['max_chunk'] = "Must be >= chunk size"
        except ValueError:
            errors['max_chunk'] = "Must be a number"

        return errors

    async def _on_save_click(self, e):
        """Handle Save button click."""
        # Clear previous errors
        self.name_field.error_text = None
        self.chunk_size_field.error_text = None
        self.chunk_overlap_field.error_text = None
        self.max_chunk_field.error_text = None

        # Validate
        errors = self._validate_fields()
        if errors:
            # Show errors on fields
            self.name_field.error_text = errors.get('name')
            self.chunk_size_field.error_text = errors.get('chunk_size')
            self.chunk_overlap_field.error_text = errors.get('chunk_overlap')
            self.max_chunk_field.error_text = errors.get('max_chunk')
            if self.page:
                self.page.update()
            return

        # Create or update collection
        try:
            if self.is_edit:
                # TODO: Implement update in RAGService
                pass
            else:
                collection = await self.rag_service.create_collection(
                    name=self.name_field.value,
                    description=self.description_field.value,
                    embedding_model=self.embedding_radio.value,
                    chunk_size=int(self.chunk_size_field.value),
                    chunk_overlap=int(self.chunk_overlap_field.value),
                    max_chunk_size=int(self.max_chunk_field.value),
                )

            # Close dialog
            self.open = False
            if self.page:
                self.page.update()

            # Callback
            if self.on_save:
                await self.on_save()

        except Exception as ex:
            # Show error
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Error: {str(ex)}"),
                        bgcolor=ft.colors.ERROR,
                    )
                )

    def _on_cancel(self, e):
        """Handle Cancel button click."""
        self.open = False
        if self.page:
            self.page.update()
