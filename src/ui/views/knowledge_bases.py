"""Knowledge Bases view for RAG collection management."""

import flet as ft
from typing import List, Optional
from src.ui.theme import Theme
from src.ui.models.knowledge_bases import CollectionCardData
from src.ui.components.collection_card import CollectionCard
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
        # TODO: Implement in Task 4 (CollectionDialog)
        pass

    def _on_query_collection(self, collection_id: str):
        """Handle Query button click."""
        # TODO: Implement in Task 7 (QueryDialog)
        pass

    def _on_manage_collection(self, collection_id: str):
        """Handle Manage button click."""
        # TODO: Implement in Task 4 (CollectionDialog)
        pass
