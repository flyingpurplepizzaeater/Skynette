"""
Twilio Integration Nodes - Send SMS and WhatsApp messages.

Uses Twilio REST API with Account SID and Auth Token.
"""

import base64

from src.core.nodes.base import BaseNode, FieldType, NodeField


def _get_credential(credential_id: str | None) -> dict | None:
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


def _get_auth(config: dict) -> tuple[str, str]:
    """Get Account SID and Auth Token from config or credential."""
    credential_id = config.get("credential")
    cred_data = _get_credential(credential_id) if credential_id else None

    if cred_data:
        account_sid = cred_data.get("account_sid", "")
        auth_token = cred_data.get("auth_token", "")
    else:
        account_sid = config.get("account_sid", "")
        auth_token = config.get("auth_token", "")

    return account_sid, auth_token


def _make_auth_header(account_sid: str, auth_token: str) -> str:
    """Create Basic Auth header value."""
    credentials = f"{account_sid}:{auth_token}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


class TwilioSendSMSNode(BaseNode):
    """
    Send an SMS message via Twilio.
    """

    type = "twilio-send-sms"
    name = "Twilio: Send SMS"
    category = "Apps"
    description = "Send an SMS message"
    icon = "sms"
    color = "#F22F46"  # Twilio red

    inputs = [
        NodeField(
            name="credential",
            label="Twilio Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Twilio credential.",
            credential_service="twilio",
        ),
        NodeField(
            name="account_sid",
            label="Account SID",
            type=FieldType.STRING,
            required=False,
            description="Twilio Account SID.",
        ),
        NodeField(
            name="auth_token",
            label="Auth Token",
            type=FieldType.SECRET,
            required=False,
            description="Twilio Auth Token.",
        ),
        NodeField(
            name="from_number",
            label="From Number",
            type=FieldType.STRING,
            required=True,
            description="Your Twilio phone number (E.164 format, e.g., +15551234567).",
        ),
        NodeField(
            name="to_number",
            label="To Number",
            type=FieldType.STRING,
            required=True,
            description="Recipient phone number (E.164 format).",
        ),
        NodeField(
            name="body",
            label="Message Body",
            type=FieldType.TEXT,
            required=True,
            description="The text message to send.",
        ),
        NodeField(
            name="media_url",
            label="Media URL",
            type=FieldType.STRING,
            required=False,
            description="URL of media to include (MMS).",
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
            name="message_sid",
            label="Message SID",
            type=FieldType.STRING,
            description="Unique identifier for the message.",
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.STRING,
            description="Message status (queued, sent, delivered, etc.).",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Send SMS via Twilio."""
        import httpx

        account_sid, auth_token = _get_auth(config)

        if not account_sid or not auth_token:
            raise ValueError("Account SID and Auth Token are required")

        from_number = config.get("from_number", "")
        to_number = config.get("to_number", "")
        body = config.get("body", "")

        if not from_number:
            raise ValueError("From number is required")
        if not to_number:
            raise ValueError("To number is required")
        if not body:
            raise ValueError("Message body is required")

        headers = {
            "Authorization": _make_auth_header(account_sid, auth_token),
        }

        data = {
            "From": from_number,
            "To": to_number,
            "Body": body,
        }

        media_url = config.get("media_url")
        if media_url:
            data["MediaUrl"] = media_url

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data)

            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "message_sid": result.get("sid", ""),
                    "status": result.get("status", ""),
                }
            else:
                return {
                    "success": False,
                    "message_sid": "",
                    "status": "failed",
                }


class TwilioSendWhatsAppNode(BaseNode):
    """
    Send a WhatsApp message via Twilio.
    """

    type = "twilio-send-whatsapp"
    name = "Twilio: Send WhatsApp"
    category = "Apps"
    description = "Send a WhatsApp message"
    icon = "chat"
    color = "#F22F46"

    inputs = [
        NodeField(
            name="credential",
            label="Twilio Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Twilio credential.",
            credential_service="twilio",
        ),
        NodeField(
            name="account_sid",
            label="Account SID",
            type=FieldType.STRING,
            required=False,
            description="Twilio Account SID.",
        ),
        NodeField(
            name="auth_token",
            label="Auth Token",
            type=FieldType.SECRET,
            required=False,
            description="Twilio Auth Token.",
        ),
        NodeField(
            name="from_number",
            label="From Number",
            type=FieldType.STRING,
            required=True,
            description="Your Twilio WhatsApp number (e.g., +14155238886).",
        ),
        NodeField(
            name="to_number",
            label="To Number",
            type=FieldType.STRING,
            required=True,
            description="Recipient WhatsApp number (E.164 format).",
        ),
        NodeField(
            name="body",
            label="Message Body",
            type=FieldType.TEXT,
            required=True,
            description="The message to send.",
        ),
        NodeField(
            name="media_url",
            label="Media URL",
            type=FieldType.STRING,
            required=False,
            description="URL of media to include.",
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
            name="message_sid",
            label="Message SID",
            type=FieldType.STRING,
            description="Unique identifier for the message.",
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.STRING,
            description="Message status.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Send WhatsApp message via Twilio."""
        import httpx

        account_sid, auth_token = _get_auth(config)

        if not account_sid or not auth_token:
            raise ValueError("Account SID and Auth Token are required")

        from_number = config.get("from_number", "")
        to_number = config.get("to_number", "")
        body = config.get("body", "")

        if not from_number:
            raise ValueError("From number is required")
        if not to_number:
            raise ValueError("To number is required")
        if not body:
            raise ValueError("Message body is required")

        # WhatsApp uses whatsapp: prefix
        whatsapp_from = (
            f"whatsapp:{from_number}" if not from_number.startswith("whatsapp:") else from_number
        )
        whatsapp_to = (
            f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number
        )

        headers = {
            "Authorization": _make_auth_header(account_sid, auth_token),
        }

        data = {
            "From": whatsapp_from,
            "To": whatsapp_to,
            "Body": body,
        }

        media_url = config.get("media_url")
        if media_url:
            data["MediaUrl"] = media_url

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data)

            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "message_sid": result.get("sid", ""),
                    "status": result.get("status", ""),
                }
            else:
                return {
                    "success": False,
                    "message_sid": "",
                    "status": "failed",
                }


