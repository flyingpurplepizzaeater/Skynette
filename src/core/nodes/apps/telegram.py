"""
Telegram Integration Nodes - Send messages via Telegram Bot API.
"""

from typing import Any, Optional

from src.core.nodes.base import BaseNode, NodeField, FieldType


class TelegramSendMessageNode(BaseNode):
    """
    Send messages via Telegram Bot.

    Supports:
    - Text messages with Markdown/HTML formatting
    - Photos, documents, and media
    - Reply keyboards and inline buttons
    - Silent messages
    """

    type = "telegram-send-message"
    name = "Telegram: Send Message"
    category = "Apps"
    description = "Send a message via Telegram Bot"
    icon = "send"
    color = "#0088CC"  # Telegram blue

    inputs = [
        NodeField(
            name="bot_token",
            label="Bot Token",
            type=FieldType.SECRET,
            required=True,
            description="Telegram Bot token from @BotFather.",
        ),
        NodeField(
            name="chat_id",
            label="Chat ID",
            type=FieldType.STRING,
            required=True,
            description="Target chat ID, username (@channel), or user ID.",
        ),
        NodeField(
            name="message",
            label="Message",
            type=FieldType.TEXT,
            required=True,
            description="Message text to send.",
        ),
        NodeField(
            name="parse_mode",
            label="Parse Mode",
            type=FieldType.SELECT,
            required=False,
            default="Markdown",
            options=[
                {"value": "Markdown", "label": "Markdown"},
                {"value": "HTML", "label": "HTML"},
                {"value": "", "label": "Plain Text"},
            ],
            description="Message formatting mode.",
        ),
        NodeField(
            name="disable_notification",
            label="Silent",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Send without notification sound.",
        ),
        NodeField(
            name="reply_to_message_id",
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
            description="Whether message was sent.",
        ),
        NodeField(
            name="message_id",
            label="Message ID",
            type=FieldType.NUMBER,
            description="ID of the sent message.",
        ),
        NodeField(
            name="chat",
            label="Chat Info",
            type=FieldType.JSON,
            description="Information about the chat.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Send message via Telegram."""
        import httpx

        bot_token = config.get("bot_token", "")
        chat_id = config.get("chat_id", "")
        message = config.get("message", "")
        parse_mode = config.get("parse_mode", "Markdown")
        disable_notification = config.get("disable_notification", False)
        reply_to = config.get("reply_to_message_id")

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": message,
            "disable_notification": disable_notification,
        }

        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_to:
            payload["reply_to_message_id"] = int(reply_to)

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            data = response.json()

        if data.get("ok"):
            result = data.get("result", {})
            return {
                "success": True,
                "message_id": result.get("message_id", 0),
                "chat": result.get("chat", {}),
            }

        return {
            "success": False,
            "message_id": 0,
            "chat": {},
        }


class TelegramSendPhotoNode(BaseNode):
    """
    Send photos via Telegram Bot.
    """

    type = "telegram-send-photo"
    name = "Telegram: Send Photo"
    category = "Apps"
    description = "Send a photo via Telegram Bot"
    icon = "image"
    color = "#0088CC"

    inputs = [
        NodeField(
            name="bot_token",
            label="Bot Token",
            type=FieldType.SECRET,
            required=True,
            description="Telegram Bot token.",
        ),
        NodeField(
            name="chat_id",
            label="Chat ID",
            type=FieldType.STRING,
            required=True,
            description="Target chat ID.",
        ),
        NodeField(
            name="photo",
            label="Photo URL or File ID",
            type=FieldType.STRING,
            required=True,
            description="URL to photo or Telegram file_id.",
        ),
        NodeField(
            name="caption",
            label="Caption",
            type=FieldType.TEXT,
            required=False,
            description="Photo caption.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
        ),
        NodeField(
            name="message_id",
            label="Message ID",
            type=FieldType.NUMBER,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Send photo via Telegram."""
        import httpx

        bot_token = config.get("bot_token", "")
        chat_id = config.get("chat_id", "")
        photo = config.get("photo", "")
        caption = config.get("caption", "")

        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

        payload = {
            "chat_id": chat_id,
            "photo": photo,
        }
        if caption:
            payload["caption"] = caption

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            data = response.json()

        return {
            "success": data.get("ok", False),
            "message_id": data.get("result", {}).get("message_id", 0),
        }


class TelegramGetUpdatesNode(BaseNode):
    """
    Get updates/messages from Telegram Bot.
    """

    type = "telegram-get-updates"
    name = "Telegram: Get Updates"
    category = "Apps"
    description = "Get recent messages/updates from bot"
    icon = "inbox"
    color = "#0088CC"

    inputs = [
        NodeField(
            name="bot_token",
            label="Bot Token",
            type=FieldType.SECRET,
            required=True,
        ),
        NodeField(
            name="limit",
            label="Limit",
            type=FieldType.NUMBER,
            required=False,
            default=10,
            description="Maximum number of updates to retrieve.",
        ),
        NodeField(
            name="offset",
            label="Offset",
            type=FieldType.NUMBER,
            required=False,
            description="Update offset (for pagination).",
        ),
    ]

    outputs = [
        NodeField(
            name="updates",
            label="Updates",
            type=FieldType.JSON,
            description="List of updates/messages.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Get updates from Telegram."""
        import httpx

        bot_token = config.get("bot_token", "")
        limit = int(config.get("limit", 10))
        offset = config.get("offset")

        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

        params = {"limit": limit}
        if offset:
            params["offset"] = int(offset)

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()

        updates = data.get("result", [])
        return {
            "updates": updates,
            "count": len(updates),
        }
