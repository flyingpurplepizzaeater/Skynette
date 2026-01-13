"""
Microsoft Teams Integration Nodes - Send messages and interact with Teams.

Uses Microsoft Graph API for Teams operations.
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


def _get_access_token(config: dict) -> str:
    """Get access token from config or credential."""
    credential_id = config.get("credential")
    cred_data = _get_credential(credential_id) if credential_id else None

    if cred_data:
        return cred_data.get("access_token", "")

    return config.get("access_token", "")


class TeamsSendMessageNode(BaseNode):
    """
    Send messages to Microsoft Teams channels or chats.

    Supports:
    - Channel messages
    - Chat messages (1:1 or group)
    - Rich text and adaptive cards
    - Reply to existing messages
    """

    type = "teams-send-message"
    name = "Teams: Send Message"
    category = "Apps"
    description = "Send a message to a Microsoft Teams channel or chat"
    icon = "chat"
    color = "#6264A7"  # Teams purple

    inputs = [
        NodeField(
            name="credential",
            label="Microsoft Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Microsoft credential.",
            credential_service="microsoft_oauth",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Microsoft Graph API access token (or use saved credential).",
        ),
        NodeField(
            name="destination_type",
            label="Destination Type",
            type=FieldType.SELECT,
            required=True,
            default="channel",
            options=[
                {"value": "channel", "label": "Channel"},
                {"value": "chat", "label": "Chat"},
            ],
            description="Send to a channel or direct chat.",
        ),
        NodeField(
            name="team_id",
            label="Team ID",
            type=FieldType.STRING,
            required=False,
            description="Team ID (required for channel messages).",
        ),
        NodeField(
            name="channel_id",
            label="Channel ID",
            type=FieldType.STRING,
            required=False,
            description="Channel ID (required for channel messages).",
        ),
        NodeField(
            name="chat_id",
            label="Chat ID",
            type=FieldType.STRING,
            required=False,
            description="Chat ID (required for chat messages).",
        ),
        NodeField(
            name="message",
            label="Message",
            type=FieldType.TEXT,
            required=True,
            description="The message content. Supports HTML formatting.",
        ),
        NodeField(
            name="content_type",
            label="Content Type",
            type=FieldType.SELECT,
            required=False,
            default="text",
            options=[
                {"value": "text", "label": "Plain Text"},
                {"value": "html", "label": "HTML"},
            ],
            description="Message content format.",
        ),
        NodeField(
            name="reply_to_id",
            label="Reply To Message ID",
            type=FieldType.STRING,
            required=False,
            description="Message ID to reply to (for threaded replies).",
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
            name="message_id",
            label="Message ID",
            type=FieldType.STRING,
            description="ID of the sent message.",
        ),
        NodeField(
            name="web_url",
            label="Web URL",
            type=FieldType.STRING,
            description="URL to view the message in Teams.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Send message to Teams."""
        import httpx

        access_token = _get_access_token(config)
        if not access_token:
            raise ValueError("Access token required (via credential or direct input)")

        destination_type = config.get("destination_type", "channel")
        message = config.get("message", "")
        content_type = config.get("content_type", "text")
        reply_to_id = config.get("reply_to_id")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # Build message body
        body = {
            "body": {
                "contentType": content_type,
                "content": message,
            }
        }

        # Determine endpoint
        if destination_type == "channel":
            team_id = config.get("team_id")
            channel_id = config.get("channel_id")

            if not team_id or not channel_id:
                raise ValueError("Team ID and Channel ID are required for channel messages")

            if reply_to_id:
                # Reply to existing message
                url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages/{reply_to_id}/replies"
            else:
                url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages"
        else:
            chat_id = config.get("chat_id")

            if not chat_id:
                raise ValueError("Chat ID is required for chat messages")

            url = f"https://graph.microsoft.com/v1.0/chats/{chat_id}/messages"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=body, headers=headers)

            if response.status_code in (200, 201):
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("id", ""),
                    "web_url": data.get("webUrl", ""),
                }
            else:
                return {
                    "success": False,
                    "message_id": "",
                    "web_url": "",
                }


