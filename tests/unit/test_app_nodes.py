"""
Tests for App Integration Nodes.

This module provides comprehensive tests for all app integration nodes
including Slack, Email, Discord, GitHub, Database, and more.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json


# ============================================================================
# Slack Node Tests
# ============================================================================

class TestSlackSendMessageNode:
    """Tests for SlackSendMessageNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.slack import SlackSendMessageNode
        return SlackSendMessageNode()

    @pytest.fixture
    def webhook_config(self):
        return {
            "webhook_url": "https://hooks.slack.com/services/T00/B00/XXX",
            "message": "Test message",
        }

    @pytest.fixture
    def bot_config(self):
        return {
            "bot_token": "xoxb-test-token",
            "channel": "#general",
            "message": "Test message from bot",
        }

    @pytest.mark.asyncio
    async def test_send_via_webhook_success(self, node, webhook_config):
        """Test sending message via webhook successfully."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(webhook_config, {})

            assert result["success"] is True
            assert result["message_ts"] == ""
            assert result["channel_id"] == ""

    @pytest.mark.asyncio
    async def test_send_via_webhook_failure(self, node, webhook_config):
        """Test handling webhook failure."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(webhook_config, {})

            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_send_via_bot_api_success(self, node, bot_config):
        """Test sending message via bot API successfully."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "ts": "1234567890.123456",
                "channel": "C1234567890",
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(bot_config, {})

            assert result["success"] is True
            assert result["message_ts"] == "1234567890.123456"
            assert result["channel_id"] == "C1234567890"

    @pytest.mark.asyncio
    async def test_send_via_bot_api_with_thread(self, node, bot_config):
        """Test sending threaded reply via bot API."""
        bot_config["thread_ts"] = "1234567890.000000"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "ts": "1234567890.123457"}
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await node.execute(bot_config, {})

            # Verify thread_ts was passed
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["json"]["thread_ts"] == "1234567890.000000"

    @pytest.mark.asyncio
    async def test_missing_auth_raises_error(self, node):
        """Test that missing auth raises ValueError."""
        config = {"message": "Test message"}

        with pytest.raises(ValueError, match="Either webhook_url or bot_token"):
            await node.execute(config, {})

    @pytest.mark.asyncio
    async def test_bot_without_channel_raises_error(self, node):
        """Test that bot token without channel raises error."""
        config = {"bot_token": "xoxb-test", "message": "Test"}

        with patch("httpx.AsyncClient"):
            with pytest.raises(ValueError, match="Channel is required"):
                await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "slack-send-message"
        assert node.category == "Apps"
        assert len(node.inputs) > 0
        assert len(node.outputs) > 0


class TestSlackReactionNode:
    """Tests for SlackReactionNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.slack import SlackReactionNode
        return SlackReactionNode()

    @pytest.fixture
    def config(self):
        return {
            "bot_token": "xoxb-test-token",
            "channel": "C1234567890",
            "message_ts": "1234567890.123456",
            "emoji": "thumbsup",
        }

    @pytest.mark.asyncio
    async def test_add_reaction_success(self, node, config):
        """Test adding reaction successfully."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"ok": True}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_add_reaction_failure(self, node, config):
        """Test handling reaction failure."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"ok": False, "error": "already_reacted"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False


# ============================================================================
# Discord Node Tests
# ============================================================================

class TestDiscordWebhookNode:
    """Tests for DiscordWebhookNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.discord import DiscordWebhookNode
        return DiscordWebhookNode()

    @pytest.fixture
    def config(self):
        return {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
            "content": "Test message",
        }

    @pytest.mark.asyncio
    async def test_send_simple_message(self, node, config):
        """Test sending simple text message."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["status_code"] == 204

    @pytest.mark.asyncio
    async def test_send_with_embed(self, node, config):
        """Test sending message with embed."""
        config["embed_title"] = "Test Embed"
        config["embed_description"] = "This is a test embed"
        config["embed_color"] = "#FF5733"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await node.execute(config, {})

            assert result["success"] is True
            # Verify embed was included in payload
            call_kwargs = mock_post.call_args[1]
            assert "embeds" in call_kwargs["json"]
            assert call_kwargs["json"]["embeds"][0]["title"] == "Test Embed"

    @pytest.mark.asyncio
    async def test_send_with_custom_username(self, node, config):
        """Test sending with custom username and avatar."""
        config["username"] = "Test Bot"
        config["avatar_url"] = "https://example.com/avatar.png"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await node.execute(config, {})

            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["json"]["username"] == "Test Bot"
            assert call_kwargs["json"]["avatar_url"] == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_empty_message_gets_default(self, node):
        """Test that empty message gets default content."""
        config = {"webhook_url": "https://discord.com/api/webhooks/123/abc"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await node.execute(config, {})

            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["json"]["content"] == "Empty message"

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "discord-webhook"
        assert node.color == "#5865F2"  # Discord blurple


class TestDiscordBotMessageNode:
    """Tests for DiscordBotMessageNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.discord import DiscordBotMessageNode
        return DiscordBotMessageNode()

    @pytest.fixture
    def config(self):
        return {
            "bot_token": "test-bot-token",
            "channel_id": "123456789",
            "content": "Hello from bot!",
        }

    @pytest.mark.asyncio
    async def test_send_bot_message_success(self, node, config):
        """Test sending message via bot API."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "msg-123"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["message_id"] == "msg-123"

    @pytest.mark.asyncio
    async def test_send_reply_to_message(self, node, config):
        """Test sending reply to existing message."""
        config["reply_to"] = "original-msg-id"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "reply-123"}
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await node.execute(config, {})

            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["json"]["message_reference"]["message_id"] == "original-msg-id"


# ============================================================================
# GitHub Node Tests
# ============================================================================

class TestGitHubCreateIssueNode:
    """Tests for GitHubCreateIssueNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.github import GitHubCreateIssueNode
        return GitHubCreateIssueNode()

    @pytest.fixture
    def config(self):
        return {
            "token": "ghp_test_token",
            "owner": "testowner",
            "repo": "testrepo",
            "title": "Test Issue",
            "body": "This is a test issue",
        }

    @pytest.mark.asyncio
    async def test_create_issue_success(self, node, config):
        """Test creating issue successfully."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "number": 42,
                "html_url": "https://github.com/testowner/testrepo/issues/42",
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["issue_number"] == 42
            assert "issues/42" in result["issue_url"]

    @pytest.mark.asyncio
    async def test_create_issue_with_labels(self, node, config):
        """Test creating issue with labels."""
        config["labels"] = "bug, priority:high"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"number": 1, "html_url": ""}
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await node.execute(config, {})

            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["json"]["labels"] == ["bug", "priority:high"]

    @pytest.mark.asyncio
    async def test_create_issue_failure(self, node, config):
        """Test handling issue creation failure."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"message": "Bad credentials"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False
            assert result["issue_number"] == 0

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "github-create-issue"
        assert node.color == "#24292E"


class TestGitHubCreatePRNode:
    """Tests for GitHubCreatePRNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.github import GitHubCreatePRNode
        return GitHubCreatePRNode()

    @pytest.fixture
    def config(self):
        return {
            "token": "ghp_test_token",
            "owner": "testowner",
            "repo": "testrepo",
            "title": "Test PR",
            "head": "feature-branch",
            "base": "main",
        }

    @pytest.mark.asyncio
    async def test_create_pr_success(self, node, config):
        """Test creating PR successfully."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "number": 100,
                "html_url": "https://github.com/testowner/testrepo/pull/100",
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["pr_number"] == 100

    @pytest.mark.asyncio
    async def test_create_draft_pr(self, node, config):
        """Test creating draft PR."""
        config["draft"] = True

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"number": 101, "html_url": ""}
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await node.execute(config, {})

            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["json"]["draft"] is True


class TestGitHubListReposNode:
    """Tests for GitHubListReposNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.github import GitHubListReposNode
        return GitHubListReposNode()

    @pytest.fixture
    def config(self):
        return {
            "token": "ghp_test_token",
            "type": "owner",
        }

    @pytest.mark.asyncio
    async def test_list_own_repos(self, node, config):
        """Test listing own repositories."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {
                    "name": "repo1",
                    "full_name": "user/repo1",
                    "description": "Test repo",
                    "html_url": "https://github.com/user/repo1",
                    "stargazers_count": 10,
                    "forks_count": 2,
                    "private": False,
                }
            ]
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 1
            assert result["repositories"][0]["name"] == "repo1"
            assert result["repositories"][0]["stars"] == 10

    @pytest.mark.asyncio
    async def test_list_user_repos(self, node, config):
        """Test listing another user's repositories."""
        config["type"] = "user"
        config["username"] = "octocat"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = []
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await node.execute(config, {})

            # Verify correct URL was called
            call_args = mock_get.call_args[0]
            assert "users/octocat/repos" in call_args[0]


# ============================================================================
# Email Node Tests
# ============================================================================

class TestEmailSendNode:
    """Tests for EmailSendNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.email import EmailSendNode
        return EmailSendNode()

    @pytest.fixture
    def config(self):
        return {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@gmail.com",
            "password": "app_password",
            "from_email": "test@gmail.com",
            "to": "recipient@example.com",
            "subject": "Test Subject",
            "body": "Test body content",
            "use_tls": True,
        }

    @pytest.mark.asyncio
    async def test_send_email_success(self, node, config):
        """Test sending email successfully."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["message_id"] != ""
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.sendmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_html(self, node, config):
        """Test sending HTML email."""
        config["html"] = "<h1>Hello</h1><p>Test HTML content</p>"

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server

            result = await node.execute(config, {})

            assert result["success"] is True
            # Verify multipart message was created
            sendmail_call = mock_server.sendmail.call_args
            msg_str = sendmail_call[0][2]
            assert "multipart/alternative" in msg_str

    @pytest.mark.asyncio
    async def test_send_email_ssl(self, node, config):
        """Test sending email via SSL (port 465)."""
        config["smtp_port"] = 465

        with patch("smtplib.SMTP_SSL") as mock_smtp_ssl:
            mock_server = MagicMock()
            mock_smtp_ssl.return_value = mock_server

            result = await node.execute(config, {})

            assert result["success"] is True
            mock_smtp_ssl.assert_called_once_with("smtp.gmail.com", 465)

    @pytest.mark.asyncio
    async def test_send_email_multiple_recipients(self, node, config):
        """Test sending to multiple recipients."""
        config["to"] = "a@example.com, b@example.com"
        config["cc"] = "c@example.com"
        config["bcc"] = "d@example.com"

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server

            await node.execute(config, {})

            sendmail_call = mock_server.sendmail.call_args
            recipients = sendmail_call[0][1]
            assert len(recipients) == 4

    @pytest.mark.asyncio
    async def test_send_email_failure(self, node, config):
        """Test handling email send failure."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.login.side_effect = Exception("Auth failed")

            result = await node.execute(config, {})

            assert result["success"] is False

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "email-send"
        assert node.color == "#EA4335"  # Gmail red


class TestEmailReadNode:
    """Tests for EmailReadNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.email import EmailReadNode
        return EmailReadNode()

    @pytest.fixture
    def config(self):
        return {
            "imap_host": "imap.gmail.com",
            "imap_port": 993,
            "username": "test@gmail.com",
            "password": "app_password",
            "folder": "INBOX",
            "filter": "unseen",
            "limit": 10,
        }

    @pytest.mark.asyncio
    async def test_read_emails_success(self, node, config):
        """Test reading emails successfully."""
        mock_email = b"""From: sender@example.com
To: test@gmail.com
Subject: Test Email
Date: Mon, 1 Jan 2024 12:00:00 +0000

This is a test email body."""

        with patch("imaplib.IMAP4_SSL") as mock_imap:
            mock_mail = MagicMock()
            mock_imap.return_value = mock_mail
            mock_mail.search.return_value = (None, [b"1"])
            mock_mail.fetch.return_value = (None, [(b"1", mock_email)])

            result = await node.execute(config, {})

            assert result["count"] == 1
            assert result["emails"][0]["subject"] == "Test Email"

    @pytest.mark.asyncio
    async def test_read_emails_empty(self, node, config):
        """Test handling empty inbox."""
        with patch("imaplib.IMAP4_SSL") as mock_imap:
            mock_mail = MagicMock()
            mock_imap.return_value = mock_mail
            mock_mail.search.return_value = (None, [b""])

            result = await node.execute(config, {})

            assert result["count"] == 0
            assert result["emails"] == []

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "email-read"


