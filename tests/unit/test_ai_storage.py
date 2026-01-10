"""Tests for AI storage functionality."""

import pytest
import sqlite3
from pathlib import Path

from src.data.storage import WorkflowStorage


class TestAIStorageMigration:
    """Test AI database tables are created."""

    def test_ai_providers_table_exists(self, tmp_path):
        """Test ai_providers table is created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        with sqlite3.connect(storage.db_path) as conn:
            cursor = conn.cursor()

            # Check table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_providers'"
            )
            result = cursor.fetchone()

        assert result is not None, "ai_providers table should exist"

    def test_ai_usage_table_exists(self, tmp_path):
        """Test ai_usage table is created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        with sqlite3.connect(storage.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_usage'"
            )
            result = cursor.fetchone()

        assert result is not None, "ai_usage table should exist"

    def test_local_models_table_exists(self, tmp_path):
        """Test local_models table is created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        with sqlite3.connect(storage.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='local_models'"
            )
            result = cursor.fetchone()

        assert result is not None, "local_models table should exist"

    def test_ai_budgets_table_exists(self, tmp_path):
        """Test ai_budgets table is created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        with sqlite3.connect(storage.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_budgets'"
            )
            result = cursor.fetchone()

        assert result is not None, "ai_budgets table should exist"

    def test_ai_usage_indices_exist(self, tmp_path):
        """Test indices on ai_usage table are created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        with sqlite3.connect(storage.db_path) as conn:
            cursor = conn.cursor()

            # Check indices exist
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ai_usage'"
            )
            indices = cursor.fetchall()

        index_names = [idx[0] for idx in indices]
        assert 'idx_ai_usage_workflow' in index_names
        assert 'idx_ai_usage_timestamp' in index_names
        assert 'idx_ai_usage_provider' in index_names
