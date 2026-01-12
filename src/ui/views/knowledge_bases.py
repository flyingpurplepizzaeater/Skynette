"""Knowledge Bases view for RAG collection management."""

import asyncio
import flet as ft
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from src.ui.theme import Theme
from src.ui.models.knowledge_bases import CollectionCardData
from src.ui.components.collection_card import CollectionCard
from src.ui.dialogs.collection_dialog import CollectionDialog
from src.ui.dialogs.query_dialog import QueryDialog
from src.rag.service import RAGService


class KnowledgeBasesView(ft.Column):
    """Main view for Knowledge Bases tab in AI Hub."""

    def __init__(self, page: ft.Page = None, rag_service: Optional[RAGService] = None):
        super().__init__()
        self._page = page
        self.expand = True
        self.spacing = Theme.SPACING_MD

        # State
        self.rag_service = rag_service
        self.collections: List[CollectionCardData] = []

        # Cache
        self.collections_cache: Optional[List[CollectionCardData]] = None
        self.cache_timestamp: Optional[datetime] = None
        self.cache_ttl_seconds = 60  # 1 minute cache

    def build(self):
        """Build the view."""
        return ft.Column(
            controls=[
                self._build_header(),
                self._build_collections_grid(),
            ],
            expand=True,
            spacing=self.spacing,
        )

    def did_mount(self):
        """Called when view is mounted."""
        # Load collections on first mount
        if not self.collections_cache:
            asyncio.create_task(self._load_collections())

    def _build_header(self):
        """Build header with title and New Collection button."""
        return ft.Row(
            controls=[
                ft.Text(
                    "Knowledge Bases",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=Theme.TEXT_PRIMARY,
                ),
                ft.Container(expand=True),
                ft.Button(
                    "New Collection",
                    icon=ft.Icons.ADD,
                    on_click=self._on_new_collection,
                ),
            ],
        )

    def _build_collections_grid(self):
        """Build collections grid or empty state."""
        if not self.collections:
            return self._build_empty_state()

        # Grid: 3 cards per row
        rows = []
        for i in range(0, len(self.collections), 3):
            row_collections = self.collections[i:i+3]
            rows.append(
                ft.Row(
                    controls=[
                        CollectionCard(
                            data=coll,
                            on_query=self._on_query_collection,
                            on_manage=self._on_manage_collection,
                        )
                        for coll in row_collections
                    ],
                    spacing=16,
                    wrap=True,
                )
            )

        return ft.Column(
            controls=rows,
            spacing=16,
        )

    def _build_empty_state(self):
        """Build empty state when no collections exist."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=Theme.TEXT_SECONDARY),
                    ft.Text(
                        "No Knowledge Bases Yet",
                        size=24,
                        weight=ft.FontWeight.W_500,
                        color=Theme.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Create a collection to start indexing documents",
                        size=14,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Container(height=Theme.SPACING_MD),
                    ft.Button(
                        "Create Your First Collection",
                        icon=ft.Icons.ADD,
                        on_click=self._on_new_collection,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Theme.SPACING_SM,
            ),
            alignment=ft.alignment.Alignment(0, 0),
            expand=True,
        )

    def _on_new_collection(self, e):
        """Handle New Collection button click."""
        dialog = CollectionDialog(
            rag_service=self.rag_service,
            collection_id=None,
            on_save=self._on_collection_saved,
        )
        if self._page:
            self._page.dialog = dialog
            dialog.open = True
            self._page.update()

    def _on_query_collection(self, collection_id: str):
        """Handle Query button click."""
        # Find collection
        collection = next((c for c in self.collections if c.id == collection_id), None)
        if not collection:
            return

        dialog = QueryDialog(
            rag_service=self.rag_service,
            collection_id=collection_id,
            collection_name=collection.name,
        )
        if self._page:
            self._page.dialog = dialog
            dialog.open = True
            self._page.update()

    def _on_manage_collection(self, collection_id: str):
        """Handle Manage button click."""
        dialog = CollectionDialog(
            rag_service=self.rag_service,
            collection_id=collection_id,
            on_save=self._on_collection_saved,
        )
        if self._page:
            self._page.dialog = dialog
            dialog.open = True
            self._page.update()

    async def _on_collection_saved(self):
        """Handle collection save callback."""
        self._invalidate_cache()
        await self._load_collections()

    async def _load_collections(self):
        """Load collections from backend with caching and error handling."""
        # Check cache
        if self.collections_cache is not None and self.cache_timestamp:
            age = (datetime.now(timezone.utc) - self.cache_timestamp).total_seconds()
            if age < self.cache_ttl_seconds:
                # Use cache
                self.collections = self.collections_cache
                self._rebuild_ui()
                return

        try:
            # Fetch from backend
            collections = await self.rag_service.list_collections()

            # Convert to CollectionCardData with stats
            self.collections = []
            for collection in collections:
                stats = await self.rag_service.get_collection_stats(collection.id)

                card_data = CollectionCardData(
                    id=collection.id,
                    name=collection.name,
                    description=collection.description or "",
                    document_count=stats.get("document_count", 0),
                    chunk_count=stats.get("chunk_count", 0),
                    last_updated=stats.get("last_updated", datetime.now(timezone.utc)),
                    storage_size_bytes=stats.get("storage_size_bytes", 0),
                    embedding_model=collection.embedding_model,
                )
                self.collections.append(card_data)

            # Update cache
            self.collections_cache = self.collections
            self.cache_timestamp = datetime.now(timezone.utc)

            # Rebuild UI
            self._rebuild_ui()

        except Exception as ex:
            # Show error to user
            if self._page:
                self._page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Failed to load collections: {str(ex)}"),
                        bgcolor=ft.colors.ERROR,
                    )
                )

            # Keep existing cached data if available
            if self.collections_cache:
                self.collections = self.collections_cache
            else:
                self.collections = []

            self._rebuild_ui()

    def _rebuild_ui(self):
        """Rebuild UI controls."""
        if self._page:
            self.controls = [
                self._build_header(),
                self._build_collections_grid(),
            ]
            self._page.update()

    def _invalidate_cache(self):
        """Invalidate collections cache."""
        self.collections_cache = None
        self.cache_timestamp = None