# ============================================================================
# Database Node Tests
# ============================================================================

class TestSQLiteQueryNode:
    """Tests for SQLiteQueryNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.database import SQLiteQueryNode
        return SQLiteQueryNode()

    @pytest.fixture
    def config(self, tmp_path):
        db_path = tmp_path / "test.db"
        return {
            "database": str(db_path),
            "query": "SELECT 1 as value",
        }

    @pytest.mark.asyncio
    async def test_simple_query(self, node, config, tmp_path):
        """Test executing simple SELECT query."""
        # Create test database
        import sqlite3
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'Alice')")
        conn.commit()
        conn.close()

        config["database"] = str(db_path)
        config["query"] = "SELECT * FROM test"

        result = await node.execute(config, {})

        assert result["row_count"] == 1
        assert result["rows"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_query_with_parameters(self, node, config, tmp_path):
        """Test query with parameters."""
        import sqlite3
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO users VALUES (1, 'Bob')")
        conn.execute("INSERT INTO users VALUES (2, 'Alice')")
        conn.commit()
        conn.close()

        config["database"] = str(db_path)
        config["query"] = "SELECT * FROM users WHERE name = ?"
        config["parameters"] = '["Alice"]'

        result = await node.execute(config, {})

        assert result["row_count"] == 1
        assert result["rows"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_insert_operation(self, node, config, tmp_path):
        """Test INSERT operation."""
        import sqlite3
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        conn.close()

        config["database"] = str(db_path)
        config["query"] = "INSERT INTO items (name) VALUES (?)"
        config["parameters"] = '["TestItem"]'
        config["operation"] = "execute"

        result = await node.execute(config, {})

        assert result["row_count"] == 1
        assert result["last_id"] == 1

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "sqlite-query"


class TestPostgreSQLQueryNode:
    """Tests for PostgreSQLQueryNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.database import PostgreSQLQueryNode
        return PostgreSQLQueryNode()

    @pytest.fixture
    def config(self):
        return {
            "connection_string": "postgresql://testuser:testpass@localhost:5432/testdb",
            "query": "SELECT 1 as value",
            "operation": "fetch",
        }

    @pytest.mark.asyncio
    async def test_query_raises_without_asyncpg(self, node, config):
        """Test PostgreSQL raises helpful error when asyncpg not installed."""
        # This test verifies the error handling when asyncpg is missing
        try:
            import asyncpg
            # If asyncpg is installed, we need to mock it
            pytest.skip("asyncpg is installed, skipping missing module test")
        except ImportError:
            # asyncpg not installed - test the error handling
            with pytest.raises(RuntimeError, match="asyncpg not installed"):
                await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "postgresql-query"

    def test_node_inputs(self, node):
        """Test node has required inputs."""
        input_names = [i.name for i in node.inputs]
        assert "connection_string" in input_names
        assert "query" in input_names


# ============================================================================
# Telegram Node Tests
# ============================================================================

class TestTelegramSendMessageNode:
    """Tests for TelegramSendMessageNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.telegram import TelegramSendMessageNode
        return TelegramSendMessageNode()

    @pytest.fixture
    def config(self):
        return {
            "bot_token": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ",
            "chat_id": "987654321",
            "text": "Hello from Skynette!",
        }

    @pytest.mark.asyncio
    async def test_send_message_success(self, node, config):
        """Test sending Telegram message."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": {"message_id": 12345},
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["message_id"] == 12345

    @pytest.mark.asyncio
    async def test_send_with_parse_mode(self, node, config):
        """Test sending with markdown parse mode."""
        config["parse_mode"] = "Markdown"
        config["text"] = "*Bold* and _italic_"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "result": {"message_id": 1}}
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await node.execute(config, {})

            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["json"]["parse_mode"] == "Markdown"

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "telegram-send-message"


# ============================================================================
# Google Sheets Node Tests
# ============================================================================

class TestGoogleSheetsReadNode:
    """Tests for GoogleSheetsReadNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.google_sheets import GoogleSheetsReadNode
        return GoogleSheetsReadNode()

    @pytest.fixture
    def config(self):
        # Google Sheets requires service account JSON credentials
        return {
            "credentials_json": '{"type": "service_account", "project_id": "test"}',
            "spreadsheet_id": "1abc123def456",
            "range": "Sheet1!A1:D10",
            "has_header": True,
            "output_format": "objects",
        }

    @pytest.mark.asyncio
    async def test_read_sheets_with_mocked_api(self, node, config):
        """Test reading from Google Sheets with mocked Google API."""
        # Mock at the import level since imports happen inside execute()
        mock_creds = MagicMock()
        mock_service = MagicMock()
        mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
            "values": [
                ["Name", "Age"],
                ["Alice", "30"],
                ["Bob", "25"],
            ]
        }

        with patch.dict("sys.modules", {
            "google": MagicMock(),
            "google.oauth2": MagicMock(),
            "google.oauth2.service_account": MagicMock(),
            "googleapiclient": MagicMock(),
            "googleapiclient.discovery": MagicMock(),
        }):
            with patch("google.oauth2.service_account.Credentials") as mock_sa:
                with patch("googleapiclient.discovery.build") as mock_build:
                    mock_sa.from_service_account_info.return_value = mock_creds
                    mock_build.return_value = mock_service

                    result = await node.execute(config, {})

                    # With has_header=True, first row is headers, so 2 data rows
                    assert result["row_count"] == 2
                    assert result["columns"] == ["Name", "Age"]

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "google-sheets-read"

    def test_node_inputs(self, node):
        """Test node has required inputs."""
        input_names = [i.name for i in node.inputs]
        assert "credentials_json" in input_names
        assert "spreadsheet_id" in input_names
        assert "range" in input_names


# ============================================================================
# Notion Node Tests
# ============================================================================

class TestNotionQueryDatabaseNode:
    """Tests for NotionQueryDatabaseNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.notion import NotionQueryDatabaseNode
        return NotionQueryDatabaseNode()

    @pytest.fixture
    def config(self):
        return {
            "api_key": "secret_test_key",
            "database_id": "abc123def456",
        }

    @pytest.mark.asyncio
    async def test_query_database_success(self, node, config):
        """Test querying Notion database."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {"id": "page-1", "properties": {}},
                    {"id": "page-2", "properties": {}},
                ],
                "has_more": False,
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            # Notion returns "results" and "count", not "success" and "pages"
            assert result["count"] == 2
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_query_with_filter(self, node, config):
        """Test querying with filter."""
        config["filter_property"] = "Status"
        config["filter_value"] = "Done"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [{"id": "page-1"}],
                "has_more": False,
            }
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await node.execute(config, {})

            # Verify filter was included in request
            call_kwargs = mock_post.call_args[1]
            assert "filter" in call_kwargs["json"]

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "notion-query-database"


# ============================================================================
# AWS S3 Node Tests
# ============================================================================

class TestS3UploadNode:
    """Tests for S3UploadNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.aws_s3 import S3UploadNode
        return S3UploadNode()

    @pytest.fixture
    def config(self):
        return {
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "region": "us-east-1",
            "bucket": "test-bucket",
            "key": "uploads/test.txt",
            "content": "Hello, S3!",
        }

    @pytest.mark.asyncio
    async def test_upload_success(self, node, config):
        """Test S3 upload with mocked boto3."""
        with patch("boto3.client") as mock_boto:
            mock_s3 = MagicMock()
            mock_boto.return_value = mock_s3

            result = await node.execute(config, {})

            assert result["success"] is True
            mock_s3.put_object.assert_called_once()

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "s3-upload"


# ============================================================================
# Twitter Node Tests
# ============================================================================

class TestTwitterPostTweetNode:
    """Tests for TwitterPostTweetNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.twitter import TwitterPostTweetNode
        return TwitterPostTweetNode()

    @pytest.fixture
    def config(self):
        return {
            "api_key": "test_api_key",
            "api_secret": "test_api_secret",
            "access_token": "test_access_token",
            "access_token_secret": "test_access_token_secret",
            "text": "Hello Twitter from Skynette!",
        }

    @pytest.mark.asyncio
    async def test_post_tweet_success(self, node, config):
        """Test posting a tweet."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "data": {
                    "id": "1234567890",
                    "text": "Hello Twitter from Skynette!",
                }
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["tweet_id"] == "1234567890"

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "twitter-post-tweet"


# ============================================================================
# Webhook Node Tests
# ============================================================================

class TestWebhookCallNode:
    """Tests for WebhookCallNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.webhook import WebhookCallNode
        return WebhookCallNode()

    @pytest.fixture
    def config(self):
        return {
            "url": "https://api.example.com/webhook",
            "method": "POST",
            "body": '{"event": "test"}',
        }

    @pytest.mark.asyncio
    async def test_webhook_call_success(self, node, config):
        """Test calling a webhook."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"received": True}
            mock_response.headers = {"content-type": "application/json"}
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_webhook_call_with_headers(self, node, config):
        """Test webhook call with custom headers."""
        config["headers"] = '{"X-Custom-Header": "test-value"}'

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_response.headers = {}
            mock_request = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.request = mock_request

            await node.execute(config, {})

            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["headers"]["X-Custom-Header"] == "test-value"

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "webhook-call"


# ============================================================================
# Google Drive Node Tests
# ============================================================================

