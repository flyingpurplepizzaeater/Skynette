"""HubSpot CRM integration nodes."""

from typing import Any
import httpx

from src.core.nodes.base import BaseNode, NodeField, FieldType


def _get_headers(access_token: str) -> dict:
    """Get HubSpot API headers."""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


class HubSpotGetContactNode(BaseNode):
    """Get a HubSpot contact by ID."""

    name = "hubspot_get_contact"
    display_name = "HubSpot Get Contact"
    category = "apps"
    description = "Get a HubSpot contact by ID"
    icon = "hubspot"
    color = "#FF7A59"

    inputs = [
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="hubspot",
            description="HubSpot access token.",
        ),
        NodeField(
            name="contact_id",
            label="Contact ID",
            type=FieldType.STRING,
            required=True,
            description="The HubSpot contact ID.",
        ),
        NodeField(
            name="properties",
            label="Properties",
            type=FieldType.STRING,
            required=False,
            description="Comma-separated list of properties to return (e.g., 'email,firstname,lastname').",
        ),
    ]

    outputs = [
        NodeField(
            name="contact",
            label="Contact",
            type=FieldType.JSON,
            required=True,
            description="The contact data.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Get a HubSpot contact."""
        access_token = config.get("access_token")
        contact_id = config.get("contact_id")
        properties = config.get("properties", "")

        if not access_token:
            raise ValueError("Access token is required")
        if not contact_id:
            raise ValueError("Contact ID is required")

        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
        params = {}
        if properties:
            params["properties"] = properties

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=_get_headers(access_token),
                params=params,
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"HubSpot API error: {response.status_code} - {response.text}")

        contact = response.json()
        return {"success": True, "contact": contact}


class HubSpotSearchContactsNode(BaseNode):
    """Search HubSpot contacts."""

    name = "hubspot_search_contacts"
    display_name = "HubSpot Search Contacts"
    category = "apps"
    description = "Search HubSpot contacts with filters"
    icon = "hubspot"
    color = "#FF7A59"

    inputs = [
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="hubspot",
            description="HubSpot access token.",
        ),
        NodeField(
            name="query",
            label="Query",
            type=FieldType.STRING,
            required=False,
            description="Search query string.",
        ),
        NodeField(
            name="filters",
            label="Filters",
            type=FieldType.JSON,
            required=False,
            description="Filter groups in HubSpot filter format.",
        ),
        NodeField(
            name="properties",
            label="Properties",
            type=FieldType.STRING,
            required=False,
            description="Comma-separated list of properties to return.",
        ),
        NodeField(
            name="limit",
            label="Limit",
            type=FieldType.NUMBER,
            required=False,
            default=10,
            description="Maximum number of results (default: 10, max: 100).",
        ),
    ]

    outputs = [
        NodeField(
            name="contacts",
            label="Contacts",
            type=FieldType.JSON,
            required=True,
            description="List of matching contacts.",
        ),
        NodeField(
            name="total",
            label="Total",
            type=FieldType.NUMBER,
            required=True,
            description="Total number of matching contacts.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Search HubSpot contacts."""
        access_token = config.get("access_token")
        query = config.get("query", "")
        filters = config.get("filters")
        properties = config.get("properties", "")
        limit = config.get("limit", 10)

        if not access_token:
            raise ValueError("Access token is required")

        url = "https://api.hubapi.com/crm/v3/objects/contacts/search"

        body: dict[str, Any] = {"limit": min(limit, 100)}

        if query:
            body["query"] = query

        if filters:
            body["filterGroups"] = filters if isinstance(filters, list) else [filters]

        if properties:
            body["properties"] = [p.strip() for p in properties.split(",")]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=_get_headers(access_token),
                json=body,
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"HubSpot API error: {response.status_code} - {response.text}")

        data = response.json()
        return {
            "success": True,
            "contacts": data.get("results", []),
            "total": data.get("total", 0),
        }


class HubSpotCreateContactNode(BaseNode):
    """Create a HubSpot contact."""

    name = "hubspot_create_contact"
    display_name = "HubSpot Create Contact"
    category = "apps"
    description = "Create a new HubSpot contact"
    icon = "hubspot"
    color = "#FF7A59"

    inputs = [
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="hubspot",
            description="HubSpot access token.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Contact email address.",
        ),
        NodeField(
            name="firstname",
            label="First Name",
            type=FieldType.STRING,
            required=False,
            description="Contact first name.",
        ),
        NodeField(
            name="lastname",
            label="Last Name",
            type=FieldType.STRING,
            required=False,
            description="Contact last name.",
        ),
        NodeField(
            name="phone",
            label="Phone",
            type=FieldType.STRING,
            required=False,
            description="Contact phone number.",
        ),
        NodeField(
            name="company",
            label="Company",
            type=FieldType.STRING,
            required=False,
            description="Contact company name.",
        ),
        NodeField(
            name="properties",
            label="Additional Properties",
            type=FieldType.JSON,
            required=False,
            description="Additional contact properties as JSON object.",
        ),
    ]

    outputs = [
        NodeField(
            name="contact",
            label="Contact",
            type=FieldType.JSON,
            required=True,
            description="The created contact data.",
        ),
        NodeField(
            name="contact_id",
            label="Contact ID",
            type=FieldType.STRING,
            required=True,
            description="The ID of the created contact.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Create a HubSpot contact."""
        access_token = config.get("access_token")
        email = config.get("email")
        firstname = config.get("firstname", "")
        lastname = config.get("lastname", "")
        phone = config.get("phone", "")
        company = config.get("company", "")
        additional_props = config.get("properties", {})

        if not access_token:
            raise ValueError("Access token is required")
        if not email:
            raise ValueError("Email is required")

        url = "https://api.hubapi.com/crm/v3/objects/contacts"

        properties = {"email": email}
        if firstname:
            properties["firstname"] = firstname
        if lastname:
            properties["lastname"] = lastname
        if phone:
            properties["phone"] = phone
        if company:
            properties["company"] = company
        if additional_props and isinstance(additional_props, dict):
            properties.update(additional_props)

        body = {"properties": properties}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=_get_headers(access_token),
                json=body,
                timeout=30.0,
            )

        if response.status_code != 201:
            raise ValueError(f"HubSpot API error: {response.status_code} - {response.text}")

        contact = response.json()
        return {
            "success": True,
            "contact": contact,
            "contact_id": contact.get("id"),
        }


class HubSpotUpdateContactNode(BaseNode):
    """Update a HubSpot contact."""

    name = "hubspot_update_contact"
    display_name = "HubSpot Update Contact"
    category = "apps"
    description = "Update an existing HubSpot contact"
    icon = "hubspot"
    color = "#FF7A59"

    inputs = [
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="hubspot",
            description="HubSpot access token.",
        ),
        NodeField(
            name="contact_id",
            label="Contact ID",
            type=FieldType.STRING,
            required=True,
            description="The HubSpot contact ID to update.",
        ),
        NodeField(
            name="properties",
            label="Properties",
            type=FieldType.JSON,
            required=True,
            description="Contact properties to update as JSON object.",
        ),
    ]

    outputs = [
        NodeField(
            name="contact",
            label="Contact",
            type=FieldType.JSON,
            required=True,
            description="The updated contact data.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Update a HubSpot contact."""
        access_token = config.get("access_token")
        contact_id = config.get("contact_id")
        properties = config.get("properties")

        if not access_token:
            raise ValueError("Access token is required")
        if not contact_id:
            raise ValueError("Contact ID is required")
        if not properties:
            raise ValueError("Properties are required")

        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
        body = {"properties": properties}

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=_get_headers(access_token),
                json=body,
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"HubSpot API error: {response.status_code} - {response.text}")

        contact = response.json()
        return {"success": True, "contact": contact}


class HubSpotGetDealNode(BaseNode):
    """Get a HubSpot deal by ID."""

    name = "hubspot_get_deal"
    display_name = "HubSpot Get Deal"
    category = "apps"
    description = "Get a HubSpot deal by ID"
    icon = "hubspot"
    color = "#FF7A59"

    inputs = [
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="hubspot",
            description="HubSpot access token.",
        ),
        NodeField(
            name="deal_id",
            label="Deal ID",
            type=FieldType.STRING,
            required=True,
            description="The HubSpot deal ID.",
        ),
        NodeField(
            name="properties",
            label="Properties",
            type=FieldType.STRING,
            required=False,
            description="Comma-separated list of properties to return.",
        ),
    ]

    outputs = [
        NodeField(
            name="deal",
            label="Deal",
            type=FieldType.JSON,
            required=True,
            description="The deal data.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Get a HubSpot deal."""
        access_token = config.get("access_token")
        deal_id = config.get("deal_id")
        properties = config.get("properties", "")

        if not access_token:
            raise ValueError("Access token is required")
        if not deal_id:
            raise ValueError("Deal ID is required")

        url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"
        params = {}
        if properties:
            params["properties"] = properties

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=_get_headers(access_token),
                params=params,
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"HubSpot API error: {response.status_code} - {response.text}")

        deal = response.json()
        return {"success": True, "deal": deal}


class HubSpotListDealsNode(BaseNode):
    """List HubSpot deals."""

    name = "hubspot_list_deals"
    display_name = "HubSpot List Deals"
    category = "apps"
    description = "List HubSpot deals with optional filters"
    icon = "hubspot"
    color = "#FF7A59"

    inputs = [
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="hubspot",
            description="HubSpot access token.",
        ),
        NodeField(
            name="properties",
            label="Properties",
            type=FieldType.STRING,
            required=False,
            description="Comma-separated list of properties to return.",
        ),
        NodeField(
            name="limit",
            label="Limit",
            type=FieldType.NUMBER,
            required=False,
            default=10,
            description="Maximum number of results (default: 10, max: 100).",
        ),
    ]

    outputs = [
        NodeField(
            name="deals",
            label="Deals",
            type=FieldType.JSON,
            required=True,
            description="List of deals.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """List HubSpot deals."""
        access_token = config.get("access_token")
        properties = config.get("properties", "")
        limit = config.get("limit", 10)

        if not access_token:
            raise ValueError("Access token is required")

        url = "https://api.hubapi.com/crm/v3/objects/deals"
        params: dict[str, Any] = {"limit": min(limit, 100)}
        if properties:
            params["properties"] = properties

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=_get_headers(access_token),
                params=params,
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"HubSpot API error: {response.status_code} - {response.text}")

        data = response.json()
        return {"success": True, "deals": data.get("results", [])}


class HubSpotCreateDealNode(BaseNode):
    """Create a HubSpot deal."""

    name = "hubspot_create_deal"
    display_name = "HubSpot Create Deal"
    category = "apps"
    description = "Create a new HubSpot deal"
    icon = "hubspot"
    color = "#FF7A59"

    inputs = [
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="hubspot",
            description="HubSpot access token.",
        ),
        NodeField(
            name="dealname",
            label="Deal Name",
            type=FieldType.STRING,
            required=True,
            description="Name of the deal.",
        ),
        NodeField(
            name="dealstage",
            label="Deal Stage",
            type=FieldType.STRING,
            required=False,
            description="Deal stage ID.",
        ),
        NodeField(
            name="pipeline",
            label="Pipeline",
            type=FieldType.STRING,
            required=False,
            description="Pipeline ID.",
        ),
        NodeField(
            name="amount",
            label="Amount",
            type=FieldType.NUMBER,
            required=False,
            description="Deal amount.",
        ),
        NodeField(
            name="closedate",
            label="Close Date",
            type=FieldType.STRING,
            required=False,
            description="Expected close date (ISO 8601 format).",
        ),
        NodeField(
            name="properties",
            label="Additional Properties",
            type=FieldType.JSON,
            required=False,
            description="Additional deal properties as JSON object.",
        ),
    ]

    outputs = [
        NodeField(
            name="deal",
            label="Deal",
            type=FieldType.JSON,
            required=True,
            description="The created deal data.",
        ),
        NodeField(
            name="deal_id",
            label="Deal ID",
            type=FieldType.STRING,
            required=True,
            description="The ID of the created deal.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Create a HubSpot deal."""
        access_token = config.get("access_token")
        dealname = config.get("dealname")
        dealstage = config.get("dealstage", "")
        pipeline = config.get("pipeline", "")
        amount = config.get("amount")
        closedate = config.get("closedate", "")
        additional_props = config.get("properties", {})

        if not access_token:
            raise ValueError("Access token is required")
        if not dealname:
            raise ValueError("Deal name is required")

        url = "https://api.hubapi.com/crm/v3/objects/deals"

        properties: dict[str, Any] = {"dealname": dealname}
        if dealstage:
            properties["dealstage"] = dealstage
        if pipeline:
            properties["pipeline"] = pipeline
        if amount is not None:
            properties["amount"] = str(amount)
        if closedate:
            properties["closedate"] = closedate
        if additional_props and isinstance(additional_props, dict):
            properties.update(additional_props)

        body = {"properties": properties}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=_get_headers(access_token),
                json=body,
                timeout=30.0,
            )

        if response.status_code != 201:
            raise ValueError(f"HubSpot API error: {response.status_code} - {response.text}")

        deal = response.json()
        return {
            "success": True,
            "deal": deal,
            "deal_id": deal.get("id"),
        }