class TwilioGetMessageNode(BaseNode):
    """
    Get details of a specific Twilio message.
    """

    type = "twilio-get-message"
    name = "Twilio: Get Message"
    category = "Apps"
    description = "Get message details by SID"
    icon = "info"
    color = "#F22F46"

    inputs = [
        NodeField(
            name="credential",
            label="Twilio Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Twilio credential.",
            credential_service="twilio",
        ),
        NodeField(
            name="account_sid",
            label="Account SID",
            type=FieldType.STRING,
            required=False,
            description="Twilio Account SID.",
        ),
        NodeField(
            name="auth_token",
            label="Auth Token",
            type=FieldType.SECRET,
            required=False,
            description="Twilio Auth Token.",
        ),
        NodeField(
            name="message_sid",
            label="Message SID",
            type=FieldType.STRING,
            required=True,
            description="The message SID to retrieve.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the message was found.",
        ),
        NodeField(
            name="message",
            label="Message",
            type=FieldType.JSON,
            description="Full message data.",
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.STRING,
            description="Message status.",
        ),
        NodeField(
            name="body",
            label="Body",
            type=FieldType.STRING,
            description="Message body text.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Get Twilio message details."""
        import httpx

        account_sid, auth_token = _get_auth(config)

        if not account_sid or not auth_token:
            raise ValueError("Account SID and Auth Token are required")

        message_sid = config.get("message_sid", "")
        if not message_sid:
            raise ValueError("Message SID is required")

        headers = {
            "Authorization": _make_auth_header(account_sid, auth_token),
        }

        url = (
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages/{message_sid}.json"
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                message = response.json()
                return {
                    "success": True,
                    "message": message,
                    "status": message.get("status", ""),
                    "body": message.get("body", ""),
                }
            else:
                return {
                    "success": False,
                    "message": {},
                    "status": "",
                    "body": "",
                }


class TwilioListMessagesNode(BaseNode):
    """
    List Twilio messages with optional filters.
    """

    type = "twilio-list-messages"
    name = "Twilio: List Messages"
    category = "Apps"
    description = "List sent and received messages"
    icon = "list"
    color = "#F22F46"

    inputs = [
        NodeField(
            name="credential",
            label="Twilio Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Twilio credential.",
            credential_service="twilio",
        ),
        NodeField(
            name="account_sid",
            label="Account SID",
            type=FieldType.STRING,
            required=False,
            description="Twilio Account SID.",
        ),
        NodeField(
            name="auth_token",
            label="Auth Token",
            type=FieldType.SECRET,
            required=False,
            description="Twilio Auth Token.",
        ),
        NodeField(
            name="to_number",
            label="To Number",
            type=FieldType.STRING,
            required=False,
            description="Filter by recipient number.",
        ),
        NodeField(
            name="from_number",
            label="From Number",
            type=FieldType.STRING,
            required=False,
            description="Filter by sender number.",
        ),
        NodeField(
            name="date_sent",
            label="Date Sent",
            type=FieldType.STRING,
            required=False,
            description="Filter by date (YYYY-MM-DD).",
        ),
        NodeField(
            name="limit",
            label="Limit",
            type=FieldType.NUMBER,
            required=False,
            default=20,
            description="Maximum messages to return.",
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
            description="Number of messages returned.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List Twilio messages."""
        import httpx

        account_sid, auth_token = _get_auth(config)

        if not account_sid or not auth_token:
            raise ValueError("Account SID and Auth Token are required")

        headers = {
            "Authorization": _make_auth_header(account_sid, auth_token),
        }

        params = {}

        to_number = config.get("to_number")
        if to_number:
            params["To"] = to_number

        from_number = config.get("from_number")
        if from_number:
            params["From"] = from_number

        date_sent = config.get("date_sent")
        if date_sent:
            params["DateSent"] = date_sent

        limit = config.get("limit", 20)
        params["PageSize"] = limit

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                return {
                    "messages": messages,
                    "count": len(messages),
                }
            else:
                return {
                    "messages": [],
                    "count": 0,
                }


class TwilioMakeCallNode(BaseNode):
    """
    Initiate a phone call via Twilio.
    """

    type = "twilio-make-call"
    name = "Twilio: Make Call"
    category = "Apps"
    description = "Initiate an outbound phone call"
    icon = "phone"
    color = "#F22F46"

    inputs = [
        NodeField(
            name="credential",
            label="Twilio Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Twilio credential.",
            credential_service="twilio",
        ),
        NodeField(
            name="account_sid",
            label="Account SID",
            type=FieldType.STRING,
            required=False,
            description="Twilio Account SID.",
        ),
        NodeField(
            name="auth_token",
            label="Auth Token",
            type=FieldType.SECRET,
            required=False,
            description="Twilio Auth Token.",
        ),
        NodeField(
            name="from_number",
            label="From Number",
            type=FieldType.STRING,
            required=True,
            description="Your Twilio phone number.",
        ),
        NodeField(
            name="to_number",
            label="To Number",
            type=FieldType.STRING,
            required=True,
            description="Number to call.",
        ),
        NodeField(
            name="twiml_url",
            label="TwiML URL",
            type=FieldType.STRING,
            required=False,
            description="URL returning TwiML instructions.",
        ),
        NodeField(
            name="twiml",
            label="TwiML",
            type=FieldType.TEXT,
            required=False,
            description="Inline TwiML instructions (e.g., <Say>Hello!</Say>).",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the call was initiated.",
        ),
        NodeField(
            name="call_sid",
            label="Call SID",
            type=FieldType.STRING,
            description="Unique identifier for the call.",
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.STRING,
            description="Call status.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Make outbound call via Twilio."""
        import httpx

        account_sid, auth_token = _get_auth(config)

        if not account_sid or not auth_token:
            raise ValueError("Account SID and Auth Token are required")

        from_number = config.get("from_number", "")
        to_number = config.get("to_number", "")

        if not from_number:
            raise ValueError("From number is required")
        if not to_number:
            raise ValueError("To number is required")

        twiml_url = config.get("twiml_url", "")
        twiml = config.get("twiml", "")

        if not twiml_url and not twiml:
            raise ValueError("Either TwiML URL or inline TwiML is required")

        headers = {
            "Authorization": _make_auth_header(account_sid, auth_token),
        }

        data = {
            "From": from_number,
            "To": to_number,
        }

        if twiml_url:
            data["Url"] = twiml_url
        elif twiml:
            data["Twiml"] = twiml

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data)

            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "call_sid": result.get("sid", ""),
                    "status": result.get("status", ""),
                }
            else:
                return {
                    "success": False,
                    "call_sid": "",
                    "status": "failed",
                }


class TwilioLookupNode(BaseNode):
    """
    Look up information about a phone number.
    """

    type = "twilio-lookup"
    name = "Twilio: Lookup Number"
    category = "Apps"
    description = "Look up phone number information"
    icon = "search"
    color = "#F22F46"

    inputs = [
        NodeField(
            name="credential",
            label="Twilio Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Twilio credential.",
            credential_service="twilio",
        ),
        NodeField(
            name="account_sid",
            label="Account SID",
            type=FieldType.STRING,
            required=False,
            description="Twilio Account SID.",
        ),
        NodeField(
            name="auth_token",
            label="Auth Token",
            type=FieldType.SECRET,
            required=False,
            description="Twilio Auth Token.",
        ),
        NodeField(
            name="phone_number",
            label="Phone Number",
            type=FieldType.STRING,
            required=True,
            description="Phone number to look up (E.164 format).",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the lookup succeeded.",
        ),
        NodeField(
            name="phone_number",
            label="Phone Number",
            type=FieldType.STRING,
            description="Formatted phone number.",
        ),
        NodeField(
            name="country_code",
            label="Country Code",
            type=FieldType.STRING,
            description="ISO country code.",
        ),
        NodeField(
            name="carrier",
            label="Carrier",
            type=FieldType.JSON,
            description="Carrier information (if available).",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Look up phone number via Twilio."""
        from urllib.parse import quote

        import httpx

        account_sid, auth_token = _get_auth(config)

        if not account_sid or not auth_token:
            raise ValueError("Account SID and Auth Token are required")

        phone_number = config.get("phone_number", "")
        if not phone_number:
            raise ValueError("Phone number is required")

        headers = {
            "Authorization": _make_auth_header(account_sid, auth_token),
        }

        encoded_number = quote(phone_number, safe="")
        url = f"https://lookups.twilio.com/v2/PhoneNumbers/{encoded_number}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "phone_number": data.get("phone_number", ""),
                    "country_code": data.get("country_code", ""),
                    "carrier": data.get("carrier", {}),
                }
            else:
                return {
                    "success": False,
                    "phone_number": "",
                    "country_code": "",
                    "carrier": {},
                }
