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
