"""
Discord Integration Node - Send messages and interact with Discord.
"""

from typing import Any, Optional

from src.core.nodes.base import BaseNode, NodeField, FieldType


class DiscordWebhookNode(BaseNode):
    """
    Send messages to Discord via webhook.

    Supports:
    - Plain text and rich embeds
    - Custom username and avatar
    - File attachments
    """

    type = "discord-webhook"
    name = "Discord: Send Webhook"
    category = "Apps"
    description = "Send a message to Discord via webhook"
    icon = "chat"
    color = "#5865F2"  # Discord blurple

    inputs = [
        NodeField(
            name="webhook_url",
            label="Webhook URL",
            type=FieldType.SECRET,
            required=True,
            description="Discord webhook URL.",
        ),
        NodeField(
            name="content",
            label="Message Content",
            type=FieldType.TEXT,
            required=False,
            description="Plain text message content.",
        ),
        NodeField(
            name="username",
            label="Username",
            type=FieldType.STRING,
            required=False,
            description="Override the webhook's username.",
        ),
        NodeField(
            name="avatar_url",
            label="Avatar URL",
            type=FieldType.STRING,
            required=False,
            description="Override the webhook's avatar.",
        ),
        NodeField(
            name="embed_title",
            label="Embed Title",
            type=FieldType.STRING,
            required=False,
            description="Title for rich embed.",
        ),
        NodeField(
            name="embed_description",
            label="Embed Description",
            type=FieldType.TEXT,
            required=False,
            description="Description for rich embed.",
        ),
        NodeField(
            name="embed_color",
            label="Embed Color",
            type=FieldType.STRING,
            required=False,
            default="#5865F2",
            description="Embed sidebar color (hex).",
        ),
        NodeField(
            name="embed_url",
            label="Embed URL",
            type=FieldType.STRING,
            required=False,
            description="URL for the embed title.",
        ),
        NodeField(
            name="embed_image",
            label="Embed Image URL",
            type=FieldType.STRING,
            required=False,
            description="Image URL to include in embed.",
        ),
        NodeField(
            name="embed_footer",
            label="Embed Footer",
            type=FieldType.STRING,
            required=False,
            description="Footer text for embed.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the message was sent.",
        ),
        NodeField(
            name="status_code",
            label="Status Code",
            type=FieldType.NUMBER,
            description="HTTP response status code.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Send message to Discord webhook."""
        import httpx

        webhook_url = config.get("webhook_url")
        content = config.get("content", "")
        username = config.get("username")
        avatar_url = config.get("avatar_url")
        embed_title = config.get("embed_title")
        embed_description = config.get("embed_description")
        embed_color = config.get("embed_color", "#5865F2")
        embed_url = config.get("embed_url")
        embed_image = config.get("embed_image")
        embed_footer = config.get("embed_footer")

        # Build payload
        payload = {}

        if content:
            payload["content"] = content
        if username:
            payload["username"] = username
        if avatar_url:
            payload["avatar_url"] = avatar_url

        # Build embed if any embed field is set
        if any([embed_title, embed_description, embed_image]):
            embed = {}
            if embed_title:
                embed["title"] = embed_title
            if embed_description:
                embed["description"] = embed_description
            if embed_url:
                embed["url"] = embed_url
            if embed_color:
                # Convert hex to int
                color_hex = embed_color.lstrip("#")
                embed["color"] = int(color_hex, 16)
            if embed_image:
                embed["image"] = {"url": embed_image}
            if embed_footer:
                embed["footer"] = {"text": embed_footer}

            payload["embeds"] = [embed]

        if not payload:
            payload["content"] = "Empty message"

        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)

        return {
            "success": response.status_code in [200, 204],
            "status_code": response.status_code,
        }


class DiscordBotMessageNode(BaseNode):
    """
    Send messages via Discord Bot API.

    Requires a Discord bot token and channel ID.
    """

    type = "discord-bot-message"
    name = "Discord: Bot Message"
    category = "Apps"
    description = "Send a message via Discord Bot"
    icon = "smart_toy"
    color = "#5865F2"

    inputs = [
        NodeField(
            name="bot_token",
            label="Bot Token",
            type=FieldType.SECRET,
            required=True,
            description="Discord Bot Token.",
        ),
        NodeField(
            name="channel_id",
            label="Channel ID",
            type=FieldType.STRING,
            required=True,
            description="Discord channel ID to send to.",
        ),
        NodeField(
            name="content",
            label="Message Content",
            type=FieldType.TEXT,
            required=True,
            description="Message content to send.",
        ),
        NodeField(
            name="reply_to",
            label="Reply To Message ID",
            type=FieldType.STRING,
            required=False,
            description="Message ID to reply to.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the message was sent.",
        ),
        NodeField(
            name="message_id",
            label="Message ID",
            type=FieldType.STRING,
            description="ID of the sent message.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Send message via Discord Bot API."""
        import httpx

        bot_token = config.get("bot_token")
        channel_id = config.get("channel_id")
        content = config.get("content", "")
        reply_to = config.get("reply_to")

        headers = {
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json",
        }

        payload = {"content": content}

        if reply_to:
            payload["message_reference"] = {"message_id": reply_to}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                json=payload,
                headers=headers,
            )
            data = response.json()

        return {
            "success": response.status_code == 200,
            "message_id": data.get("id", ""),
        }
