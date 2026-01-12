"""Query dialog for testing collection searches."""

import flet as ft
import time
from typing import List
from src.ui.theme import Theme
from src.ui.models.knowledge_bases import QueryResultUI
from src.rag.service import RAGService


class QueryDialog(ft.AlertDialog):
    """Dialog for querying a collection."""

    def __init__(
        self,
        rag_service: RAGService,
        collection_id: str,
        collection_name: str,
    ):
        super().__init__()
        self.rag_service = rag_service
        self.collection_id = collection_id
        self.collection_name = collection_name

        # Query field
        self.query_field = ft.TextField(
            label="Query",
            hint_text="Ask a question about your documents...",
            multiline=True,
            min_lines=2,
            max_lines=4,
            autofocus=True,
        )

        # Options
        self.top_k_slider = ft.Slider(
            min=1,
            max=10,
            value=5,
            divisions=9,
            label="{value} results",
        )

        self.min_similarity_slider = ft.Slider(
            min=0.0,
            max=1.0,
            value=0.5,
            divisions=10,
            label="{value}",
        )

        # Results
        self.query_time_text = ft.Text("", size=12, color=Theme.TEXT_SECONDARY)
        self.results_column = ft.Column(scroll=ft.ScrollMode.AUTO)

        # Build dialog
        self.modal = True
        self.title = ft.Text(f'Query "{collection_name}"')
        self.content = ft.Column(
            controls=[
                ft.Text("Test Query", weight=ft.FontWeight.BOLD),
                self.query_field,
                ft.Container(height=8),
                ft.Text("Options", weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Text("Top K results:", size=14),
                    ft.Container(expand=True),
                    self.top_k_slider,
                ]),
                ft.Row([
                    ft.Text("Min similarity:", size=14),
                    ft.Container(expand=True),
                    self.min_similarity_slider,
                ]),
                ft.Container(height=8),
                ft.Button("Search", on_click=self._on_search, icon=ft.Icons.SEARCH),
                ft.Divider(),
                self.query_time_text,
                self.results_column,
            ],
            width=700,
            height=600,
            scroll=ft.ScrollMode.AUTO,
        )

        self.actions = [
            ft.TextButton("Close", on_click=lambda _: self._close()),
        ]

    async def _on_search(self, e):
        """Handle search button click."""
        # Validate query not empty
        if not self.query_field.value or not self.query_field.value.strip():
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Please enter a query"),
                        bgcolor=ft.colors.WARNING,
                    )
                )
            return

        # Clear previous results
        self.results_column.controls = [
            ft.ProgressRing(),
            ft.Text("Searching...", italic=True),
        ]
        if self.page:
            self.page.update()

        start_time = time.time()

        try:
            # Query backend
            results = await self.rag_service.query(
                query=self.query_field.value,
                collection_id=self.collection_id,
                top_k=int(self.top_k_slider.value),
                min_similarity=self.min_similarity_slider.value,
            )

            query_time_ms = int((time.time() - start_time) * 1000)

            # Convert to UI models
            ui_results = [QueryResultUI.from_backend_result(r) for r in results]

            # Display results
            self.query_time_text.value = f"Found {len(ui_results)} results in {query_time_ms}ms"

            if not ui_results:
                self.results_column.controls = [
                    ft.Container(
                        content=ft.Text(
                            "No results found.\n\n"
                            "Try:\n"
                            "• Different keywords\n"
                            "• Lower min similarity threshold\n"
                            "• Adding more documents to this collection",
                            italic=True,
                            size=14,
                        ),
                        padding=20,
                    )
                ]
            else:
                self.results_column.controls = [
                    self._build_result_card(i + 1, result)
                    for i, result in enumerate(ui_results)
                ]

        except Exception as ex:
            self.query_time_text.value = ""
            self.results_column.controls = [
                ft.Container(
                    content=ft.Text(
                        f"Error: {str(ex)}",
                        color=ft.colors.ERROR,
                    ),
                    padding=20,
                )
            ]

        if self.page:
            self.page.update()

    def _build_result_card(self, index: int, result: QueryResultUI) -> ft.Container:
        """Build a result card."""
        # Truncate long content
        preview = result.chunk_content
        if len(preview) > 500:
            preview = preview[:500] + "..."

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"{index}. {result.source_file}",
                                weight=ft.FontWeight.BOLD,
                                size=14,
                            ),
                            ft.Container(expand=True),
                            ft.Text(
                                f"similarity: {result.similarity:.2f}",
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.COPY,
                                icon_size=16,
                                tooltip="Copy chunk text",
                                on_click=lambda _, r=result: self._copy_text(r.chunk_content),
                            ),
                        ],
                    ),
                    ft.Container(
                        content=ft.Text(
                            preview,
                            font_family="monospace",
                            size=12,
                        ),
                        bgcolor=Theme.BG_SECONDARY,
                        padding=12,
                        border_radius=4,
                    ),
                ],
                spacing=8,
            ),
            border=ft.Border.all(1, Theme.BORDER),
            border_radius=8,
            padding=12,
            margin=ft.margin.only(bottom=8),
        )

    def _copy_text(self, text: str):
        """Copy text to clipboard."""
        if self.page:
            try:
                self.page.set_clipboard(text)
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Copied to clipboard"))
                )
            except Exception as e:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(f"Failed to copy: {str(e)}"))
                )

    def _close(self):
        """Close dialog."""
        self.open = False
        if self.page:
            self.page.update()
