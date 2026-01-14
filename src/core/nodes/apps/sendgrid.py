"""
SendGrid Integration Nodes - Send transactional emails.

Uses SendGrid Web API v3 with API Key authentication.
"""

from typing import Optional

import httpx

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


def _get_api_key(config: dict) -> str:
    """Get API key from config or credential."""
    credential_id = config.get("credential")
    cred_data = _get_credential(credential_id) if credential_id else None

    if cred_data:
        return cred_data.get("api_key", "")
    return config.get("api_key", "")


class SendGridSendEmailNode(BaseNode):
    """Send an email via SendGrid."""

    type = "sendgrid-send-email"
    name = "SendGrid: Send Email"
    category = "Apps"
    description = "Send a transactional email using SendGrid API"
    icon = "email"
    color = "#1A82E2"  # SendGrid blue

    inputs = [
        NodeField(
            name="credential",
            label="SendGrid Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved SendGrid credential.",
            credential_service="sendgrid",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="SendGrid API key.",
        ),
        NodeField(
            name="from_email",
            label="From Email",
            type=FieldType.STRING,
            required=True,
            description="Sender email address.",
        ),
        NodeField(
            name="from_name",
            label="From Name",
            type=FieldType.STRING,
            required=False,
            description="Sender display name.",
        ),
        NodeField(
            name="to_email",
            label="To Email",
            type=FieldType.STRING,
            required=True,
            description="Recipient email address.",
        ),
        NodeField(
            name="to_name",
            label="To Name",
            type=FieldType.STRING,
            required=False,
            description="Recipient display name.",
        ),
        NodeField(
            name="subject",
            label="Subject",
            type=FieldType.STRING,
            required=True,
            description="Email subject line.",
        ),
        NodeField(
            name="content",
            label="Content",
            type=FieldType.STRING,
            required=True,
            description="Email body content (plain text or HTML).",
        ),
        NodeField(
            name="content_type",
            label="Content Type",
            type=FieldType.SELECT,
            required=False,
            default="text/plain",
            options=[
                {"value": "text/plain", "label": "Plain Text"},
                {"value": "text/html", "label": "HTML"},
            ],
            description="Content type.",
        ),
        NodeField(
            name="cc_email",
            label="CC Email",
            type=FieldType.STRING,
            required=False,
            description="CC recipient email address.",
        ),
        NodeField(
            name="bcc_email",
            label="BCC Email",
            type=FieldType.STRING,
            required=False,
            description="BCC recipient email address.",
        ),
        NodeField(
            name="reply_to",
            label="Reply To",
            type=FieldType.STRING,
            required=False,
            description="Reply-to email address.",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="message_id", label="Message ID", type=FieldType.STRING),
        NodeField(name="status_code", label="Status Code", type=FieldType.NUMBER),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the SendGrid send email node."""
        api_key = _get_api_key(config)
        from_email = config.get("from_email", "")
        from_name = config.get("from_name", "")
        to_email = config.get("to_email", "")
        to_name = config.get("to_name", "")
        subject = config.get("subject", "")
        content = config.get("content", "")
        content_type = config.get("content_type", "text/plain")
        cc_email = config.get("cc_email", "")
        bcc_email = config.get("bcc_email", "")
        reply_to = config.get("reply_to", "")

        # Build from object
        from_obj = {"email": from_email}
        if from_name:
            from_obj["name"] = from_name

        # Build to object
        to_obj = {"email": to_email}
        if to_name:
            to_obj["name"] = to_name

        # Build personalizations
        personalizations = [{"to": [to_obj]}]

        if cc_email:
            personalizations[0]["cc"] = [{"email": cc_email}]
        if bcc_email:
            personalizations[0]["bcc"] = [{"email": bcc_email}]

        # Build request payload
        payload = {
            "personalizations": personalizations,
            "from": from_obj,
            "subject": subject,
            "content": [{"type": content_type, "value": content}],
        }

        if reply_to:
            payload["reply_to"] = {"email": reply_to}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                # SendGrid returns 202 Accepted for successful sends
                if response.status_code == 202:
                    # Message ID is in the X-Message-Id header
                    message_id = response.headers.get("X-Message-Id", "")
                    return {
                        "success": True,
                        "message_id": message_id,
                        "status_code": response.status_code,
                        "error": "",
                    }
                else:
                    error_text = response.text
                    return {
                        "success": False,
                        "message_id": "",
                        "status_code": response.status_code,
                        "error": error_text,
                    }

        except Exception as e:
            return {
                "success": False,
                "message_id": "",
                "status_code": 0,
                "error": str(e),
            }


class SendGridSendTemplateNode(BaseNode):
    """Send an email using a SendGrid dynamic template."""

    type = "sendgrid-send-template"
    name = "SendGrid: Send Template"
    category = "Apps"
    description = "Send an email using a SendGrid dynamic template"
    icon = "template"
    color = "#1A82E2"

    inputs = [
        NodeField(
            name="credential",
            label="SendGrid Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved SendGrid credential.",
            credential_service="sendgrid",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="SendGrid API key.",
        ),
        NodeField(
            name="from_email",
            label="From Email",
            type=FieldType.STRING,
            required=True,
            description="Sender email address.",
        ),
        NodeField(
            name="from_name",
            label="From Name",
            type=FieldType.STRING,
            required=False,
            description="Sender display name.",
        ),
        NodeField(
            name="to_email",
            label="To Email",
            type=FieldType.STRING,
            required=True,
            description="Recipient email address.",
        ),
        NodeField(
            name="to_name",
            label="To Name",
            type=FieldType.STRING,
            required=False,
            description="Recipient display name.",
        ),
        NodeField(
            name="template_id",
            label="Template ID",
            type=FieldType.STRING,
            required=True,
            description="SendGrid dynamic template ID.",
        ),
        NodeField(
            name="template_data",
            label="Template Data",
            type=FieldType.JSON,
            required=False,
            default={},
            description="Dynamic template data (JSON object).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="message_id", label="Message ID", type=FieldType.STRING),
        NodeField(name="status_code", label="Status Code", type=FieldType.NUMBER),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the SendGrid send template node."""
        api_key = _get_api_key(config)
        from_email = config.get("from_email", "")
        from_name = config.get("from_name", "")
        to_email = config.get("to_email", "")
        to_name = config.get("to_name", "")
        template_id = config.get("template_id", "")
        template_data = config.get("template_data", {})

        # Build from object
        from_obj = {"email": from_email}
        if from_name:
            from_obj["name"] = from_name

        # Build to object
        to_obj = {"email": to_email}
        if to_name:
            to_obj["name"] = to_name

        # Build personalizations with dynamic template data
        personalizations = [{"to": [to_obj]}]
        if template_data:
            personalizations[0]["dynamic_template_data"] = template_data

        # Build request payload
        payload = {
            "personalizations": personalizations,
            "from": from_obj,
            "template_id": template_id,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code == 202:
                    message_id = response.headers.get("X-Message-Id", "")
                    return {
                        "success": True,
                        "message_id": message_id,
                        "status_code": response.status_code,
                        "error": "",
                    }
                else:
                    error_text = response.text
                    return {
                        "success": False,
                        "message_id": "",
                        "status_code": response.status_code,
                        "error": error_text,
                    }

        except Exception as e:
            return {
                "success": False,
                "message_id": "",
                "status_code": 0,
                "error": str(e),
            }


class SendGridGetStatsNode(BaseNode):
    """Get email statistics from SendGrid."""

    type = "sendgrid-get-stats"
    name = "SendGrid: Get Stats"
    category = "Apps"
    description = "Get email sending statistics from SendGrid"
    icon = "chart"
    color = "#1A82E2"

    inputs = [
        NodeField(
            name="credential",
            label="SendGrid Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved SendGrid credential.",
            credential_service="sendgrid",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="SendGrid API key.",
        ),
        NodeField(
            name="start_date",
            label="Start Date",
            type=FieldType.STRING,
            required=True,
            description="Start date in YYYY-MM-DD format.",
        ),
        NodeField(
            name="end_date",
            label="End Date",
            type=FieldType.STRING,
            required=False,
            description="End date in YYYY-MM-DD format (defaults to today).",
        ),
        NodeField(
            name="aggregated_by",
            label="Aggregated By",
            type=FieldType.SELECT,
            required=False,
            default="day",
            options=[
                {"value": "day", "label": "Day"},
                {"value": "week", "label": "Week"},
                {"value": "month", "label": "Month"},
            ],
            description="How to aggregate the statistics.",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="stats", label="Statistics", type=FieldType.JSON),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the SendGrid get stats node."""
        api_key = _get_api_key(config)
        start_date = config.get("start_date", "")
        end_date = config.get("end_date", "")
        aggregated_by = config.get("aggregated_by", "day")

        params = {
            "start_date": start_date,
            "aggregated_by": aggregated_by,
        }
        if end_date:
            params["end_date"] = end_date

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.sendgrid.com/v3/stats",
                    params=params,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    stats = response.json()
                    return {
                        "success": True,
                        "stats": stats,
                        "error": "",
                    }
                else:
                    error_text = response.text
                    return {
                        "success": False,
                        "stats": [],
                        "error": error_text,
                    }

        except Exception as e:
            return {
                "success": False,
                "stats": [],
                "error": str(e),
            }


class SendGridListTemplatesNode(BaseNode):
    """List SendGrid dynamic templates."""

    type = "sendgrid-list-templates"
    name = "SendGrid: List Templates"
    category = "Apps"
    description = "List available SendGrid dynamic templates"
    icon = "list"
    color = "#1A82E2"

    inputs = [
        NodeField(
            name="credential",
            label="SendGrid Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved SendGrid credential.",
            credential_service="sendgrid",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="SendGrid API key.",
        ),
        NodeField(
            name="generations",
            label="Generations",
            type=FieldType.SELECT,
            required=False,
            default="dynamic",
            options=[
                {"value": "dynamic", "label": "Dynamic"},
                {"value": "legacy", "label": "Legacy"},
            ],
            description="Template generation type.",
        ),
        NodeField(
            name="page_size",
            label="Page Size",
            type=FieldType.NUMBER,
            required=False,
            default=50,
            description="Number of templates per page (max 200).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="templates", label="Templates", type=FieldType.JSON),
        NodeField(name="count", label="Count", type=FieldType.NUMBER),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the SendGrid list templates node."""
        api_key = _get_api_key(config)
        generations = config.get("generations", "dynamic")
        page_size = config.get("page_size", 50)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.sendgrid.com/v3/templates",
                    params={
                        "generations": generations,
                        "page_size": page_size,
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    templates = data.get("result", [])
                    return {
                        "success": True,
                        "templates": templates,
                        "count": len(templates),
                        "error": "",
                    }
                else:
                    error_text = response.text
                    return {
                        "success": False,
                        "templates": [],
                        "count": 0,
                        "error": error_text,
                    }

        except Exception as e:
            return {
                "success": False,
                "templates": [],
                "count": 0,
                "error": str(e),
            }


class SendGridAddContactNode(BaseNode):
    """Add a contact to SendGrid."""

    type = "sendgrid-add-contact"
    name = "SendGrid: Add Contact"
    category = "Apps"
    description = "Add or update a contact in SendGrid"
    icon = "user-plus"
    color = "#1A82E2"

    inputs = [
        NodeField(
            name="credential",
            label="SendGrid Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved SendGrid credential.",
            credential_service="sendgrid",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="SendGrid API key.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Contact email address.",
        ),
        NodeField(
            name="first_name",
            label="First Name",
            type=FieldType.STRING,
            required=False,
            description="Contact first name.",
        ),
        NodeField(
            name="last_name",
            label="Last Name",
            type=FieldType.STRING,
            required=False,
            description="Contact last name.",
        ),
        NodeField(
            name="list_ids",
            label="List IDs",
            type=FieldType.JSON,
            required=False,
            default=[],
            description="List IDs to add the contact to (JSON array).",
        ),
        NodeField(
            name="custom_fields",
            label="Custom Fields",
            type=FieldType.JSON,
            required=False,
            default={},
            description="Custom field values (JSON object).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="job_id", label="Job ID", type=FieldType.STRING),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the SendGrid add contact node."""
        api_key = _get_api_key(config)
        email = config.get("email", "")
        first_name = config.get("first_name", "")
        last_name = config.get("last_name", "")
        list_ids = config.get("list_ids", [])
        custom_fields = config.get("custom_fields", {})

        # Build contact object
        contact = {"email": email}
        if first_name:
            contact["first_name"] = first_name
        if last_name:
            contact["last_name"] = last_name
        if custom_fields:
            contact["custom_fields"] = custom_fields

        # Build request payload
        payload = {"contacts": [contact]}
        if list_ids:
            payload["list_ids"] = list_ids

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    "https://api.sendgrid.com/v3/marketing/contacts",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code == 202:
                    data = response.json()
                    job_id = data.get("job_id", "")
                    return {
                        "success": True,
                        "job_id": job_id,
                        "error": "",
                    }
                else:
                    error_text = response.text
                    return {
                        "success": False,
                        "job_id": "",
                        "error": error_text,
                    }

        except Exception as e:
            return {
                "success": False,
                "job_id": "",
                "error": str(e),
            }


class SendGridSearchContactsNode(BaseNode):
    """Search contacts in SendGrid."""

    type = "sendgrid-search-contacts"
    name = "SendGrid: Search Contacts"
    category = "Apps"
    description = "Search contacts in SendGrid using SGQL query"
    icon = "search"
    color = "#1A82E2"

    inputs = [
        NodeField(
            name="credential",
            label="SendGrid Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved SendGrid credential.",
            credential_service="sendgrid",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="SendGrid API key.",
        ),
        NodeField(
            name="query",
            label="Query",
            type=FieldType.STRING,
            required=True,
            description="SGQL query (e.g., email LIKE '%@example.com').",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="contacts", label="Contacts", type=FieldType.JSON),
        NodeField(name="count", label="Count", type=FieldType.NUMBER),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the SendGrid search contacts node."""
        api_key = _get_api_key(config)
        query = config.get("query", "")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/marketing/contacts/search",
                    json={"query": query},
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    contacts = data.get("result", [])
                    return {
                        "success": True,
                        "contacts": contacts,
                        "count": len(contacts),
                        "error": "",
                    }
                else:
                    error_text = response.text
                    return {
                        "success": False,
                        "contacts": [],
                        "count": 0,
                        "error": error_text,
                    }

        except Exception as e:
            return {
                "success": False,
                "contacts": [],
                "count": 0,
                "error": str(e),
            }