class TeamsListChannelsNode(BaseNode):
    """
    List channels in a Microsoft Teams team.
    """

    type = "teams-list-channels"
    name = "Teams: List Channels"
    category = "Apps"
    description = "List all channels in a Teams team"
    icon = "list"
    color = "#6264A7"

    inputs = [
        NodeField(
            name="credential",
            label="Microsoft Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Microsoft credential.",
            credential_service="microsoft_oauth",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Microsoft Graph API access token (or use saved credential).",
        ),
        NodeField(
            name="team_id",
            label="Team ID",
            type=FieldType.STRING,
            required=True,
            description="The ID of the team to list channels for.",
        ),
    ]

    outputs = [
        NodeField(
            name="channels",
            label="Channels",
            type=FieldType.JSON,
            description="List of channels with their details.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of channels.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List channels in a team."""
        import httpx

        access_token = _get_access_token(config)
        if not access_token:
            raise ValueError("Access token required")

        team_id = config.get("team_id")
        if not team_id:
            raise ValueError("Team ID is required")

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                channels = data.get("value", [])
                return {
                    "channels": channels,
                    "count": len(channels),
                }
            else:
                return {
                    "channels": [],
                    "count": 0,
                }


class TeamsListTeamsNode(BaseNode):
    """
    List teams the user is a member of.
    """

    type = "teams-list-teams"
    name = "Teams: List Teams"
    category = "Apps"
    description = "List all teams the user is a member of"
    icon = "groups"
    color = "#6264A7"

    inputs = [
        NodeField(
            name="credential",
            label="Microsoft Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Microsoft credential.",
            credential_service="microsoft_oauth",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Microsoft Graph API access token (or use saved credential).",
        ),
    ]

    outputs = [
        NodeField(
            name="teams",
            label="Teams",
            type=FieldType.JSON,
            description="List of teams with their details.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of teams.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List user's teams."""
        import httpx

        access_token = _get_access_token(config)
        if not access_token:
            raise ValueError("Access token required")

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        url = "https://graph.microsoft.com/v1.0/me/joinedTeams"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                teams = data.get("value", [])
                return {
                    "teams": teams,
                    "count": len(teams),
                }
            else:
                return {
                    "teams": [],
                    "count": 0,
                }


class TeamsGetMessagesNode(BaseNode):
    """
    Get messages from a Teams channel or chat.
    """

    type = "teams-get-messages"
    name = "Teams: Get Messages"
    category = "Apps"
    description = "Get messages from a Teams channel or chat"
    icon = "inbox"
    color = "#6264A7"

    inputs = [
        NodeField(
            name="credential",
            label="Microsoft Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Microsoft credential.",
            credential_service="microsoft_oauth",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Microsoft Graph API access token (or use saved credential).",
        ),
        NodeField(
            name="source_type",
            label="Source Type",
            type=FieldType.SELECT,
            required=True,
            default="channel",
            options=[
                {"value": "channel", "label": "Channel"},
                {"value": "chat", "label": "Chat"},
            ],
            description="Get messages from channel or chat.",
        ),
        NodeField(
            name="team_id",
            label="Team ID",
            type=FieldType.STRING,
            required=False,
            description="Team ID (required for channel messages).",
        ),
        NodeField(
            name="channel_id",
            label="Channel ID",
            type=FieldType.STRING,
            required=False,
            description="Channel ID (required for channel messages).",
        ),
        NodeField(
            name="chat_id",
            label="Chat ID",
            type=FieldType.STRING,
            required=False,
            description="Chat ID (required for chat messages).",
        ),
        NodeField(
            name="limit",
            label="Limit",
            type=FieldType.NUMBER,
            required=False,
            default=50,
            description="Maximum number of messages to retrieve.",
        ),
    ]

    outputs = [
        NodeField(
            name="messages",
            label="Messages",
            type=FieldType.JSON,
            description="List of messages.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of messages retrieved.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Get messages from Teams."""
        import httpx

        access_token = _get_access_token(config)
        if not access_token:
            raise ValueError("Access token required")

        source_type = config.get("source_type", "channel")
        limit = config.get("limit", 50)

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        # Determine endpoint
        if source_type == "channel":
            team_id = config.get("team_id")
            channel_id = config.get("channel_id")

            if not team_id or not channel_id:
                raise ValueError("Team ID and Channel ID are required")

            url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages?$top={limit}"
        else:
            chat_id = config.get("chat_id")

            if not chat_id:
                raise ValueError("Chat ID is required")

            url = f"https://graph.microsoft.com/v1.0/chats/{chat_id}/messages?$top={limit}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                messages = data.get("value", [])
                return {
                    "messages": messages,
                    "count": len(messages),
                }
            else:
                return {
                    "messages": [],
                    "count": 0,
                }


class TeamsCreateMeetingNode(BaseNode):
    """
    Create an online meeting in Microsoft Teams.
    """

    type = "teams-create-meeting"
    name = "Teams: Create Meeting"
    category = "Apps"
    description = "Create an online meeting in Microsoft Teams"
    icon = "video_call"
    color = "#6264A7"

    inputs = [
        NodeField(
            name="credential",
            label="Microsoft Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Microsoft credential.",
            credential_service="microsoft_oauth",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Microsoft Graph API access token (or use saved credential).",
        ),
        NodeField(
            name="subject",
            label="Subject",
            type=FieldType.STRING,
            required=True,
            description="Meeting subject/title.",
        ),
        NodeField(
            name="start_time",
            label="Start Time",
            type=FieldType.STRING,
            required=True,
            description="Meeting start time in ISO 8601 format (e.g., 2024-01-15T14:00:00).",
        ),
        NodeField(
            name="end_time",
            label="End Time",
            type=FieldType.STRING,
            required=True,
            description="Meeting end time in ISO 8601 format.",
        ),
        NodeField(
            name="attendees",
            label="Attendees",
            type=FieldType.TEXT,
            required=False,
            description="Comma-separated list of attendee email addresses.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the meeting was created successfully.",
        ),
        NodeField(
            name="meeting_id",
            label="Meeting ID",
            type=FieldType.STRING,
            description="ID of the created meeting.",
        ),
        NodeField(
            name="join_url",
            label="Join URL",
            type=FieldType.STRING,
            description="URL to join the meeting.",
        ),
        NodeField(
            name="join_info",
            label="Join Info",
            type=FieldType.JSON,
            description="Full meeting join information.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Create Teams meeting."""
        import httpx

        access_token = _get_access_token(config)
        if not access_token:
            raise ValueError("Access token required")

        subject = config.get("subject", "")
        start_time = config.get("start_time", "")
        end_time = config.get("end_time", "")
        attendees_str = config.get("attendees", "")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # Build meeting body
        body = {
            "subject": subject,
            "startDateTime": start_time,
            "endDateTime": end_time,
        }

        # Add attendees if provided
        if attendees_str:
            attendees = [
                {
                    "emailAddress": {"address": email.strip()},
                    "type": "required",
                }
                for email in attendees_str.split(",")
                if email.strip()
            ]
            body["participants"] = {"attendees": attendees}

        url = "https://graph.microsoft.com/v1.0/me/onlineMeetings"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=body, headers=headers)

            if response.status_code in (200, 201):
                data = response.json()
                return {
                    "success": True,
                    "meeting_id": data.get("id", ""),
                    "join_url": data.get("joinWebUrl", ""),
                    "join_info": data.get("joinInformation", {}),
                }
            else:
                return {
                    "success": False,
                    "meeting_id": "",
                    "join_url": "",
                    "join_info": {},
                }