class TestGoogleDriveListNode:
    """Tests for GoogleDriveListNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.google_drive import GoogleDriveListNode
        return GoogleDriveListNode()

    @pytest.fixture
    def mock_service(self):
        """Create mock Google Drive service."""
        mock_svc = MagicMock()
        mock_files = MagicMock()
        mock_list = MagicMock()
        mock_list.execute.return_value = {
            "files": [
                {
                    "id": "file1",
                    "name": "Document.docx",
                    "mimeType": "application/vnd.google-apps.document",
                    "size": "1024",
                },
                {
                    "id": "folder1",
                    "name": "My Folder",
                    "mimeType": "application/vnd.google-apps.folder",
                },
            ]
        }
        mock_files.list.return_value = mock_list
        mock_svc.files.return_value = mock_files
        return mock_svc

    @pytest.mark.asyncio
    async def test_list_files_success(self, node, mock_service):
        """Test listing files successfully."""
        config = {"credentials_json": '{"type": "service_account", "private_key": "key"}'}

        with patch("src.core.nodes.apps.google_drive._get_drive_service") as mock_get:
            mock_get.return_value = mock_service

            result = await node.execute(config, {})

            assert result["count"] == 2
            assert len(result["files"]) == 2
            assert result["files"][0]["name"] == "Document.docx"

    @pytest.mark.asyncio
    async def test_list_files_empty(self, node):
        """Test listing when no files exist."""
        config = {"credentials_json": '{"type": "service_account"}'}

        mock_svc = MagicMock()
        mock_files = MagicMock()
        mock_list = MagicMock()
        mock_list.execute.return_value = {"files": []}
        mock_files.list.return_value = mock_list
        mock_svc.files.return_value = mock_files

        with patch("src.core.nodes.apps.google_drive._get_drive_service") as mock_get:
            mock_get.return_value = mock_svc

            result = await node.execute(config, {})

            assert result["count"] == 0
            assert result["files"] == []

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "google-drive-list"
        assert node.category == "Apps"


class TestGoogleDriveUploadNode:
    """Tests for GoogleDriveUploadNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.google_drive import GoogleDriveUploadNode
        return GoogleDriveUploadNode()

    @pytest.mark.asyncio
    async def test_upload_text_file(self, node):
        """Test uploading a text file."""
        config = {
            "credentials_json": '{"type": "service_account"}',
            "filename": "test.txt",
            "content": "Hello, World!",
            "mime_type": "text/plain",
        }

        mock_svc = MagicMock()
        mock_files = MagicMock()
        mock_create = MagicMock()
        mock_create.execute.return_value = {
            "id": "new-file-id",
            "webViewLink": "https://drive.google.com/file/d/new-file-id/view",
        }
        mock_files.create.return_value = mock_create
        mock_svc.files.return_value = mock_files

        with patch("src.core.nodes.apps.google_drive._get_drive_service") as mock_get:
            with patch("googleapiclient.http.MediaIoBaseUpload"):
                mock_get.return_value = mock_svc

                result = await node.execute(config, {})

                assert result["success"] is True
                assert result["file_id"] == "new-file-id"
                assert "drive.google.com" in result["web_link"]

    @pytest.mark.asyncio
    async def test_upload_to_folder(self, node):
        """Test uploading to a specific folder."""
        config = {
            "credentials_json": '{"type": "service_account"}',
            "filename": "test.txt",
            "content": "Content",
            "folder_id": "folder123",
        }

        mock_svc = MagicMock()
        mock_files = MagicMock()
        mock_create = MagicMock()
        mock_create.execute.return_value = {"id": "file-id", "webViewLink": ""}
        mock_files.create.return_value = mock_create
        mock_svc.files.return_value = mock_files

        with patch("src.core.nodes.apps.google_drive._get_drive_service") as mock_get:
            with patch("googleapiclient.http.MediaIoBaseUpload"):
                mock_get.return_value = mock_svc

                await node.execute(config, {})

                call_args = mock_files.create.call_args
                body = call_args[1]["body"]
                assert "folder123" in body["parents"]

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "google-drive-upload"


class TestGoogleDriveDownloadNode:
    """Tests for GoogleDriveDownloadNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.google_drive import GoogleDriveDownloadNode
        return GoogleDriveDownloadNode()

    @pytest.mark.asyncio
    async def test_download_binary_file(self, node):
        """Test downloading a binary file."""
        config = {
            "credentials_json": '{"type": "service_account"}',
            "file_id": "file123",
        }

        mock_svc = MagicMock()
        mock_files = MagicMock()

        # Mock get for metadata
        mock_get = MagicMock()
        mock_get.execute.return_value = {
            "id": "file123",
            "name": "image.png",
            "mimeType": "image/png",
            "size": "1024",
        }
        mock_files.get.return_value = mock_get

        # Mock get_media for download
        mock_media = MagicMock()
        mock_media.execute.return_value = b"binary content here"
        mock_files.get_media.return_value = mock_media

        mock_svc.files.return_value = mock_files

        with patch("src.core.nodes.apps.google_drive._get_drive_service") as mock_get_svc:
            mock_get_svc.return_value = mock_svc

            result = await node.execute(config, {})

            assert result["filename"] == "image.png"
            assert result["mime_type"] == "image/png"
            assert result["size"] == len(b"binary content here")

    @pytest.mark.asyncio
    async def test_export_google_doc(self, node):
        """Test exporting a Google Doc to PDF."""
        config = {
            "credentials_json": '{"type": "service_account"}',
            "file_id": "doc123",
            "export_format": "pdf",
        }

        mock_svc = MagicMock()
        mock_files = MagicMock()

        # Mock get for metadata
        mock_get = MagicMock()
        mock_get.execute.return_value = {
            "id": "doc123",
            "name": "My Document",
            "mimeType": "application/vnd.google-apps.document",
        }
        mock_files.get.return_value = mock_get

        # Mock export_media for export
        mock_export = MagicMock()
        mock_export.execute.return_value = b"PDF content"
        mock_files.export_media.return_value = mock_export

        mock_svc.files.return_value = mock_files

        with patch("src.core.nodes.apps.google_drive._get_drive_service") as mock_get_svc:
            mock_get_svc.return_value = mock_svc

            result = await node.execute(config, {})

            assert result["filename"] == "My Document.pdf"
            assert result["mime_type"] == "application/pdf"

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "google-drive-download"


class TestGoogleDriveCreateFolderNode:
    """Tests for GoogleDriveCreateFolderNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.google_drive import GoogleDriveCreateFolderNode
        return GoogleDriveCreateFolderNode()

    @pytest.mark.asyncio
    async def test_create_folder(self, node):
        """Test creating a folder."""
        config = {
            "credentials_json": '{"type": "service_account"}',
            "folder_name": "New Folder",
        }

        mock_svc = MagicMock()
        mock_files = MagicMock()
        mock_create = MagicMock()
        mock_create.execute.return_value = {
            "id": "folder-id",
            "webViewLink": "https://drive.google.com/drive/folders/folder-id",
        }
        mock_files.create.return_value = mock_create
        mock_svc.files.return_value = mock_files

        with patch("src.core.nodes.apps.google_drive._get_drive_service") as mock_get:
            mock_get.return_value = mock_svc

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["folder_id"] == "folder-id"

            # Verify folder metadata was set correctly
            call_args = mock_files.create.call_args
            body = call_args[1]["body"]
            assert body["name"] == "New Folder"
            assert body["mimeType"] == "application/vnd.google-apps.folder"

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "google-drive-create-folder"


