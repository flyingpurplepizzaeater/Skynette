"""
Slack Integration Node - Send messages and interact with Slack.
"""

from typing import Any, Optional

from src.core.nodes.base import BaseNode, NodeField, FieldType


def _get_credential(credential_id: Optional[str]) -> Optional[dict]:
    """Load credential from vault if ID is provided."""
    if not credential_id:
        return None
    try:
        from src.data.credentials import CredentialVault
        vault = CredentialVault()
        cred = vault.get_credential(credential_id)
        if cred:
            return cred.get("data", {})
    except Exception:
        pass
    return None


class SlackSendMessageNode(BaseNode):
    """
    Send messages to Slack channels.

    Supports:
    - Plain text and formatted messages
    - Blocks for rich formatting
    - File attachments
    - Thread replies
    """

    type = "slack-send-message"
    name = "Slack: Send Message"
    category = "Apps"
    description = "Send a message to a Slack channel"
    icon = "chat"
    color = "#4A154B"  # Slack purple

    inputs = [
        NodeField(
            name="credential",
            label="Slack Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Slack credential.",
            credential_service="slack",
        ),
        NodeField(
            name="webhook_url",
            label="Webhook URL",
            type=FieldType.SECRET,
            required=False,
            description="Slack Incoming Webhook URL (or use saved credential above).",
        ),
        NodeField(
            name="bot_token",
            label="Bot Token",
            type=FieldType.SECRET,
            required=False,
            description="Slack Bot Token (or use saved credential above).",
        ),
        NodeField(
            name="channel",
            label="Channel",
            type=FieldType.STRING,
            required=False,
            description="Channel ID or name (e.g., #general). Required with Bot Token.",
        ),
        NodeField(
            name="message",
            label="Message",
            type=FieldType.TEXT,
            required=True,
            description="The message to send. Supports Slack markdown.",
        ),
        NodeField(
            name="username",
            label="Username",
            type=FieldType.STRING,
            required=False,
            description="Override the bot's username.",
        ),
        NodeField(
            name="icon_emoji",
            label="Icon Emoji",
            type=FieldType.STRING,
            required=False,
            description="Override the bot's icon (e.g., :robot_face:).",
        ),
        NodeField(
            name="thread_ts",
            label="Thread Timestamp",
            type=FieldType.STRING,
            required=False,
            description="Reply in a thread (provide parent message timestamp).",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the message was sent successfully.",
        ),
        NodeField(
            name="message_ts",
            label="Message Timestamp",
            type=FieldType.STRING,
            description="Timestamp of the sent message (for threading).",
        ),
        NodeField(
            name="channel_id",
            label="Channel ID",
            type=FieldType.STRING,
            description="ID of the channel where message was sent.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Send message to Slack."""
        import httpx

        # Check for saved credential first
        credential_id = config.get("credential")
        cred_data = _get_credential(credential_id) if credential_id else None

        # Use credential data or fall back to direct config
        if cred_data:
            webhook_url = cred_data.get("webhook_url") or cred_data.get("api_key")
            bot_token = cred_data.get("bot_token")
        else:
            webhook_url = config.get("webhook_url")
            bot_token = config.get("bot_token")

        channel = config.get("channel")
        message = config.get("message", "")
        username = config.get("username")
        icon_emoji = config.get("icon_emoji")
        thread_ts = config.get("thread_ts")

        if webhook_url:
            # Use incoming webhook
            return await self._send_via_webhook(
                webhook_url, message, username, icon_emoji
            )
        elif bot_token:
            # Use Bot API
            return await self._send_via_bot(
                bot_token, channel, message, username, icon_emoji, thread_ts
            )
        else:
            raise ValueError("Either webhook_url or bot_token is required")

    async def _send_via_webhook(
        self,
        webhook_url: str,
        message: str,
        username: Optional[str],
        icon_emoji: Optional[str],
    ) -> dict:
        """Send message via incoming webhook."""
        import httpx

        payload = {"text": message}
        if username:
            payload["username"] = username
        if icon_emoji:
            payload["icon_emoji"] = icon_emoji

        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            success = response.status_code == 200

        return {
            "success": success,
            "message_ts": "",
            "channel_id": "",
        }

    async def _send_via_bot(
        self,
        bot_token: str,
        channel: str,
        message: str,
        username: Optional[str],
        icon_emoji: Optional[str],
        thread_ts: Optional[str],
    ) -> dict:
        """Send message via Slack Bot API."""
        import httpx

        if not channel:
            raise ValueError("Channel is required when using bot token")

        payload = {
            "channel": channel,
            "text": message,
        }
        if username:
            payload["username"] = username
        if icon_emoji:
            payload["icon_emoji"] = icon_emoji
        if thread_ts:
            payload["thread_ts"] = thread_ts

        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                json=payload,
                headers=headers,
            )
            data = response.json()

        return {
            "success": data.get("ok", False),
            "message_ts": data.get("ts", ""),
            "channel_id": data.get("channel", ""),
        }


class SlackReactionNode(BaseNode):
    """
    Add reactions to Slack messages.
    """

    type = "slack-add-reaction"
    name = "Slack: Add Reaction"
    category = "Apps"
    description = "Add an emoji reaction to a message"
    icon = "add_reaction"
    color = "#4A154B"

    inputs = [
        NodeField(
            name="credential",
            label="Slack Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Slack credential.",
            credential_service="slack",
        ),
        NodeField(
            name="bot_token",
            label="Bot Token",
            type=FieldType.SECRET,
            required=False,
            description="Slack Bot Token (or use saved credential above).",
        ),
        NodeField(
            name="channel",
            label="Channel",
            type=FieldType.STRING,
            required=True,
            description="Channel ID where the message is.",
        ),
        NodeField(
            name="message_ts",
            label="Message Timestamp",
            type=FieldType.STRING,
            required=True,
            description="Timestamp of the message to react to.",
        ),
        NodeField(
            name="emoji",
            label="Emoji",
            type=FieldType.STRING,
            required=True,
            default="thumbsup",
            description="Emoji name without colons (e.g., thumbsup, heart).",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the reaction was added.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Add reaction to message."""
        import httpx

        # Check for saved credential first
        credential_id = config.get("credential")
        cred_data = _get_credential(credential_id) if credential_id else None

        # Use credential data or fall back to direct config
        if cred_data:
            bot_token = cred_data.get("bot_token") or cred_data.get("api_key")
        else:
            bot_token = config.get("bot_token")

        if not bot_token:
            raise ValueError("Bot token is required (via credential or direct input)")

        channel = config.get("channel")
        message_ts = config.get("message_ts")
        emoji = config.get("emoji", "thumbsup")

        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "channel": channel,
            "timestamp": message_ts,
            "name": emoji,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/reactions.add",
                json=payload,
                headers=headers,
            )
            data = response.json()

        return {
            "success": data.get("ok", False),
        }
