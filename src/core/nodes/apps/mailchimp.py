"""Mailchimp email marketing integration nodes."""

from typing import Any
import hashlib
import httpx

from src.core.nodes.base import BaseNode, NodeField, FieldType


def _get_base_url(api_key: str) -> str:
    """Get Mailchimp API base URL from API key."""
    # API key format: key-dc (e.g., abc123-us10)
    if "-" in api_key:
        dc = api_key.split("-")[-1]
    else:
        dc = "us1"
    return f"https://{dc}.api.mailchimp.com/3.0"


def _get_auth(api_key: str) -> tuple:
    """Get Mailchimp API auth tuple."""
    return ("anystring", api_key)


def _get_subscriber_hash(email: str) -> str:
    """Get MD5 hash of email for subscriber operations.

    Note: MD5 is required by Mailchimp API for subscriber identification.
    This is not used for security purposes.
    """
    return hashlib.md5(email.lower().encode(), usedforsecurity=False).hexdigest()


class MailchimpListAudiencesNode(BaseNode):
    """List Mailchimp audiences (lists)."""

    name = "mailchimp_list_audiences"
    display_name = "Mailchimp List Audiences"
    category = "apps"
    description = "List all Mailchimp audiences/lists"
    icon = "mailchimp"
    color = "#FFE01B"

    inputs = [
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="mailchimp",
            description="Mailchimp API key.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            required=False,
            default=10,
            description="Number of results to return (default: 10).",
        ),
    ]

    outputs = [
        NodeField(
            name="audiences",
            label="Audiences",
            type=FieldType.JSON,
            required=True,
            description="List of audiences.",
        ),
        NodeField(
            name="total",
            label="Total",
            type=FieldType.NUMBER,
            required=True,
            description="Total number of audiences.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """List Mailchimp audiences."""
        api_key = config.get("api_key")
        count = config.get("count", 10)

        if not api_key:
            raise ValueError("API key is required")

        url = f"{_get_base_url(api_key)}/lists"
        params = {"count": count}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                auth=_get_auth(api_key),
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"Mailchimp API error: {response.status_code} - {response.text}")

        data = response.json()
        return {
            "success": True,
            "audiences": data.get("lists", []),
            "total": data.get("total_items", 0),
        }


class MailchimpGetAudienceNode(BaseNode):
    """Get a Mailchimp audience by ID."""

    name = "mailchimp_get_audience"
    display_name = "Mailchimp Get Audience"
    category = "apps"
    description = "Get a Mailchimp audience by ID"
    icon = "mailchimp"
    color = "#FFE01B"

    inputs = [
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="mailchimp",
            description="Mailchimp API key.",
        ),
        NodeField(
            name="list_id",
            label="Audience ID",
            type=FieldType.STRING,
            required=True,
            description="The ID of the audience/list.",
        ),
    ]

    outputs = [
        NodeField(
            name="audience",
            label="Audience",
            type=FieldType.JSON,
            required=True,
            description="The audience data.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Get a Mailchimp audience."""
        api_key = config.get("api_key")
        list_id = config.get("list_id")

        if not api_key:
            raise ValueError("API key is required")
        if not list_id:
            raise ValueError("Audience ID is required")

        url = f"{_get_base_url(api_key)}/lists/{list_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                auth=_get_auth(api_key),
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"Mailchimp API error: {response.status_code} - {response.text}")

        return {"success": True, "audience": response.json()}


class MailchimpAddSubscriberNode(BaseNode):
    """Add a subscriber to a Mailchimp audience."""

    name = "mailchimp_add_subscriber"
    display_name = "Mailchimp Add Subscriber"
    category = "apps"
    description = "Add a new subscriber to a Mailchimp audience"
    icon = "mailchimp"
    color = "#FFE01B"

    inputs = [
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="mailchimp",
            description="Mailchimp API key.",
        ),
        NodeField(
            name="list_id",
            label="Audience ID",
            type=FieldType.STRING,
            required=True,
            description="The ID of the audience/list.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Subscriber email address.",
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.SELECT,
            required=False,
            default="subscribed",
            options=[
                {"value": "subscribed", "label": "Subscribed"},
                {"value": "pending", "label": "Pending (Double Opt-in)"},
                {"value": "unsubscribed", "label": "Unsubscribed"},
                {"value": "cleaned", "label": "Cleaned"},
            ],
            description="Subscription status.",
        ),
        NodeField(
            name="first_name",
            label="First Name",
            type=FieldType.STRING,
            required=False,
            description="Subscriber first name.",
        ),
        NodeField(
            name="last_name",
            label="Last Name",
            type=FieldType.STRING,
            required=False,
            description="Subscriber last name.",
        ),
        NodeField(
            name="tags",
            label="Tags",
            type=FieldType.STRING,
            required=False,
            description="Comma-separated list of tags.",
        ),
    ]

    outputs = [
        NodeField(
            name="subscriber",
            label="Subscriber",
            type=FieldType.JSON,
            required=True,
            description="The subscriber data.",
        ),
        NodeField(
            name="subscriber_id",
            label="Subscriber ID",
            type=FieldType.STRING,
            required=True,
            description="The subscriber ID (email hash).",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Add a subscriber to Mailchimp."""
        api_key = config.get("api_key")
        list_id = config.get("list_id")
        email = config.get("email")
        status = config.get("status", "subscribed")
        first_name = config.get("first_name", "")
        last_name = config.get("last_name", "")
        tags = config.get("tags", "")

        if not api_key:
            raise ValueError("API key is required")
        if not list_id:
            raise ValueError("Audience ID is required")
        if not email:
            raise ValueError("Email is required")

        url = f"{_get_base_url(api_key)}/lists/{list_id}/members"

        member_data: dict[str, Any] = {
            "email_address": email,
            "status": status,
        }

        merge_fields = {}
        if first_name:
            merge_fields["FNAME"] = first_name
        if last_name:
            merge_fields["LNAME"] = last_name
        if merge_fields:
            member_data["merge_fields"] = merge_fields

        if tags:
            member_data["tags"] = [t.strip() for t in tags.split(",")]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=member_data,
                auth=_get_auth(api_key),
                timeout=30.0,
            )

        if response.status_code not in (200, 201):
            raise ValueError(f"Mailchimp API error: {response.status_code} - {response.text}")

        subscriber = response.json()
        return {
            "success": True,
            "subscriber": subscriber,
            "subscriber_id": subscriber.get("id"),
        }


class MailchimpUpdateSubscriberNode(BaseNode):
    """Update a subscriber in a Mailchimp audience."""

    name = "mailchimp_update_subscriber"
    display_name = "Mailchimp Update Subscriber"
    category = "apps"
    description = "Update an existing subscriber in a Mailchimp audience"
    icon = "mailchimp"
    color = "#FFE01B"

    inputs = [
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="mailchimp",
            description="Mailchimp API key.",
        ),
        NodeField(
            name="list_id",
            label="Audience ID",
            type=FieldType.STRING,
            required=True,
            description="The ID of the audience/list.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Subscriber email address.",
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.SELECT,
            required=False,
            options=[
                {"value": "subscribed", "label": "Subscribed"},
                {"value": "pending", "label": "Pending"},
                {"value": "unsubscribed", "label": "Unsubscribed"},
                {"value": "cleaned", "label": "Cleaned"},
            ],
            description="New subscription status.",
        ),
        NodeField(
            name="first_name",
            label="First Name",
            type=FieldType.STRING,
            required=False,
            description="Subscriber first name.",
        ),
        NodeField(
            name="last_name",
            label="Last Name",
            type=FieldType.STRING,
            required=False,
            description="Subscriber last name.",
        ),
    ]

    outputs = [
        NodeField(
            name="subscriber",
            label="Subscriber",
            type=FieldType.JSON,
            required=True,
            description="The updated subscriber data.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Update a subscriber in Mailchimp."""
        api_key = config.get("api_key")
        list_id = config.get("list_id")
        email = config.get("email")
        status = config.get("status", "")
        first_name = config.get("first_name", "")
        last_name = config.get("last_name", "")

        if not api_key:
            raise ValueError("API key is required")
        if not list_id:
            raise ValueError("Audience ID is required")
        if not email:
            raise ValueError("Email is required")

        subscriber_hash = _get_subscriber_hash(email)
        url = f"{_get_base_url(api_key)}/lists/{list_id}/members/{subscriber_hash}"

        member_data: dict[str, Any] = {}
        if status:
            member_data["status"] = status

        merge_fields = {}
        if first_name:
            merge_fields["FNAME"] = first_name
        if last_name:
            merge_fields["LNAME"] = last_name
        if merge_fields:
            member_data["merge_fields"] = merge_fields

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                json=member_data,
                auth=_get_auth(api_key),
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"Mailchimp API error: {response.status_code} - {response.text}")

        return {"success": True, "subscriber": response.json()}


class MailchimpGetSubscriberNode(BaseNode):
    """Get a subscriber from a Mailchimp audience."""

    name = "mailchimp_get_subscriber"
    display_name = "Mailchimp Get Subscriber"
    category = "apps"
    description = "Get a subscriber from a Mailchimp audience by email"
    icon = "mailchimp"
    color = "#FFE01B"

    inputs = [
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="mailchimp",
            description="Mailchimp API key.",
        ),
        NodeField(
            name="list_id",
            label="Audience ID",
            type=FieldType.STRING,
            required=True,
            description="The ID of the audience/list.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Subscriber email address.",
        ),
    ]

    outputs = [
        NodeField(
            name="subscriber",
            label="Subscriber",
            type=FieldType.JSON,
            required=True,
            description="The subscriber data.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Get a subscriber from Mailchimp."""
        api_key = config.get("api_key")
        list_id = config.get("list_id")
        email = config.get("email")

        if not api_key:
            raise ValueError("API key is required")
        if not list_id:
            raise ValueError("Audience ID is required")
        if not email:
            raise ValueError("Email is required")

        subscriber_hash = _get_subscriber_hash(email)
        url = f"{_get_base_url(api_key)}/lists/{list_id}/members/{subscriber_hash}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                auth=_get_auth(api_key),
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"Mailchimp API error: {response.status_code} - {response.text}")

        return {"success": True, "subscriber": response.json()}


class MailchimpListCampaignsNode(BaseNode):
    """List Mailchimp campaigns."""

    name = "mailchimp_list_campaigns"
    display_name = "Mailchimp List Campaigns"
    category = "apps"
    description = "List Mailchimp campaigns"
    icon = "mailchimp"
    color = "#FFE01B"

    inputs = [
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="mailchimp",
            description="Mailchimp API key.",
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.SELECT,
            required=False,
            options=[
                {"value": "save", "label": "Saved/Draft"},
                {"value": "paused", "label": "Paused"},
                {"value": "schedule", "label": "Scheduled"},
                {"value": "sending", "label": "Sending"},
                {"value": "sent", "label": "Sent"},
            ],
            description="Filter by campaign status.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            required=False,
            default=10,
            description="Number of results to return.",
        ),
    ]

    outputs = [
        NodeField(
            name="campaigns",
            label="Campaigns",
            type=FieldType.JSON,
            required=True,
            description="List of campaigns.",
        ),
        NodeField(
            name="total",
            label="Total",
            type=FieldType.NUMBER,
            required=True,
            description="Total number of campaigns.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """List Mailchimp campaigns."""
        api_key = config.get("api_key")
        status = config.get("status", "")
        count = config.get("count", 10)

        if not api_key:
            raise ValueError("API key is required")

        url = f"{_get_base_url(api_key)}/campaigns"
        params: dict[str, Any] = {"count": count}
        if status:
            params["status"] = status

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                auth=_get_auth(api_key),
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"Mailchimp API error: {response.status_code} - {response.text}")

        data = response.json()
        return {
            "success": True,
            "campaigns": data.get("campaigns", []),
            "total": data.get("total_items", 0),
        }


class MailchimpCreateCampaignNode(BaseNode):
    """Create a Mailchimp campaign."""

    name = "mailchimp_create_campaign"
    display_name = "Mailchimp Create Campaign"
    category = "apps"
    description = "Create a new Mailchimp email campaign"
    icon = "mailchimp"
    color = "#FFE01B"

    inputs = [
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="mailchimp",
            description="Mailchimp API key.",
        ),
        NodeField(
            name="list_id",
            label="Audience ID",
            type=FieldType.STRING,
            required=True,
            description="The ID of the audience/list to send to.",
        ),
        NodeField(
            name="campaign_type",
            label="Type",
            type=FieldType.SELECT,
            required=False,
            default="regular",
            options=[
                {"value": "regular", "label": "Regular"},
                {"value": "plaintext", "label": "Plain Text"},
                {"value": "absplit", "label": "A/B Split"},
                {"value": "rss", "label": "RSS"},
            ],
            description="Campaign type.",
        ),
        NodeField(
            name="subject",
            label="Subject Line",
            type=FieldType.STRING,
            required=True,
            description="Email subject line.",
        ),
        NodeField(
            name="from_name",
            label="From Name",
            type=FieldType.STRING,
            required=True,
            description="Sender name.",
        ),
        NodeField(
            name="reply_to",
            label="Reply-To Email",
            type=FieldType.STRING,
            required=True,
            description="Reply-to email address.",
        ),
    ]

    outputs = [
        NodeField(
            name="campaign",
            label="Campaign",
            type=FieldType.JSON,
            required=True,
            description="The created campaign data.",
        ),
        NodeField(
            name="campaign_id",
            label="Campaign ID",
            type=FieldType.STRING,
            required=True,
            description="The ID of the created campaign.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Create a Mailchimp campaign."""
        api_key = config.get("api_key")
        list_id = config.get("list_id")
        campaign_type = config.get("campaign_type", "regular")
        subject = config.get("subject")
        from_name = config.get("from_name")
        reply_to = config.get("reply_to")

        if not api_key:
            raise ValueError("API key is required")
        if not list_id:
            raise ValueError("Audience ID is required")
        if not subject:
            raise ValueError("Subject line is required")
        if not from_name:
            raise ValueError("From name is required")
        if not reply_to:
            raise ValueError("Reply-to email is required")

        url = f"{_get_base_url(api_key)}/campaigns"

        campaign_data = {
            "type": campaign_type,
            "recipients": {"list_id": list_id},
            "settings": {
                "subject_line": subject,
                "from_name": from_name,
                "reply_to": reply_to,
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=campaign_data,
                auth=_get_auth(api_key),
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"Mailchimp API error: {response.status_code} - {response.text}")

        campaign = response.json()
        return {
            "success": True,
            "campaign": campaign,
            "campaign_id": campaign.get("id"),
        }


class MailchimpSendCampaignNode(BaseNode):
    """Send a Mailchimp campaign."""

    name = "mailchimp_send_campaign"
    display_name = "Mailchimp Send Campaign"
    category = "apps"
    description = "Send a Mailchimp campaign immediately"
    icon = "mailchimp"
    color = "#FFE01B"

    inputs = [
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="mailchimp",
            description="Mailchimp API key.",
        ),
        NodeField(
            name="campaign_id",
            label="Campaign ID",
            type=FieldType.STRING,
            required=True,
            description="The ID of the campaign to send.",
        ),
    ]

    outputs = [
        NodeField(
            name="sent",
            label="Sent",
            type=FieldType.BOOLEAN,
            required=True,
            description="Whether the campaign was sent.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Send a Mailchimp campaign."""
        api_key = config.get("api_key")
        campaign_id = config.get("campaign_id")

        if not api_key:
            raise ValueError("API key is required")
        if not campaign_id:
            raise ValueError("Campaign ID is required")

        url = f"{_get_base_url(api_key)}/campaigns/{campaign_id}/actions/send"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                auth=_get_auth(api_key),
                timeout=30.0,
            )

        if response.status_code != 204:
            raise ValueError(f"Mailchimp API error: {response.status_code} - {response.text}")

        return {"success": True, "sent": True, "campaign_id": campaign_id}
