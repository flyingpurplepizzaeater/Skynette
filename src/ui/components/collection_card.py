"""Collection card component for Knowledge Bases."""

from collections.abc import Callable
from datetime import UTC, datetime

import flet as ft

from src.ui.models.knowledge_bases import CollectionCardData
from src.ui.theme import Theme


class CollectionCard(ft.Container):
    """Card displaying collection stats and actions."""

    def __init__(
        self,
        data: CollectionCardData,
        on_query: Callable[[str], None],
        on_manage: Callable[[str], None],
    ):
        super().__init__()
        self.data = data
        self.on_query = on_query
        self.on_manage = on_manage

        self.content = ft.Column(
            controls=[
                # Header
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.FOLDER, size=32, color=Theme.PRIMARY),
                        ft.Text(
                            data.name,
                            size=20,
                            weight=ft.FontWeight.W_500,
                            color=Theme.TEXT_PRIMARY,
                        ),
                    ],
                    spacing=8,
                ),
                ft.Container(height=8),
                # Stats
                ft.Text(
                    f"📄 {data.document_count} documents",
                    size=14,
                    color=Theme.TEXT_SECONDARY,
                ),
                ft.Text(
                    f"🧩 {data.chunk_count:,} chunks",
                    size=14,
                    color=Theme.TEXT_SECONDARY,
                ),
                ft.Text(
                    f"🕐 Last: {self._format_time_ago(data.last_updated)}",
                    size=14,
                    color=Theme.TEXT_SECONDARY,
                ),
                ft.Text(
                    f"💾 {self._format_bytes(data.storage_size_bytes)}",
                    size=14,
                    color=Theme.TEXT_SECONDARY,
                ),
                ft.Container(height=16),
                # Actions
                ft.Row(
                    controls=[
                        ft.TextButton(
                            "Query",
                            icon=ft.Icons.SEARCH,
                            on_click=lambda _: on_query(data.id),
                        ),
                        ft.TextButton(
                            "Manage",
                            icon=ft.Icons.SETTINGS,
                            on_click=lambda _: on_manage(data.id),
                        ),
                    ],
                    spacing=8,
                ),
            ],
            spacing=4,
        )

        self.width = 280
        self.padding = 16
        self.border = ft.Border.all(1, Theme.BORDER)
        self.border_radius = 8
        self.bgcolor = Theme.SURFACE

    def _format_time_ago(self, dt: datetime) -> str:
        """Format datetime as relative time."""
        now = datetime.now(UTC)
        delta = now - dt
        total_seconds = delta.total_seconds()

        # Handle future dates (clock skew or bad data)
        if total_seconds < 0:
            return "just now"

        if total_seconds < 60:
            return "just now"
        elif total_seconds < 3600:
            minutes = int(total_seconds // 60)
            return f"{minutes}m ago"
        elif total_seconds < 86400:  # Less than 1 day
            hours = int(total_seconds // 3600)
            return f"{hours}h ago"
        elif delta.days < 30:
            return f"{delta.days}d ago"
        else:
            return dt.strftime("%Y-%m-%d")

    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes as human-readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024
        return f"{bytes_count:.1f} PB"
