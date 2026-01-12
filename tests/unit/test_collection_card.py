import pytest
import flet as ft
from datetime import datetime, timezone, timedelta
from src.ui.components.collection_card import CollectionCard
from src.ui.models.knowledge_bases import CollectionCardData


class TestCollectionCard:
    def test_card_creation(self):
        """CollectionCard should create with data."""
        data = CollectionCardData(
            id="coll-123",
            name="TestCollection",
            description="Test description",
            document_count=10,
            chunk_count=50,
            last_updated=datetime.now(timezone.utc),
            storage_size_bytes=1024 * 1024,  # 1 MB
            embedding_model="local",
        )

        card = CollectionCard(
            data=data,
            on_query=lambda id: None,
            on_manage=lambda id: None,
        )

        assert card is not None
        assert isinstance(card, ft.Container)

    def test_format_time_ago_seconds(self):
        """_format_time_ago should format seconds."""
        from src.ui.components.collection_card import CollectionCard

        data = CollectionCardData(
            id="test",
            name="Test",
            description="",
            document_count=0,
            chunk_count=0,
            last_updated=datetime.now(timezone.utc),
            storage_size_bytes=0,
            embedding_model="local",
        )
        card = CollectionCard(data, lambda x: None, lambda x: None)

        result = card._format_time_ago(datetime.now(timezone.utc))
        assert result == "just now"

    def test_format_bytes(self):
        """_format_bytes should format sizes correctly."""
        from src.ui.components.collection_card import CollectionCard

        data = CollectionCardData(
            id="test",
            name="Test",
            description="",
            document_count=0,
            chunk_count=0,
            last_updated=datetime.now(timezone.utc),
            storage_size_bytes=0,
            embedding_model="local",
        )
        card = CollectionCard(data, lambda x: None, lambda x: None)

        assert card._format_bytes(512) == "512.0 B"
        assert card._format_bytes(1024) == "1.0 KB"
        assert card._format_bytes(1024 * 1024) == "1.0 MB"
        assert card._format_bytes(1024 * 1024 * 1024) == "1.0 GB"

    def test_format_time_ago_minutes(self):
        """_format_time_ago should format minutes correctly."""
        from src.ui.components.collection_card import CollectionCard

        data = CollectionCardData(
            id="test", name="Test", description="",
            document_count=0, chunk_count=0,
            last_updated=datetime.now(timezone.utc),
            storage_size_bytes=0, embedding_model="local",
        )
        card = CollectionCard(data, lambda x: None, lambda x: None)

        five_min_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert card._format_time_ago(five_min_ago) == "5m ago"

    def test_format_time_ago_hours(self):
        """_format_time_ago should format hours correctly."""
        from src.ui.components.collection_card import CollectionCard

        data = CollectionCardData(
            id="test", name="Test", description="",
            document_count=0, chunk_count=0,
            last_updated=datetime.now(timezone.utc),
            storage_size_bytes=0, embedding_model="local",
        )
        card = CollectionCard(data, lambda x: None, lambda x: None)

        three_hours_ago = datetime.now(timezone.utc) - timedelta(hours=3)
        assert card._format_time_ago(three_hours_ago) == "3h ago"

    def test_format_time_ago_days(self):
        """_format_time_ago should format days correctly."""
        from src.ui.components.collection_card import CollectionCard

        data = CollectionCardData(
            id="test", name="Test", description="",
            document_count=0, chunk_count=0,
            last_updated=datetime.now(timezone.utc),
            storage_size_bytes=0, embedding_model="local",
        )
        card = CollectionCard(data, lambda x: None, lambda x: None)

        two_days_ago = datetime.now(timezone.utc) - timedelta(days=2)
        assert card._format_time_ago(two_days_ago) == "2d ago"

    def test_format_time_ago_days_with_seconds(self):
        """_format_time_ago should handle multi-day deltas with small seconds."""
        from src.ui.components.collection_card import CollectionCard

        data = CollectionCardData(
            id="test", name="Test", description="",
            document_count=0, chunk_count=0,
            last_updated=datetime.now(timezone.utc),
            storage_size_bytes=0, embedding_model="local",
        )
        card = CollectionCard(data, lambda x: None, lambda x: None)

        # This catches the delta.seconds bug
        two_days_30sec_ago = datetime.now(timezone.utc) - timedelta(days=2, seconds=30)
        assert card._format_time_ago(two_days_30sec_ago) == "2d ago"

    def test_format_time_ago_future_date(self):
        """_format_time_ago should handle future dates gracefully."""
        from src.ui.components.collection_card import CollectionCard

        data = CollectionCardData(
            id="test", name="Test", description="",
            document_count=0, chunk_count=0,
            last_updated=datetime.now(timezone.utc),
            storage_size_bytes=0, embedding_model="local",
        )
        card = CollectionCard(data, lambda x: None, lambda x: None)

        future_date = datetime.now(timezone.utc) + timedelta(hours=1)
        assert card._format_time_ago(future_date) == "just now"