class TestGoogleDriveDeleteNode:
    """Tests for GoogleDriveDeleteNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.google_drive import GoogleDriveDeleteNode
        return GoogleDriveDeleteNode()

    @pytest.mark.asyncio
    async def test_move_to_trash(self, node):
        """Test moving file to trash."""
        config = {
            "credentials_json": '{"type": "service_account"}',
            "file_id": "file123",
            "trash": True,
        }

        mock_svc = MagicMock()
        mock_files = MagicMock()
        mock_update = MagicMock()
        mock_update.execute.return_value = {}
        mock_files.update.return_value = mock_update
        mock_svc.files.return_value = mock_files

        with patch("src.core.nodes.apps.google_drive._get_drive_service") as mock_get:
            mock_get.return_value = mock_svc

            result = await node.execute(config, {})

            assert result["success"] is True

            # Verify update was called with trashed=True
            call_args = mock_files.update.call_args
            assert call_args[1]["body"]["trashed"] is True

    @pytest.mark.asyncio
    async def test_permanent_delete(self, node):
        """Test permanent deletion."""
        config = {
            "credentials_json": '{"type": "service_account"}',
            "file_id": "file123",
            "trash": False,
        }

        mock_svc = MagicMock()
        mock_files = MagicMock()
        mock_delete = MagicMock()
        mock_delete.execute.return_value = None
        mock_files.delete.return_value = mock_delete
        mock_svc.files.return_value = mock_files

        with patch("src.core.nodes.apps.google_drive._get_drive_service") as mock_get:
            mock_get.return_value = mock_svc

            result = await node.execute(config, {})

            assert result["success"] is True
            mock_files.delete.assert_called_once_with(fileId="file123")

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "google-drive-delete"


# ============================================================================
# Microsoft Teams Node Tests
# ============================================================================

class TestTeamsSendMessageNode:
    """Tests for TeamsSendMessageNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.teams import TeamsSendMessageNode
        return TeamsSendMessageNode()

    @pytest.mark.asyncio
    async def test_send_channel_message_success(self, node):
        """Test sending message to a channel."""
        config = {
            "access_token": "test-token",
            "destination_type": "channel",
            "team_id": "team123",
            "channel_id": "channel456",
            "message": "Hello Teams!",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "msg123",
                "webUrl": "https://teams.microsoft.com/...",
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["message_id"] == "msg123"

    @pytest.mark.asyncio
    async def test_send_chat_message_success(self, node):
        """Test sending message to a chat."""
        config = {
            "access_token": "test-token",
            "destination_type": "chat",
            "chat_id": "chat789",
            "message": "Hello!",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "msg456"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_missing_token_raises_error(self, node):
        """Test that missing token raises error."""
        config = {
            "destination_type": "channel",
            "team_id": "team123",
            "channel_id": "channel456",
            "message": "Hello!",
        }

        with pytest.raises(ValueError, match="Access token required"):
            await node.execute(config, {})

    @pytest.mark.asyncio
    async def test_channel_missing_ids_raises_error(self, node):
        """Test that missing team/channel IDs raises error."""
        config = {
            "access_token": "test-token",
            "destination_type": "channel",
            "message": "Hello!",
        }

        with pytest.raises(ValueError, match="Team ID and Channel ID are required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "teams-send-message"
        assert node.category == "Apps"


class TestTeamsListTeamsNode:
    """Tests for TeamsListTeamsNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.teams import TeamsListTeamsNode
        return TeamsListTeamsNode()

    @pytest.mark.asyncio
    async def test_list_teams_success(self, node):
        """Test listing user's teams."""
        config = {"access_token": "test-token"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "value": [
                    {"id": "team1", "displayName": "Team One"},
                    {"id": "team2", "displayName": "Team Two"},
                ]
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 2
            assert len(result["teams"]) == 2

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "teams-list-teams"


class TestTeamsListChannelsNode:
    """Tests for TeamsListChannelsNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.teams import TeamsListChannelsNode
        return TeamsListChannelsNode()

    @pytest.mark.asyncio
    async def test_list_channels_success(self, node):
        """Test listing team channels."""
        config = {
            "access_token": "test-token",
            "team_id": "team123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "value": [
                    {"id": "ch1", "displayName": "General"},
                    {"id": "ch2", "displayName": "Random"},
                ]
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 2

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "teams-list-channels"


class TestTeamsGetMessagesNode:
    """Tests for TeamsGetMessagesNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.teams import TeamsGetMessagesNode
        return TeamsGetMessagesNode()

    @pytest.mark.asyncio
    async def test_get_channel_messages(self, node):
        """Test getting messages from a channel."""
        config = {
            "access_token": "test-token",
            "source_type": "channel",
            "team_id": "team123",
            "channel_id": "channel456",
            "limit": 10,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "value": [
                    {"id": "msg1", "body": {"content": "Hello"}},
                    {"id": "msg2", "body": {"content": "World"}},
                ]
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 2
            assert len(result["messages"]) == 2

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "teams-get-messages"


class TestTeamsCreateMeetingNode:
    """Tests for TeamsCreateMeetingNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.teams import TeamsCreateMeetingNode
        return TeamsCreateMeetingNode()

    @pytest.mark.asyncio
    async def test_create_meeting_success(self, node):
        """Test creating a meeting."""
        config = {
            "access_token": "test-token",
            "subject": "Team Standup",
            "start_time": "2024-01-15T09:00:00",
            "end_time": "2024-01-15T09:30:00",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "meeting123",
                "joinWebUrl": "https://teams.microsoft.com/l/meetup-join/...",
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["meeting_id"] == "meeting123"
            assert "teams.microsoft.com" in result["join_url"]

    @pytest.mark.asyncio
    async def test_create_meeting_with_attendees(self, node):
        """Test creating a meeting with attendees."""
        config = {
            "access_token": "test-token",
            "subject": "Project Review",
            "start_time": "2024-01-15T14:00:00",
            "end_time": "2024-01-15T15:00:00",
            "attendees": "user1@example.com, user2@example.com",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "mtg456", "joinWebUrl": ""}
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await node.execute(config, {})

            # Verify attendees were included in request
            call_args = mock_post.call_args
            body = call_args[1]["json"]
            assert "participants" in body
            assert len(body["participants"]["attendees"]) == 2

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "teams-create-meeting"


# ============================================================================
# Dropbox Node Tests
# ============================================================================

class TestDropboxListNode:
    """Tests for DropboxListNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.dropbox import DropboxListNode
        return DropboxListNode()

    @pytest.mark.asyncio
    async def test_list_files_success(self, node):
        """Test listing files successfully."""
        config = {
            "access_token": "test-token",
            "path": "",
            "recursive": False,
            "limit": 100,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "entries": [
                    {
                        "name": "document.pdf",
                        "path_display": "/document.pdf",
                        ".tag": "file",
                        "size": 1024,
                        "client_modified": "2024-01-15T10:00:00Z",
                        "id": "id:abc123",
                    },
                    {
                        "name": "Photos",
                        "path_display": "/Photos",
                        ".tag": "folder",
                        "id": "id:def456",
                    },
                ],
                "has_more": False,
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 2
            assert len(result["entries"]) == 2
            assert result["entries"][0]["name"] == "document.pdf"
            assert result["entries"][0]["type"] == "file"
            assert result["entries"][1]["type"] == "folder"
            assert result["has_more"] is False

    @pytest.mark.asyncio
    async def test_list_files_empty(self, node):
        """Test listing when folder is empty."""
        config = {"access_token": "test-token", "path": "/empty-folder"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "entries": [],
                "has_more": False,
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 0
            assert result["entries"] == []

    @pytest.mark.asyncio
    async def test_missing_token_raises_error(self, node):
        """Test that missing token raises error."""
        config = {"path": "/test"}

        with pytest.raises(ValueError, match="Access token required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "dropbox-list"
        assert node.category == "Apps"
        assert node.color == "#0061FF"


class TestDropboxDownloadNode:
    """Tests for DropboxDownloadNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.dropbox import DropboxDownloadNode
        return DropboxDownloadNode()

    @pytest.mark.asyncio
    async def test_download_success(self, node):
        """Test downloading file successfully."""
        config = {
            "access_token": "test-token",
            "path": "/document.txt",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"Hello, World!"
            mock_response.headers = {
                "Dropbox-API-Result": '{"name": "document.txt", "size": 13}'
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["filename"] == "document.txt"
            assert result["size"] == 13

    @pytest.mark.asyncio
    async def test_download_failure(self, node):
        """Test handling download failure."""
        config = {"access_token": "test-token", "path": "/nonexistent.txt"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False
            assert result["content"] == ""

    @pytest.mark.asyncio
    async def test_missing_path_raises_error(self, node):
        """Test that missing path raises error."""
        config = {"access_token": "test-token", "path": ""}

        with pytest.raises(ValueError, match="File path is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "dropbox-download"


class TestDropboxUploadNode:
    """Tests for DropboxUploadNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.dropbox import DropboxUploadNode
        return DropboxUploadNode()

    @pytest.mark.asyncio
    async def test_upload_text_success(self, node):
        """Test uploading text file successfully."""
        config = {
            "access_token": "test-token",
            "path": "/uploads/test.txt",
            "content": "Hello, Dropbox!",
            "is_base64": False,
            "mode": "add",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "path_display": "/uploads/test.txt",
                "id": "id:xyz789",
                "size": 15,
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["path"] == "/uploads/test.txt"
            assert result["id"] == "id:xyz789"

    @pytest.mark.asyncio
    async def test_upload_base64_content(self, node):
        """Test uploading base64 encoded content."""
        import base64
        content = base64.b64encode(b"Binary content").decode()

        config = {
            "access_token": "test-token",
            "path": "/binary.dat",
            "content": content,
            "is_base64": True,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "path_display": "/binary.dat",
                "id": "id:bin123",
            }
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await node.execute(config, {})

            assert result["success"] is True
            # Verify binary content was decoded
            call_args = mock_post.call_args
            assert call_args[1]["content"] == b"Binary content"

    @pytest.mark.asyncio
    async def test_upload_failure(self, node):
        """Test handling upload failure."""
        config = {
            "access_token": "test-token",
            "path": "/test.txt",
            "content": "Test",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 409  # Conflict
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "dropbox-upload"


class TestDropboxCreateFolderNode:
    """Tests for DropboxCreateFolderNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.dropbox import DropboxCreateFolderNode
        return DropboxCreateFolderNode()

    @pytest.mark.asyncio
    async def test_create_folder_success(self, node):
        """Test creating folder successfully."""
        config = {
            "access_token": "test-token",
            "path": "/New Folder",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "metadata": {
                    "path_display": "/New Folder",
                    "id": "id:folder123",
                }
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["path"] == "/New Folder"
            assert result["id"] == "id:folder123"

    @pytest.mark.asyncio
    async def test_create_folder_failure(self, node):
        """Test handling folder creation failure (already exists)."""
        config = {"access_token": "test-token", "path": "/Existing Folder"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 409
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_missing_path_raises_error(self, node):
        """Test that missing path raises error."""
        config = {"access_token": "test-token", "path": ""}

        with pytest.raises(ValueError, match="Folder path is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "dropbox-create-folder"


class TestDropboxDeleteNode:
    """Tests for DropboxDeleteNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.dropbox import DropboxDeleteNode
        return DropboxDeleteNode()

    @pytest.mark.asyncio
    async def test_delete_success(self, node):
        """Test deleting file successfully."""
        config = {
            "access_token": "test-token",
            "path": "/old-file.txt",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "metadata": {"path_display": "/old-file.txt"}
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["deleted_path"] == "/old-file.txt"

    @pytest.mark.asyncio
    async def test_delete_failure(self, node):
        """Test handling delete failure (not found)."""
        config = {"access_token": "test-token", "path": "/nonexistent.txt"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_missing_path_raises_error(self, node):
        """Test that missing path raises error."""
        config = {"access_token": "test-token", "path": ""}

        with pytest.raises(ValueError, match="Path is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "dropbox-delete"


class TestDropboxGetLinkNode:
    """Tests for DropboxGetLinkNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.dropbox import DropboxGetLinkNode
        return DropboxGetLinkNode()

    @pytest.mark.asyncio
    async def test_create_share_link_success(self, node):
        """Test creating share link successfully."""
        config = {
            "access_token": "test-token",
            "path": "/shared-doc.pdf",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "url": "https://www.dropbox.com/s/abc123/shared-doc.pdf?dl=0"
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert "dropbox.com" in result["url"]

    @pytest.mark.asyncio
    async def test_get_existing_link(self, node):
        """Test getting existing share link when one already exists."""
        config = {"access_token": "test-token", "path": "/already-shared.pdf"}

        with patch("httpx.AsyncClient") as mock_client:
            # First call returns 409 (link exists)
            mock_create_response = MagicMock()
            mock_create_response.status_code = 409

            # Second call returns existing links
            mock_list_response = MagicMock()
            mock_list_response.status_code = 200
            mock_list_response.json.return_value = {
                "links": [{"url": "https://www.dropbox.com/s/existing/file?dl=0"}]
            }

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=[mock_create_response, mock_list_response]
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert "existing" in result["url"]

    @pytest.mark.asyncio
    async def test_get_link_failure(self, node):
        """Test handling failure when no link can be created/found."""
        config = {"access_token": "test-token", "path": "/problem-file.txt"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 403  # Forbidden
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False
            assert result["url"] == ""

    @pytest.mark.asyncio
    async def test_missing_path_raises_error(self, node):
        """Test that missing path raises error."""
        config = {"access_token": "test-token", "path": ""}

        with pytest.raises(ValueError, match="Path is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "dropbox-get-link"


# ============================================================================
# MySQL Node Tests
# ============================================================================

class TestMySQLQueryNode:
    """Tests for MySQLQueryNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.database import MySQLQueryNode
        return MySQLQueryNode()

    @pytest.fixture
    def config(self):
        return {
            "host": "localhost",
            "port": 3306,
            "database": "testdb",
            "username": "testuser",
            "password": "testpass",
            "query": "SELECT * FROM users",
            "operation": "fetch",
        }

    @pytest.fixture
    def mock_aiomysql(self):
        """Create mock aiomysql module."""
        mock_module = MagicMock()
        mock_module.DictCursor = MagicMock()
        return mock_module

    @pytest.mark.asyncio
    async def test_fetch_query_success(self, node, config, mock_aiomysql):
        """Test fetching rows from MySQL."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Setup async cursor context
        mock_cursor.fetchall = AsyncMock(return_value=[
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ])
        mock_cursor.execute = AsyncMock()
        mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor.__aexit__ = AsyncMock(return_value=None)

        mock_conn.cursor.return_value = mock_cursor
        mock_conn.close = MagicMock()

        mock_aiomysql.connect = AsyncMock(return_value=mock_conn)

        with patch.dict("sys.modules", {"aiomysql": mock_aiomysql}):
            result = await node.execute(config, {})

        assert result["row_count"] == 2
        assert len(result["rows"]) == 2
        assert result["rows"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_fetchone_operation(self, node, config, mock_aiomysql):
        """Test fetching single row."""
        config["operation"] = "fetchone"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_cursor.fetchone = AsyncMock(return_value={"id": 1, "name": "Alice"})
        mock_cursor.execute = AsyncMock()
        mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor.__aexit__ = AsyncMock(return_value=None)

        mock_conn.cursor.return_value = mock_cursor
        mock_conn.close = MagicMock()

        mock_aiomysql.connect = AsyncMock(return_value=mock_conn)

        with patch.dict("sys.modules", {"aiomysql": mock_aiomysql}):
            result = await node.execute(config, {})

        assert result["row_count"] == 1
        assert result["rows"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_execute_operation(self, node, config, mock_aiomysql):
        """Test execute operation (INSERT/UPDATE/DELETE)."""
        config["operation"] = "execute"
        config["query"] = "INSERT INTO users (name) VALUES (%s)"
        config["parameters"] = '["Charlie"]'

        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_cursor.execute = AsyncMock()
        mock_cursor.rowcount = 1
        mock_cursor.lastrowid = 3
        mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor.__aexit__ = AsyncMock(return_value=None)

        mock_conn.cursor.return_value = mock_cursor
        mock_conn.close = MagicMock()

        mock_aiomysql.connect = AsyncMock(return_value=mock_conn)

        with patch.dict("sys.modules", {"aiomysql": mock_aiomysql}):
            result = await node.execute(config, {})

        assert result["row_count"] == 1
        assert result["last_id"] == 3

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "mysql-query"
        assert node.color == "#4479A1"

    def test_node_inputs(self, node):
        """Test node has required inputs."""
        input_names = [i.name for i in node.inputs]
        assert "host" in input_names
        assert "database" in input_names
        assert "username" in input_names
        assert "password" in input_names
        assert "query" in input_names


# ============================================================================
# MongoDB Node Tests
# ============================================================================

class TestMongoDBQueryNode:
    """Tests for MongoDBQueryNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.database import MongoDBQueryNode
        return MongoDBQueryNode()

    @pytest.fixture
    def config(self):
        return {
            "connection_string": "mongodb://localhost:27017",
            "database": "testdb",
            "collection": "users",
            "operation": "find",
            "query": "{}",
            "limit": 100,
        }

    @pytest.fixture
    def mock_motor(self):
        """Create mock motor module."""
        mock_motor_asyncio = MagicMock()
        mock_motor = MagicMock()
        mock_motor.motor_asyncio = mock_motor_asyncio
        return mock_motor, mock_motor_asyncio

    @pytest.mark.asyncio
    async def test_find_documents(self, node, config, mock_motor):
        """Test finding documents in MongoDB."""
        mock_motor_mod, mock_motor_asyncio = mock_motor

        # Create mock documents
        mock_docs = [
            {"_id": "abc123", "name": "Alice"},
            {"_id": "def456", "name": "Bob"},
        ]

        # Setup mock cursor
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        # Make cursor async iterable
        async def async_iter():
            for doc in mock_docs:
                yield doc

        mock_cursor.__aiter__ = lambda self: async_iter()

        mock_collection = MagicMock()
        mock_collection.find.return_value = mock_cursor

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_client_instance.close = MagicMock()

        mock_motor_asyncio.AsyncIOMotorClient.return_value = mock_client_instance

        with patch.dict("sys.modules", {"motor": mock_motor_mod, "motor.motor_asyncio": mock_motor_asyncio}):
            result = await node.execute(config, {})

        assert result["count"] == 2
        assert len(result["documents"]) == 2
        assert result["documents"][0]["name"] == "Alice"
        # _id should be converted to string
        assert result["documents"][0]["_id"] == "abc123"

    @pytest.mark.asyncio
    async def test_find_one_document(self, node, config, mock_motor):
        """Test finding single document."""
        config["operation"] = "find_one"
        config["query"] = '{"name": "Alice"}'

        mock_motor_mod, mock_motor_asyncio = mock_motor
        mock_doc = {"_id": "abc123", "name": "Alice"}

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=mock_doc)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_client_instance.close = MagicMock()

        mock_motor_asyncio.AsyncIOMotorClient.return_value = mock_client_instance

        with patch.dict("sys.modules", {"motor": mock_motor_mod, "motor.motor_asyncio": mock_motor_asyncio}):
            result = await node.execute(config, {})

        assert result["count"] == 1
        assert result["documents"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_count_documents(self, node, config, mock_motor):
        """Test counting documents."""
        config["operation"] = "count"

        mock_motor_mod, mock_motor_asyncio = mock_motor

        mock_collection = MagicMock()
        mock_collection.count_documents = AsyncMock(return_value=42)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_client_instance.close = MagicMock()

        mock_motor_asyncio.AsyncIOMotorClient.return_value = mock_client_instance

        with patch.dict("sys.modules", {"motor": mock_motor_mod, "motor.motor_asyncio": mock_motor_asyncio}):
            result = await node.execute(config, {})

        assert result["count"] == 42
        assert result["documents"] == []

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "mongodb-query"
        assert node.color == "#47A248"

    def test_node_inputs(self, node):
        """Test node has required inputs."""
        input_names = [i.name for i in node.inputs]
        assert "connection_string" in input_names
        assert "database" in input_names
        assert "collection" in input_names
        assert "operation" in input_names


class TestMongoDBWriteNode:
    """Tests for MongoDBWriteNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.database import MongoDBWriteNode
        return MongoDBWriteNode()

    @pytest.fixture
    def config(self):
        return {
            "connection_string": "mongodb://localhost:27017",
            "database": "testdb",
            "collection": "users",
            "operation": "insert_one",
            "document": '{"name": "Alice"}',
        }

    @pytest.fixture
    def mock_motor(self):
        """Create mock motor module."""
        mock_motor_asyncio = MagicMock()
        mock_motor = MagicMock()
        mock_motor.motor_asyncio = mock_motor_asyncio
        return mock_motor, mock_motor_asyncio

    @pytest.mark.asyncio
    async def test_insert_one(self, node, config, mock_motor):
        """Test inserting single document."""
        mock_motor_mod, mock_motor_asyncio = mock_motor

        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_result.inserted_id = "new_id_123"

        mock_collection = MagicMock()
        mock_collection.insert_one = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_client_instance.close = MagicMock()

        mock_motor_asyncio.AsyncIOMotorClient.return_value = mock_client_instance

        with patch.dict("sys.modules", {"motor": mock_motor_mod, "motor.motor_asyncio": mock_motor_asyncio}):
            result = await node.execute(config, {})

        assert result["success"] is True
        assert result["inserted_id"] == "new_id_123"

    @pytest.mark.asyncio
    async def test_update_one(self, node, config, mock_motor):
        """Test updating single document."""
        config["operation"] = "update_one"
        config["filter"] = '{"name": "Alice"}'
        config["document"] = '{"$set": {"age": 30}}'

        mock_motor_mod, mock_motor_asyncio = mock_motor

        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_result.matched_count = 1
        mock_result.modified_count = 1
        mock_result.upserted_id = None

        mock_collection = MagicMock()
        mock_collection.update_one = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_client_instance.close = MagicMock()

        mock_motor_asyncio.AsyncIOMotorClient.return_value = mock_client_instance

        with patch.dict("sys.modules", {"motor": mock_motor_mod, "motor.motor_asyncio": mock_motor_asyncio}):
            result = await node.execute(config, {})

        assert result["success"] is True
        assert result["matched_count"] == 1
        assert result["modified_count"] == 1

    @pytest.mark.asyncio
    async def test_delete_one(self, node, config, mock_motor):
        """Test deleting single document."""
        config["operation"] = "delete_one"
        config["filter"] = '{"name": "Alice"}'

        mock_motor_mod, mock_motor_asyncio = mock_motor

        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_result.deleted_count = 1

        mock_collection = MagicMock()
        mock_collection.delete_one = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_client_instance.close = MagicMock()

        mock_motor_asyncio.AsyncIOMotorClient.return_value = mock_client_instance

        with patch.dict("sys.modules", {"motor": mock_motor_mod, "motor.motor_asyncio": mock_motor_asyncio}):
            result = await node.execute(config, {})

        assert result["success"] is True
        assert result["deleted_count"] == 1

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "mongodb-write"
        assert node.color == "#47A248"

    def test_node_inputs(self, node):
        """Test node has required inputs."""
        input_names = [i.name for i in node.inputs]
        assert "operation" in input_names
        assert "filter" in input_names
        assert "document" in input_names
        assert "upsert" in input_names


# ============================================================================
# Trello Node Tests
# ============================================================================

class TestTrelloListBoardsNode:
    """Tests for TrelloListBoardsNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.trello import TrelloListBoardsNode
        return TrelloListBoardsNode()

    @pytest.mark.asyncio
    async def test_list_boards_success(self, node):
        """Test listing boards successfully."""
        config = {
            "api_key": "test-key",
            "token": "test-token",
            "filter": "all",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"id": "board1", "name": "Project Alpha"},
                {"id": "board2", "name": "Project Beta"},
            ]
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 2
            assert len(result["boards"]) == 2
            assert result["boards"][0]["name"] == "Project Alpha"

    @pytest.mark.asyncio
    async def test_missing_credentials_raises_error(self, node):
        """Test that missing credentials raises error."""
        config = {"filter": "all"}

        with pytest.raises(ValueError, match="API key and token required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "trello-list-boards"
        assert node.color == "#0079BF"


class TestTrelloListListsNode:
    """Tests for TrelloListListsNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.trello import TrelloListListsNode
        return TrelloListListsNode()

    @pytest.mark.asyncio
    async def test_list_lists_success(self, node):
        """Test listing lists in a board."""
        config = {
            "api_key": "test-key",
            "token": "test-token",
            "board_id": "board123",
            "filter": "open",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"id": "list1", "name": "To Do"},
                {"id": "list2", "name": "In Progress"},
                {"id": "list3", "name": "Done"},
            ]
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 3
            assert result["lists"][1]["name"] == "In Progress"

    @pytest.mark.asyncio
    async def test_missing_board_id_raises_error(self, node):
        """Test that missing board ID raises error."""
        config = {"api_key": "test-key", "token": "test-token"}

        with pytest.raises(ValueError, match="Board ID is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "trello-list-lists"


class TestTrelloListCardsNode:
    """Tests for TrelloListCardsNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.trello import TrelloListCardsNode
        return TrelloListCardsNode()

    @pytest.mark.asyncio
    async def test_list_cards_from_list(self, node):
        """Test listing cards from a list."""
        config = {
            "api_key": "test-key",
            "token": "test-token",
            "source_type": "list",
            "list_id": "list123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"id": "card1", "name": "Task 1", "desc": "Description"},
                {"id": "card2", "name": "Task 2", "desc": ""},
            ]
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 2
            assert result["cards"][0]["name"] == "Task 1"

    @pytest.mark.asyncio
    async def test_list_cards_from_board(self, node):
        """Test listing cards from entire board."""
        config = {
            "api_key": "test-key",
            "token": "test-token",
            "source_type": "board",
            "board_id": "board123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"id": "card1", "name": "Task 1"},
            ]
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 1

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "trello-list-cards"


class TestTrelloCreateCardNode:
    """Tests for TrelloCreateCardNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.trello import TrelloCreateCardNode
        return TrelloCreateCardNode()

    @pytest.mark.asyncio
    async def test_create_card_success(self, node):
        """Test creating a card successfully."""
        config = {
            "api_key": "test-key",
            "token": "test-token",
            "list_id": "list123",
            "name": "New Task",
            "description": "Task description",
            "position": "top",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "card-new-123",
                "name": "New Task",
                "url": "https://trello.com/c/abc123",
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["card_id"] == "card-new-123"
            assert "trello.com" in result["card_url"]

    @pytest.mark.asyncio
    async def test_missing_list_id_raises_error(self, node):
        """Test that missing list ID raises error."""
        config = {"api_key": "test-key", "token": "test-token", "name": "Task"}

        with pytest.raises(ValueError, match="List ID is required"):
            await node.execute(config, {})

    @pytest.mark.asyncio
    async def test_missing_name_raises_error(self, node):
        """Test that missing name raises error."""
        config = {"api_key": "test-key", "token": "test-token", "list_id": "list123"}

        with pytest.raises(ValueError, match="Card name is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "trello-create-card"


class TestTrelloUpdateCardNode:
    """Tests for TrelloUpdateCardNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.trello import TrelloUpdateCardNode
        return TrelloUpdateCardNode()

    @pytest.mark.asyncio
    async def test_update_card_success(self, node):
        """Test updating a card successfully."""
        config = {
            "api_key": "test-key",
            "token": "test-token",
            "card_id": "card123",
            "name": "Updated Task Name",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "card123",
                "name": "Updated Task Name",
            }
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["card"]["name"] == "Updated Task Name"

    @pytest.mark.asyncio
    async def test_move_card_to_list(self, node):
        """Test moving card to different list."""
        config = {
            "api_key": "test-key",
            "token": "test-token",
            "card_id": "card123",
            "list_id": "new-list-456",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "card123",
                "idList": "new-list-456",
            }
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_missing_card_id_raises_error(self, node):
        """Test that missing card ID raises error."""
        config = {"api_key": "test-key", "token": "test-token"}

        with pytest.raises(ValueError, match="Card ID is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "trello-update-card"


class TestTrelloDeleteCardNode:
    """Tests for TrelloDeleteCardNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.trello import TrelloDeleteCardNode
        return TrelloDeleteCardNode()

    @pytest.mark.asyncio
    async def test_delete_card_success(self, node):
        """Test deleting a card successfully."""
        config = {
            "api_key": "test-key",
            "token": "test-token",
            "card_id": "card123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.delete = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_card_failure(self, node):
        """Test handling delete failure."""
        config = {
            "api_key": "test-key",
            "token": "test-token",
            "card_id": "nonexistent",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.delete = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "trello-delete-card"


class TestTrelloAddCommentNode:
    """Tests for TrelloAddCommentNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.trello import TrelloAddCommentNode
        return TrelloAddCommentNode()

    @pytest.mark.asyncio
    async def test_add_comment_success(self, node):
        """Test adding a comment successfully."""
        config = {
            "api_key": "test-key",
            "token": "test-token",
            "card_id": "card123",
            "text": "This is a comment",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "comment-xyz",
                "data": {"text": "This is a comment"},
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["comment_id"] == "comment-xyz"

    @pytest.mark.asyncio
    async def test_missing_text_raises_error(self, node):
        """Test that missing text raises error."""
        config = {"api_key": "test-key", "token": "test-token", "card_id": "card123"}

        with pytest.raises(ValueError, match="Comment text is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "trello-add-comment"


# ============================================================================
# Airtable Node Tests
# ============================================================================

class TestAirtableListBasesNode:
    """Tests for AirtableListBasesNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.airtable import AirtableListBasesNode
        return AirtableListBasesNode()

    @pytest.mark.asyncio
    async def test_list_bases_success(self, node):
        """Test listing bases successfully."""
        config = {"api_key": "pat-test-key"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "bases": [
                    {"id": "appABC123", "name": "Project Tracker"},
                    {"id": "appDEF456", "name": "Customer CRM"},
                ]
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 2
            assert len(result["bases"]) == 2
            assert result["bases"][0]["name"] == "Project Tracker"

    @pytest.mark.asyncio
    async def test_list_bases_empty(self, node):
        """Test listing when no bases."""
        config = {"api_key": "pat-test-key"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"bases": []}
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 0
            assert result["bases"] == []

    @pytest.mark.asyncio
    async def test_missing_api_key_raises_error(self, node):
        """Test that missing API key raises error."""
        config = {}

        with pytest.raises(ValueError, match="API key required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "airtable-list-bases"
        assert node.color == "#18BFFF"


class TestAirtableListRecordsNode:
    """Tests for AirtableListRecordsNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.airtable import AirtableListRecordsNode
        return AirtableListRecordsNode()

    @pytest.mark.asyncio
    async def test_list_records_success(self, node):
        """Test listing records successfully."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "records": [
                    {"id": "recXYZ1", "fields": {"Name": "Task 1", "Status": "Done"}},
                    {"id": "recXYZ2", "fields": {"Name": "Task 2", "Status": "In Progress"}},
                ]
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 2
            assert len(result["records"]) == 2
            assert result["records"][0]["fields"]["Name"] == "Task 1"

    @pytest.mark.asyncio
    async def test_list_records_with_filter(self, node):
        """Test listing records with filter formula."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
            "filter_formula": "Status = 'Done'",
            "max_records": 50,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "records": [
                    {"id": "recXYZ1", "fields": {"Name": "Task 1", "Status": "Done"}},
                ]
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_missing_base_id_raises_error(self, node):
        """Test that missing base ID raises error."""
        config = {"api_key": "pat-test-key", "table_name": "Tasks"}

        with pytest.raises(ValueError, match="Base ID is required"):
            await node.execute(config, {})

    @pytest.mark.asyncio
    async def test_missing_table_name_raises_error(self, node):
        """Test that missing table name raises error."""
        config = {"api_key": "pat-test-key", "base_id": "appABC123"}

        with pytest.raises(ValueError, match="Table name is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "airtable-list-records"


class TestAirtableGetRecordNode:
    """Tests for AirtableGetRecordNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.airtable import AirtableGetRecordNode
        return AirtableGetRecordNode()

    @pytest.mark.asyncio
    async def test_get_record_success(self, node):
        """Test getting a record successfully."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
            "record_id": "recXYZ123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "recXYZ123",
                "fields": {"Name": "Important Task", "Status": "Done"},
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["fields"]["Name"] == "Important Task"

    @pytest.mark.asyncio
    async def test_get_record_not_found(self, node):
        """Test getting a record that doesn't exist."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
            "record_id": "recNONEXIST",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False
            assert result["fields"] == {}

    @pytest.mark.asyncio
    async def test_missing_record_id_raises_error(self, node):
        """Test that missing record ID raises error."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
        }

        with pytest.raises(ValueError, match="Record ID is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "airtable-get-record"


class TestAirtableCreateRecordNode:
    """Tests for AirtableCreateRecordNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.airtable import AirtableCreateRecordNode
        return AirtableCreateRecordNode()

    @pytest.mark.asyncio
    async def test_create_record_success(self, node):
        """Test creating a record successfully."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
            "fields": {"Name": "New Task", "Status": "To Do"},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "recNEW123",
                "fields": {"Name": "New Task", "Status": "To Do"},
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["record_id"] == "recNEW123"

    @pytest.mark.asyncio
    async def test_create_record_with_json_string(self, node):
        """Test creating a record with JSON string fields."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
            "fields": '{"Name": "JSON Task", "Priority": "High"}',
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "recJSON456",
                "fields": {"Name": "JSON Task", "Priority": "High"},
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_record_failure(self, node):
        """Test handling create failure."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
            "fields": {"Name": "Task"},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 422  # Validation error
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False
            assert result["record_id"] == ""

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "airtable-create-record"


class TestAirtableUpdateRecordNode:
    """Tests for AirtableUpdateRecordNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.airtable import AirtableUpdateRecordNode
        return AirtableUpdateRecordNode()

    @pytest.mark.asyncio
    async def test_update_record_success(self, node):
        """Test updating a record successfully."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
            "record_id": "recXYZ123",
            "fields": {"Status": "Done"},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "recXYZ123",
                "fields": {"Name": "Task", "Status": "Done"},
            }
            mock_client.return_value.__aenter__.return_value.patch = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["record"]["fields"]["Status"] == "Done"

    @pytest.mark.asyncio
    async def test_update_record_failure(self, node):
        """Test handling update failure."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
            "record_id": "recNONEXIST",
            "fields": {"Status": "Done"},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.patch = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_missing_record_id_raises_error(self, node):
        """Test that missing record ID raises error."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
            "fields": {"Status": "Done"},
        }

        with pytest.raises(ValueError, match="Record ID is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "airtable-update-record"


class TestAirtableDeleteRecordNode:
    """Tests for AirtableDeleteRecordNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.airtable import AirtableDeleteRecordNode
        return AirtableDeleteRecordNode()

    @pytest.mark.asyncio
    async def test_delete_record_success(self, node):
        """Test deleting a record successfully."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
            "record_id": "recXYZ123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "deleted": True,
                "id": "recXYZ123",
            }
            mock_client.return_value.__aenter__.return_value.delete = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["deleted_id"] == "recXYZ123"

    @pytest.mark.asyncio
    async def test_delete_record_not_found(self, node):
        """Test deleting a record that doesn't exist."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
            "record_id": "recNONEXIST",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.delete = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False
            assert result["deleted_id"] == ""

    @pytest.mark.asyncio
    async def test_missing_record_id_raises_error(self, node):
        """Test that missing record ID raises error."""
        config = {
            "api_key": "pat-test-key",
            "base_id": "appABC123",
            "table_name": "Tasks",
        }

        with pytest.raises(ValueError, match="Record ID is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "airtable-delete-record"


# ============================================================================
# Jira Node Tests
# ============================================================================

class TestJiraListProjectsNode:
    """Tests for JiraListProjectsNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.jira import JiraListProjectsNode
        return JiraListProjectsNode()

    @pytest.mark.asyncio
    async def test_list_projects_success(self, node):
        """Test listing projects successfully."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"id": "10001", "key": "PROJ", "name": "Project Alpha"},
                {"id": "10002", "key": "TEST", "name": "Test Project"},
            ]
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 2
            assert len(result["projects"]) == 2
            assert result["projects"][0]["key"] == "PROJ"

    @pytest.mark.asyncio
    async def test_missing_domain_raises_error(self, node):
        """Test that missing domain raises error."""
        config = {"email": "user@example.com", "api_token": "test-token"}

        with pytest.raises(ValueError, match="Jira domain is required"):
            await node.execute(config, {})

    @pytest.mark.asyncio
    async def test_missing_credentials_raises_error(self, node):
        """Test that missing credentials raises error."""
        config = {"domain": "example.atlassian.net"}

        with pytest.raises(ValueError, match="Email and API token are required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "jira-list-projects"
        assert node.color == "#0052CC"


class TestJiraSearchIssuesNode:
    """Tests for JiraSearchIssuesNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.jira import JiraSearchIssuesNode
        return JiraSearchIssuesNode()

    @pytest.mark.asyncio
    async def test_search_issues_success(self, node):
        """Test searching issues successfully."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "jql": "project = PROJ AND status = Open",
            "max_results": 50,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "issues": [
                    {"key": "PROJ-1", "fields": {"summary": "First issue"}},
                    {"key": "PROJ-2", "fields": {"summary": "Second issue"}},
                ],
                "total": 2,
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 2
            assert result["total"] == 2
            assert result["issues"][0]["key"] == "PROJ-1"

    @pytest.mark.asyncio
    async def test_missing_jql_raises_error(self, node):
        """Test that missing JQL raises error."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
        }

        with pytest.raises(ValueError, match="JQL query is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "jira-search-issues"


class TestJiraGetIssueNode:
    """Tests for JiraGetIssueNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.jira import JiraGetIssueNode
        return JiraGetIssueNode()

    @pytest.mark.asyncio
    async def test_get_issue_success(self, node):
        """Test getting an issue successfully."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "issue_key": "PROJ-123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "key": "PROJ-123",
                "fields": {
                    "summary": "Important bug fix",
                    "status": {"name": "In Progress"},
                },
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["summary"] == "Important bug fix"
            assert result["status"] == "In Progress"

    @pytest.mark.asyncio
    async def test_get_issue_not_found(self, node):
        """Test getting an issue that doesn't exist."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "issue_key": "PROJ-999",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False
            assert result["summary"] == ""

    @pytest.mark.asyncio
    async def test_missing_issue_key_raises_error(self, node):
        """Test that missing issue key raises error."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
        }

        with pytest.raises(ValueError, match="Issue key is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "jira-get-issue"


class TestJiraCreateIssueNode:
    """Tests for JiraCreateIssueNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.jira import JiraCreateIssueNode
        return JiraCreateIssueNode()

    @pytest.mark.asyncio
    async def test_create_issue_success(self, node):
        """Test creating an issue successfully."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "project_key": "PROJ",
            "issue_type": "Task",
            "summary": "New task",
            "description": "Task description",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "10001",
                "key": "PROJ-124",
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["issue_key"] == "PROJ-124"
            assert "example.atlassian.net/browse/PROJ-124" in result["issue_url"]

    @pytest.mark.asyncio
    async def test_create_issue_with_priority(self, node):
        """Test creating an issue with priority."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "project_key": "PROJ",
            "issue_type": "Bug",
            "summary": "Critical bug",
            "priority": "High",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "10002", "key": "PROJ-125"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_missing_project_key_raises_error(self, node):
        """Test that missing project key raises error."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "summary": "New task",
        }

        with pytest.raises(ValueError, match="Project key is required"):
            await node.execute(config, {})

    @pytest.mark.asyncio
    async def test_missing_summary_raises_error(self, node):
        """Test that missing summary raises error."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "project_key": "PROJ",
        }

        with pytest.raises(ValueError, match="Summary is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "jira-create-issue"


class TestJiraUpdateIssueNode:
    """Tests for JiraUpdateIssueNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.jira import JiraUpdateIssueNode
        return JiraUpdateIssueNode()

    @pytest.mark.asyncio
    async def test_update_issue_success(self, node):
        """Test updating an issue successfully."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "issue_key": "PROJ-123",
            "summary": "Updated summary",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["issue_key"] == "PROJ-123"

    @pytest.mark.asyncio
    async def test_update_issue_no_changes(self, node):
        """Test updating an issue with no changes."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "issue_key": "PROJ-123",
        }

        result = await node.execute(config, {})

        assert result["success"] is True
        assert result["issue_key"] == "PROJ-123"

    @pytest.mark.asyncio
    async def test_missing_issue_key_raises_error(self, node):
        """Test that missing issue key raises error."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
        }

        with pytest.raises(ValueError, match="Issue key is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "jira-update-issue"


class TestJiraAddCommentNode:
    """Tests for JiraAddCommentNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.jira import JiraAddCommentNode
        return JiraAddCommentNode()

    @pytest.mark.asyncio
    async def test_add_comment_success(self, node):
        """Test adding a comment successfully."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "issue_key": "PROJ-123",
            "comment": "This is a test comment",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "comment-123"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["comment_id"] == "comment-123"

    @pytest.mark.asyncio
    async def test_missing_comment_raises_error(self, node):
        """Test that missing comment raises error."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "issue_key": "PROJ-123",
        }

        with pytest.raises(ValueError, match="Comment text is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "jira-add-comment"


class TestJiraTransitionIssueNode:
    """Tests for JiraTransitionIssueNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.jira import JiraTransitionIssueNode
        return JiraTransitionIssueNode()

    @pytest.mark.asyncio
    async def test_transition_issue_success(self, node):
        """Test transitioning an issue successfully."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "issue_key": "PROJ-123",
            "transition_id": "21",  # e.g., "Done"
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["issue_key"] == "PROJ-123"

    @pytest.mark.asyncio
    async def test_transition_with_comment(self, node):
        """Test transitioning an issue with a comment."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "issue_key": "PROJ-123",
            "transition_id": "31",
            "comment": "Moving to done",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_missing_transition_id_raises_error(self, node):
        """Test that missing transition ID raises error."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "issue_key": "PROJ-123",
        }

        with pytest.raises(ValueError, match="Transition ID is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "jira-transition-issue"


class TestJiraGetTransitionsNode:
    """Tests for JiraGetTransitionsNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.jira import JiraGetTransitionsNode
        return JiraGetTransitionsNode()

    @pytest.mark.asyncio
    async def test_get_transitions_success(self, node):
        """Test getting transitions successfully."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
            "issue_key": "PROJ-123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "transitions": [
                    {"id": "11", "name": "To Do"},
                    {"id": "21", "name": "In Progress"},
                    {"id": "31", "name": "Done"},
                ]
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 3
            assert len(result["transitions"]) == 3
            assert result["transitions"][1]["name"] == "In Progress"

    @pytest.mark.asyncio
    async def test_missing_issue_key_raises_error(self, node):
        """Test that missing issue key raises error."""
        config = {
            "domain": "example.atlassian.net",
            "email": "user@example.com",
            "api_token": "test-token",
        }

        with pytest.raises(ValueError, match="Issue key is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "jira-get-transitions"


# ============================================================================
# Twilio Node Tests
# ============================================================================

class TestTwilioSendSMSNode:
    """Tests for TwilioSendSMSNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.twilio import TwilioSendSMSNode
        return TwilioSendSMSNode()

    @pytest.mark.asyncio
    async def test_send_sms_success(self, node):
        """Test sending SMS successfully."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "from_number": "+15551234567",
            "to_number": "+15559876543",
            "body": "Hello from Skynette!",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "sid": "SM123456",
                "status": "queued",
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["message_sid"] == "SM123456"
            assert result["status"] == "queued"

    @pytest.mark.asyncio
    async def test_send_sms_with_media(self, node):
        """Test sending MMS with media."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "from_number": "+15551234567",
            "to_number": "+15559876543",
            "body": "Check this out!",
            "media_url": "https://example.com/image.jpg",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"sid": "MM789", "status": "queued"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_missing_credentials_raises_error(self, node):
        """Test that missing credentials raises error."""
        config = {
            "from_number": "+15551234567",
            "to_number": "+15559876543",
            "body": "Hello!",
        }

        with pytest.raises(ValueError, match="Account SID and Auth Token are required"):
            await node.execute(config, {})

    @pytest.mark.asyncio
    async def test_missing_body_raises_error(self, node):
        """Test that missing body raises error."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "from_number": "+15551234567",
            "to_number": "+15559876543",
        }

        with pytest.raises(ValueError, match="Message body is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "twilio-send-sms"
        assert node.color == "#F22F46"


class TestTwilioSendWhatsAppNode:
    """Tests for TwilioSendWhatsAppNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.twilio import TwilioSendWhatsAppNode
        return TwilioSendWhatsAppNode()

    @pytest.mark.asyncio
    async def test_send_whatsapp_success(self, node):
        """Test sending WhatsApp message successfully."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "from_number": "+14155238886",
            "to_number": "+15559876543",
            "body": "Hello from WhatsApp!",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "sid": "SM456789",
                "status": "queued",
            }
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await node.execute(config, {})

            assert result["success"] is True
            # Verify whatsapp: prefix was added
            call_args = mock_post.call_args
            data = call_args[1]["data"]
            assert data["From"].startswith("whatsapp:")
            assert data["To"].startswith("whatsapp:")

    @pytest.mark.asyncio
    async def test_whatsapp_preserves_prefix(self, node):
        """Test that existing whatsapp: prefix is preserved."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "from_number": "whatsapp:+14155238886",
            "to_number": "whatsapp:+15559876543",
            "body": "Test message",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"sid": "SM123", "status": "queued"}
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await node.execute(config, {})

            call_args = mock_post.call_args
            data = call_args[1]["data"]
            # Should not double-prefix
            assert data["From"] == "whatsapp:+14155238886"

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "twilio-send-whatsapp"


class TestTwilioGetMessageNode:
    """Tests for TwilioGetMessageNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.twilio import TwilioGetMessageNode
        return TwilioGetMessageNode()

    @pytest.mark.asyncio
    async def test_get_message_success(self, node):
        """Test getting message details successfully."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "message_sid": "SM123456",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "sid": "SM123456",
                "status": "delivered",
                "body": "Hello!",
                "from": "+15551234567",
                "to": "+15559876543",
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["status"] == "delivered"
            assert result["body"] == "Hello!"

    @pytest.mark.asyncio
    async def test_get_message_not_found(self, node):
        """Test getting a message that doesn't exist."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "message_sid": "SM999999",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_missing_message_sid_raises_error(self, node):
        """Test that missing message SID raises error."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
        }

        with pytest.raises(ValueError, match="Message SID is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "twilio-get-message"


class TestTwilioListMessagesNode:
    """Tests for TwilioListMessagesNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.twilio import TwilioListMessagesNode
        return TwilioListMessagesNode()

    @pytest.mark.asyncio
    async def test_list_messages_success(self, node):
        """Test listing messages successfully."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "limit": 10,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "messages": [
                    {"sid": "SM1", "body": "Hello"},
                    {"sid": "SM2", "body": "World"},
                ]
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["count"] == 2
            assert len(result["messages"]) == 2

    @pytest.mark.asyncio
    async def test_list_messages_with_filters(self, node):
        """Test listing messages with filters."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "to_number": "+15559876543",
            "from_number": "+15551234567",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"messages": [{"sid": "SM1"}]}
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await node.execute(config, {})

            assert result["count"] == 1
            # Verify filters were passed
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert params["To"] == "+15559876543"
            assert params["From"] == "+15551234567"

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "twilio-list-messages"


class TestTwilioMakeCallNode:
    """Tests for TwilioMakeCallNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.twilio import TwilioMakeCallNode
        return TwilioMakeCallNode()

    @pytest.mark.asyncio
    async def test_make_call_with_url_success(self, node):
        """Test making a call with TwiML URL."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "from_number": "+15551234567",
            "to_number": "+15559876543",
            "twiml_url": "https://example.com/twiml.xml",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "sid": "CA123456",
                "status": "queued",
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["call_sid"] == "CA123456"

    @pytest.mark.asyncio
    async def test_make_call_with_twiml_success(self, node):
        """Test making a call with inline TwiML."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "from_number": "+15551234567",
            "to_number": "+15559876543",
            "twiml": "<Response><Say>Hello!</Say></Response>",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"sid": "CA789", "status": "queued"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_missing_twiml_raises_error(self, node):
        """Test that missing TwiML raises error."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "from_number": "+15551234567",
            "to_number": "+15559876543",
        }

        with pytest.raises(ValueError, match="Either TwiML URL or inline TwiML is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "twilio-make-call"


class TestTwilioLookupNode:
    """Tests for TwilioLookupNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.twilio import TwilioLookupNode
        return TwilioLookupNode()

    @pytest.mark.asyncio
    async def test_lookup_success(self, node):
        """Test phone number lookup successfully."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "phone_number": "+15551234567",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "phone_number": "+15551234567",
                "country_code": "US",
                "carrier": {"name": "Verizon"},
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["country_code"] == "US"
            assert result["phone_number"] == "+15551234567"

    @pytest.mark.asyncio
    async def test_lookup_failure(self, node):
        """Test handling lookup failure."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
            "phone_number": "+00000000000",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_missing_phone_number_raises_error(self, node):
        """Test that missing phone number raises error."""
        config = {
            "account_sid": "AC123",
            "auth_token": "token123",
        }

        with pytest.raises(ValueError, match="Phone number is required"):
            await node.execute(config, {})

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "twilio-lookup"


# ============================================================================
# SendGrid Node Tests
# ============================================================================

class TestSendGridSendEmailNode:
    """Tests for SendGridSendEmailNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.sendgrid import SendGridSendEmailNode
        return SendGridSendEmailNode()

    @pytest.mark.asyncio
    async def test_send_email_success(self, node):
        """Test sending email successfully."""
        config = {
            "api_key": "SG.test-key",
            "from_email": "sender@example.com",
            "from_name": "Test Sender",
            "to_email": "recipient@example.com",
            "to_name": "Test Recipient",
            "subject": "Test Email",
            "content": "This is a test email.",
            "content_type": "text/plain",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": "msg-abc123"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["message_id"] == "msg-abc123"
            assert result["status_code"] == 202

    @pytest.mark.asyncio
    async def test_send_html_email(self, node):
        """Test sending HTML email."""
        config = {
            "api_key": "SG.test-key",
            "from_email": "sender@example.com",
            "to_email": "recipient@example.com",
            "subject": "HTML Test",
            "content": "<h1>Hello World</h1>",
            "content_type": "text/html",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": "msg-html123"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self, node):
        """Test sending email with CC and BCC."""
        config = {
            "api_key": "SG.test-key",
            "from_email": "sender@example.com",
            "to_email": "recipient@example.com",
            "subject": "Test",
            "content": "Test content",
            "cc_email": "cc@example.com",
            "bcc_email": "bcc@example.com",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": "msg-cc123"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_email_failure(self, node):
        """Test handling send failure."""
        config = {
            "api_key": "invalid-key",
            "from_email": "sender@example.com",
            "to_email": "recipient@example.com",
            "subject": "Test",
            "content": "Test",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False
            assert result["error"] == "Unauthorized"

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "sendgrid-send-email"
        assert node.color == "#1A82E2"


class TestSendGridSendTemplateNode:
    """Tests for SendGridSendTemplateNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.sendgrid import SendGridSendTemplateNode
        return SendGridSendTemplateNode()

    @pytest.mark.asyncio
    async def test_send_template_success(self, node):
        """Test sending template email successfully."""
        config = {
            "api_key": "SG.test-key",
            "from_email": "sender@example.com",
            "to_email": "recipient@example.com",
            "template_id": "d-abc123xyz",
            "template_data": {"name": "John", "order_id": "12345"},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": "msg-template123"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["message_id"] == "msg-template123"

    @pytest.mark.asyncio
    async def test_send_template_without_data(self, node):
        """Test sending template without dynamic data."""
        config = {
            "api_key": "SG.test-key",
            "from_email": "sender@example.com",
            "to_email": "recipient@example.com",
            "template_id": "d-simple-template",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": "msg-simple"}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_template_invalid_template(self, node):
        """Test handling invalid template ID."""
        config = {
            "api_key": "SG.test-key",
            "from_email": "sender@example.com",
            "to_email": "recipient@example.com",
            "template_id": "invalid-template",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Invalid template ID"
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False
            assert "Invalid template" in result["error"]

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "sendgrid-send-template"


class TestSendGridGetStatsNode:
    """Tests for SendGridGetStatsNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.sendgrid import SendGridGetStatsNode
        return SendGridGetStatsNode()

    @pytest.mark.asyncio
    async def test_get_stats_success(self, node):
        """Test getting stats successfully."""
        config = {
            "api_key": "SG.test-key",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "aggregated_by": "day",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"date": "2024-01-01", "stats": [{"metrics": {"requests": 100, "delivered": 95}}]},
                {"date": "2024-01-02", "stats": [{"metrics": {"requests": 150, "delivered": 145}}]},
            ]
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert len(result["stats"]) == 2

    @pytest.mark.asyncio
    async def test_get_stats_weekly_aggregation(self, node):
        """Test getting stats with weekly aggregation."""
        config = {
            "api_key": "SG.test-key",
            "start_date": "2024-01-01",
            "aggregated_by": "week",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"date": "2024-01-01", "stats": [{"metrics": {"requests": 700}}]},
            ]
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_stats_failure(self, node):
        """Test handling stats failure."""
        config = {
            "api_key": "invalid-key",
            "start_date": "2024-01-01",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "sendgrid-get-stats"


class TestSendGridListTemplatesNode:
    """Tests for SendGridListTemplatesNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.sendgrid import SendGridListTemplatesNode
        return SendGridListTemplatesNode()

    @pytest.mark.asyncio
    async def test_list_templates_success(self, node):
        """Test listing templates successfully."""
        config = {
            "api_key": "SG.test-key",
            "generations": "dynamic",
            "page_size": 50,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": [
                    {"id": "d-template1", "name": "Welcome Email"},
                    {"id": "d-template2", "name": "Order Confirmation"},
                ]
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["count"] == 2
            assert result["templates"][0]["name"] == "Welcome Email"

    @pytest.mark.asyncio
    async def test_list_templates_empty(self, node):
        """Test listing when no templates."""
        config = {"api_key": "SG.test-key"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": []}
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["count"] == 0

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "sendgrid-list-templates"


class TestSendGridAddContactNode:
    """Tests for SendGridAddContactNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.sendgrid import SendGridAddContactNode
        return SendGridAddContactNode()

    @pytest.mark.asyncio
    async def test_add_contact_success(self, node):
        """Test adding contact successfully."""
        config = {
            "api_key": "SG.test-key",
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.json.return_value = {"job_id": "job-xyz123"}
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["job_id"] == "job-xyz123"

    @pytest.mark.asyncio
    async def test_add_contact_to_list(self, node):
        """Test adding contact to specific lists."""
        config = {
            "api_key": "SG.test-key",
            "email": "subscriber@example.com",
            "list_ids": ["list-abc", "list-xyz"],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.json.return_value = {"job_id": "job-list123"}
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_add_contact_with_custom_fields(self, node):
        """Test adding contact with custom fields."""
        config = {
            "api_key": "SG.test-key",
            "email": "custom@example.com",
            "custom_fields": {"company": "Acme Inc", "plan": "Enterprise"},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.json.return_value = {"job_id": "job-custom123"}
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_add_contact_failure(self, node):
        """Test handling add contact failure."""
        config = {
            "api_key": "invalid-key",
            "email": "test@example.com",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "sendgrid-add-contact"


class TestSendGridSearchContactsNode:
    """Tests for SendGridSearchContactsNode."""

    @pytest.fixture
    def node(self):
        from src.core.nodes.apps.sendgrid import SendGridSearchContactsNode
        return SendGridSearchContactsNode()

    @pytest.mark.asyncio
    async def test_search_contacts_success(self, node):
        """Test searching contacts successfully."""
        config = {
            "api_key": "SG.test-key",
            "query": "email LIKE '%@example.com'",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": [
                    {"id": "contact1", "email": "user1@example.com"},
                    {"id": "contact2", "email": "user2@example.com"},
                ]
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_search_contacts_empty(self, node):
        """Test searching when no results."""
        config = {
            "api_key": "SG.test-key",
            "query": "email = 'nonexistent@example.com'",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": []}
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is True
            assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_search_contacts_invalid_query(self, node):
        """Test handling invalid query syntax."""
        config = {
            "api_key": "SG.test-key",
            "query": "INVALID SYNTAX",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Invalid SGQL query"
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await node.execute(config, {})

            assert result["success"] is False
            assert "Invalid" in result["error"]

    def test_node_definition(self, node):
        """Test node has correct definition."""
        assert node.type == "sendgrid-search-contacts"