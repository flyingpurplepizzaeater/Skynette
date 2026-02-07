"""Zendesk customer support integration nodes."""

from typing import Any

import httpx

from src.core.nodes.base import BaseNode, FieldType, NodeField


def _get_auth(email: str, api_token: str) -> tuple:
    """Get Zendesk API auth tuple."""
    return (f"{email}/token", api_token)


def _get_base_url(subdomain: str) -> str:
    """Get Zendesk API base URL."""
    return f"https://{subdomain}.zendesk.com/api/v2"


class ZendeskCreateTicketNode(BaseNode):
    """Create a Zendesk support ticket."""

    name = "zendesk_create_ticket"
    display_name = "Zendesk Create Ticket"
    category = "apps"
    description = "Create a new Zendesk support ticket"
    icon = "zendesk"
    color = "#03363D"

    inputs = [
        NodeField(
            name="subdomain",
            label="Subdomain",
            type=FieldType.STRING,
            required=True,
            description="Your Zendesk subdomain (e.g., 'mycompany' for mycompany.zendesk.com).",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Admin/agent email address.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="zendesk",
            description="Zendesk API token.",
        ),
        NodeField(
            name="subject",
            label="Subject",
            type=FieldType.STRING,
            required=True,
            description="Ticket subject line.",
        ),
        NodeField(
            name="description",
            label="Description",
            type=FieldType.STRING,
            required=True,
            description="Ticket description/body.",
        ),
        NodeField(
            name="requester_email",
            label="Requester Email",
            type=FieldType.STRING,
            required=False,
            description="Email of the ticket requester.",
        ),
        NodeField(
            name="requester_name",
            label="Requester Name",
            type=FieldType.STRING,
            required=False,
            description="Name of the ticket requester.",
        ),
        NodeField(
            name="priority",
            label="Priority",
            type=FieldType.SELECT,
            required=False,
            options=[
                {"value": "low", "label": "Low"},
                {"value": "normal", "label": "Normal"},
                {"value": "high", "label": "High"},
                {"value": "urgent", "label": "Urgent"},
            ],
            description="Ticket priority level.",
        ),
        NodeField(
            name="ticket_type",
            label="Type",
            type=FieldType.SELECT,
            required=False,
            options=[
                {"value": "problem", "label": "Problem"},
                {"value": "incident", "label": "Incident"},
                {"value": "question", "label": "Question"},
                {"value": "task", "label": "Task"},
            ],
            description="Ticket type.",
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
            name="ticket",
            label="Ticket",
            type=FieldType.JSON,
            required=True,
            description="The created ticket data.",
        ),
        NodeField(
            name="ticket_id",
            label="Ticket ID",
            type=FieldType.NUMBER,
            required=True,
            description="The ID of the created ticket.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Create a Zendesk ticket."""
        subdomain = config.get("subdomain")
        email = config.get("email")
        api_token = config.get("api_token")
        subject = config.get("subject")
        description = config.get("description")
        requester_email = config.get("requester_email", "")
        requester_name = config.get("requester_name", "")
        priority = config.get("priority", "")
        ticket_type = config.get("ticket_type", "")
        tags = config.get("tags", "")

        if not subdomain:
            raise ValueError("Subdomain is required")
        if not email:
            raise ValueError("Email is required")
        if not api_token:
            raise ValueError("API token is required")
        if not subject:
            raise ValueError("Subject is required")
        if not description:
            raise ValueError("Description is required")

        url = f"{_get_base_url(subdomain)}/tickets.json"

        ticket_data: dict[str, Any] = {
            "subject": subject,
            "comment": {"body": description},
        }

        if requester_email or requester_name:
            ticket_data["requester"] = {}
            if requester_email:
                ticket_data["requester"]["email"] = requester_email
            if requester_name:
                ticket_data["requester"]["name"] = requester_name

        if priority:
            ticket_data["priority"] = priority
        if ticket_type:
            ticket_data["type"] = ticket_type
        if tags:
            ticket_data["tags"] = [t.strip() for t in tags.split(",")]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"ticket": ticket_data},
                auth=_get_auth(email, api_token),
                timeout=30.0,
            )

        if response.status_code != 201:
            raise ValueError(f"Zendesk API error: {response.status_code} - {response.text}")

        data = response.json()
        ticket = data.get("ticket", {})
        return {
            "success": True,
            "ticket": ticket,
            "ticket_id": ticket.get("id"),
        }


class ZendeskGetTicketNode(BaseNode):
    """Get a Zendesk ticket by ID."""

    name = "zendesk_get_ticket"
    display_name = "Zendesk Get Ticket"
    category = "apps"
    description = "Get a Zendesk ticket by ID"
    icon = "zendesk"
    color = "#03363D"

    inputs = [
        NodeField(
            name="subdomain",
            label="Subdomain",
            type=FieldType.STRING,
            required=True,
            description="Your Zendesk subdomain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Admin/agent email address.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="zendesk",
            description="Zendesk API token.",
        ),
        NodeField(
            name="ticket_id",
            label="Ticket ID",
            type=FieldType.NUMBER,
            required=True,
            description="The ID of the ticket to retrieve.",
        ),
    ]

    outputs = [
        NodeField(
            name="ticket",
            label="Ticket",
            type=FieldType.JSON,
            required=True,
            description="The ticket data.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Get a Zendesk ticket."""
        subdomain = config.get("subdomain")
        email = config.get("email")
        api_token = config.get("api_token")
        ticket_id = config.get("ticket_id")

        if not subdomain:
            raise ValueError("Subdomain is required")
        if not email:
            raise ValueError("Email is required")
        if not api_token:
            raise ValueError("API token is required")
        if not ticket_id:
            raise ValueError("Ticket ID is required")

        url = f"{_get_base_url(subdomain)}/tickets/{ticket_id}.json"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                auth=_get_auth(email, api_token),
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"Zendesk API error: {response.status_code} - {response.text}")

        data = response.json()
        return {"success": True, "ticket": data.get("ticket", {})}


class ZendeskUpdateTicketNode(BaseNode):
    """Update a Zendesk ticket."""

    name = "zendesk_update_ticket"
    display_name = "Zendesk Update Ticket"
    category = "apps"
    description = "Update an existing Zendesk ticket"
    icon = "zendesk"
    color = "#03363D"

    inputs = [
        NodeField(
            name="subdomain",
            label="Subdomain",
            type=FieldType.STRING,
            required=True,
            description="Your Zendesk subdomain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Admin/agent email address.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="zendesk",
            description="Zendesk API token.",
        ),
        NodeField(
            name="ticket_id",
            label="Ticket ID",
            type=FieldType.NUMBER,
            required=True,
            description="The ID of the ticket to update.",
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.SELECT,
            required=False,
            options=[
                {"value": "new", "label": "New"},
                {"value": "open", "label": "Open"},
                {"value": "pending", "label": "Pending"},
                {"value": "hold", "label": "On-hold"},
                {"value": "solved", "label": "Solved"},
                {"value": "closed", "label": "Closed"},
            ],
            description="New ticket status.",
        ),
        NodeField(
            name="priority",
            label="Priority",
            type=FieldType.SELECT,
            required=False,
            options=[
                {"value": "low", "label": "Low"},
                {"value": "normal", "label": "Normal"},
                {"value": "high", "label": "High"},
                {"value": "urgent", "label": "Urgent"},
            ],
            description="New ticket priority.",
        ),
        NodeField(
            name="assignee_id",
            label="Assignee ID",
            type=FieldType.NUMBER,
            required=False,
            description="User ID to assign the ticket to.",
        ),
        NodeField(
            name="tags",
            label="Tags",
            type=FieldType.STRING,
            required=False,
            description="Comma-separated list of tags (replaces existing).",
        ),
    ]

    outputs = [
        NodeField(
            name="ticket",
            label="Ticket",
            type=FieldType.JSON,
            required=True,
            description="The updated ticket data.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Update a Zendesk ticket."""
        subdomain = config.get("subdomain")
        email = config.get("email")
        api_token = config.get("api_token")
        ticket_id = config.get("ticket_id")
        status = config.get("status", "")
        priority = config.get("priority", "")
        assignee_id = config.get("assignee_id")
        tags = config.get("tags", "")

        if not subdomain:
            raise ValueError("Subdomain is required")
        if not email:
            raise ValueError("Email is required")
        if not api_token:
            raise ValueError("API token is required")
        if not ticket_id:
            raise ValueError("Ticket ID is required")

        url = f"{_get_base_url(subdomain)}/tickets/{ticket_id}.json"

        ticket_data: dict[str, Any] = {}
        if status:
            ticket_data["status"] = status
        if priority:
            ticket_data["priority"] = priority
        if assignee_id:
            ticket_data["assignee_id"] = assignee_id
        if tags:
            ticket_data["tags"] = [t.strip() for t in tags.split(",")]

        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                json={"ticket": ticket_data},
                auth=_get_auth(email, api_token),
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"Zendesk API error: {response.status_code} - {response.text}")

        data = response.json()
        return {"success": True, "ticket": data.get("ticket", {})}


class ZendeskListTicketsNode(BaseNode):
    """List Zendesk tickets."""

    name = "zendesk_list_tickets"
    display_name = "Zendesk List Tickets"
    category = "apps"
    description = "List Zendesk tickets with optional filters"
    icon = "zendesk"
    color = "#03363D"

    inputs = [
        NodeField(
            name="subdomain",
            label="Subdomain",
            type=FieldType.STRING,
            required=True,
            description="Your Zendesk subdomain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Admin/agent email address.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="zendesk",
            description="Zendesk API token.",
        ),
        NodeField(
            name="status",
            label="Status Filter",
            type=FieldType.SELECT,
            required=False,
            options=[
                {"value": "new", "label": "New"},
                {"value": "open", "label": "Open"},
                {"value": "pending", "label": "Pending"},
                {"value": "hold", "label": "On-hold"},
                {"value": "solved", "label": "Solved"},
            ],
            description="Filter by ticket status.",
        ),
        NodeField(
            name="sort_by",
            label="Sort By",
            type=FieldType.SELECT,
            required=False,
            default="created_at",
            options=[
                {"value": "created_at", "label": "Created At"},
                {"value": "updated_at", "label": "Updated At"},
                {"value": "priority", "label": "Priority"},
                {"value": "status", "label": "Status"},
            ],
            description="Field to sort by.",
        ),
        NodeField(
            name="sort_order",
            label="Sort Order",
            type=FieldType.SELECT,
            required=False,
            default="desc",
            options=[
                {"value": "asc", "label": "Ascending"},
                {"value": "desc", "label": "Descending"},
            ],
            description="Sort order.",
        ),
    ]

    outputs = [
        NodeField(
            name="tickets",
            label="Tickets",
            type=FieldType.JSON,
            required=True,
            description="List of tickets.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            required=True,
            description="Number of tickets returned.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """List Zendesk tickets."""
        subdomain = config.get("subdomain")
        email = config.get("email")
        api_token = config.get("api_token")
        status = config.get("status", "")
        sort_by = config.get("sort_by", "created_at")
        sort_order = config.get("sort_order", "desc")

        if not subdomain:
            raise ValueError("Subdomain is required")
        if not email:
            raise ValueError("Email is required")
        if not api_token:
            raise ValueError("API token is required")

        url = f"{_get_base_url(subdomain)}/tickets.json"
        params: dict[str, Any] = {
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                auth=_get_auth(email, api_token),
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"Zendesk API error: {response.status_code} - {response.text}")

        data = response.json()
        tickets = data.get("tickets", [])

        # Filter by status if specified
        if status:
            tickets = [t for t in tickets if t.get("status") == status]

        return {
            "success": True,
            "tickets": tickets,
            "count": len(tickets),
        }


class ZendeskSearchTicketsNode(BaseNode):
    """Search Zendesk tickets."""

    name = "zendesk_search_tickets"
    display_name = "Zendesk Search Tickets"
    category = "apps"
    description = "Search Zendesk tickets using query"
    icon = "zendesk"
    color = "#03363D"

    inputs = [
        NodeField(
            name="subdomain",
            label="Subdomain",
            type=FieldType.STRING,
            required=True,
            description="Your Zendesk subdomain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Admin/agent email address.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="zendesk",
            description="Zendesk API token.",
        ),
        NodeField(
            name="query",
            label="Query",
            type=FieldType.STRING,
            required=True,
            description="Search query (Zendesk search syntax).",
        ),
        NodeField(
            name="sort_by",
            label="Sort By",
            type=FieldType.SELECT,
            required=False,
            default="created_at",
            options=[
                {"value": "created_at", "label": "Created At"},
                {"value": "updated_at", "label": "Updated At"},
                {"value": "priority", "label": "Priority"},
                {"value": "status", "label": "Status"},
                {"value": "ticket_type", "label": "Ticket Type"},
            ],
            description="Field to sort by.",
        ),
        NodeField(
            name="sort_order",
            label="Sort Order",
            type=FieldType.SELECT,
            required=False,
            default="desc",
            options=[
                {"value": "asc", "label": "Ascending"},
                {"value": "desc", "label": "Descending"},
            ],
            description="Sort order.",
        ),
    ]

    outputs = [
        NodeField(
            name="tickets",
            label="Tickets",
            type=FieldType.JSON,
            required=True,
            description="List of matching tickets.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            required=True,
            description="Number of matching tickets.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Search Zendesk tickets."""
        subdomain = config.get("subdomain")
        email = config.get("email")
        api_token = config.get("api_token")
        query = config.get("query")
        sort_by = config.get("sort_by", "created_at")
        sort_order = config.get("sort_order", "desc")

        if not subdomain:
            raise ValueError("Subdomain is required")
        if not email:
            raise ValueError("Email is required")
        if not api_token:
            raise ValueError("API token is required")
        if not query:
            raise ValueError("Query is required")

        url = f"{_get_base_url(subdomain)}/search.json"
        params = {
            "query": f"type:ticket {query}",
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                auth=_get_auth(email, api_token),
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"Zendesk API error: {response.status_code} - {response.text}")

        data = response.json()
        results = data.get("results", [])
        return {
            "success": True,
            "tickets": results,
            "count": data.get("count", len(results)),
        }


class ZendeskAddCommentNode(BaseNode):
    """Add a comment to a Zendesk ticket."""

    name = "zendesk_add_comment"
    display_name = "Zendesk Add Comment"
    category = "apps"
    description = "Add a comment to an existing Zendesk ticket"
    icon = "zendesk"
    color = "#03363D"

    inputs = [
        NodeField(
            name="subdomain",
            label="Subdomain",
            type=FieldType.STRING,
            required=True,
            description="Your Zendesk subdomain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Admin/agent email address.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="zendesk",
            description="Zendesk API token.",
        ),
        NodeField(
            name="ticket_id",
            label="Ticket ID",
            type=FieldType.NUMBER,
            required=True,
            description="The ID of the ticket to comment on.",
        ),
        NodeField(
            name="body",
            label="Comment Body",
            type=FieldType.STRING,
            required=True,
            description="The comment text.",
        ),
        NodeField(
            name="public",
            label="Public",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
            description="Whether the comment is public (visible to requester).",
        ),
    ]

    outputs = [
        NodeField(
            name="ticket",
            label="Ticket",
            type=FieldType.JSON,
            required=True,
            description="The updated ticket data.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Add a comment to a Zendesk ticket."""
        subdomain = config.get("subdomain")
        email = config.get("email")
        api_token = config.get("api_token")
        ticket_id = config.get("ticket_id")
        body = config.get("body")
        public = config.get("public", True)

        if not subdomain:
            raise ValueError("Subdomain is required")
        if not email:
            raise ValueError("Email is required")
        if not api_token:
            raise ValueError("API token is required")
        if not ticket_id:
            raise ValueError("Ticket ID is required")
        if not body:
            raise ValueError("Comment body is required")

        url = f"{_get_base_url(subdomain)}/tickets/{ticket_id}.json"

        ticket_data = {
            "comment": {
                "body": body,
                "public": public,
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                json={"ticket": ticket_data},
                auth=_get_auth(email, api_token),
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"Zendesk API error: {response.status_code} - {response.text}")

        data = response.json()
        return {"success": True, "ticket": data.get("ticket", {})}


class ZendeskGetUserNode(BaseNode):
    """Get a Zendesk user by ID."""

    name = "zendesk_get_user"
    display_name = "Zendesk Get User"
    category = "apps"
    description = "Get a Zendesk user by ID"
    icon = "zendesk"
    color = "#03363D"

    inputs = [
        NodeField(
            name="subdomain",
            label="Subdomain",
            type=FieldType.STRING,
            required=True,
            description="Your Zendesk subdomain.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Admin/agent email address.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="zendesk",
            description="Zendesk API token.",
        ),
        NodeField(
            name="user_id",
            label="User ID",
            type=FieldType.NUMBER,
            required=True,
            description="The ID of the user to retrieve.",
        ),
    ]

    outputs = [
        NodeField(
            name="user",
            label="User",
            type=FieldType.JSON,
            required=True,
            description="The user data.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Get a Zendesk user."""
        subdomain = config.get("subdomain")
        email = config.get("email")
        api_token = config.get("api_token")
        user_id = config.get("user_id")

        if not subdomain:
            raise ValueError("Subdomain is required")
        if not email:
            raise ValueError("Email is required")
        if not api_token:
            raise ValueError("API token is required")
        if not user_id:
            raise ValueError("User ID is required")

        url = f"{_get_base_url(subdomain)}/users/{user_id}.json"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                auth=_get_auth(email, api_token),
                timeout=30.0,
            )

        if response.status_code != 200:
            raise ValueError(f"Zendesk API error: {response.status_code} - {response.text}")

        data = response.json()
        return {"success": True, "user": data.get("user", {})}


class ZendeskCreateUserNode(BaseNode):
    """Create a Zendesk user."""

    name = "zendesk_create_user"
    display_name = "Zendesk Create User"
    category = "apps"
    description = "Create a new Zendesk user"
    icon = "zendesk"
    color = "#03363D"

    inputs = [
        NodeField(
            name="subdomain",
            label="Subdomain",
            type=FieldType.STRING,
            required=True,
            description="Your Zendesk subdomain.",
        ),
        NodeField(
            name="email",
            label="Admin Email",
            type=FieldType.STRING,
            required=True,
            description="Admin/agent email address.",
        ),
        NodeField(
            name="api_token",
            label="API Token",
            type=FieldType.CREDENTIAL,
            required=True,
            credential_service="zendesk",
            description="Zendesk API token.",
        ),
        NodeField(
            name="user_name",
            label="Name",
            type=FieldType.STRING,
            required=True,
            description="User's full name.",
        ),
        NodeField(
            name="user_email",
            label="User Email",
            type=FieldType.STRING,
            required=True,
            description="User's email address.",
        ),
        NodeField(
            name="role",
            label="Role",
            type=FieldType.SELECT,
            required=False,
            default="end-user",
            options=[
                {"value": "end-user", "label": "End User"},
                {"value": "agent", "label": "Agent"},
                {"value": "admin", "label": "Admin"},
            ],
            description="User role.",
        ),
        NodeField(
            name="phone",
            label="Phone",
            type=FieldType.STRING,
            required=False,
            description="User's phone number.",
        ),
    ]

    outputs = [
        NodeField(
            name="user",
            label="User",
            type=FieldType.JSON,
            required=True,
            description="The created user data.",
        ),
        NodeField(
            name="user_id",
            label="User ID",
            type=FieldType.NUMBER,
            required=True,
            description="The ID of the created user.",
        ),
    ]

    async def execute(self, config: dict, input_data: dict) -> dict[str, Any]:
        """Create a Zendesk user."""
        subdomain = config.get("subdomain")
        email = config.get("email")
        api_token = config.get("api_token")
        user_name = config.get("user_name")
        user_email = config.get("user_email")
        role = config.get("role", "end-user")
        phone = config.get("phone", "")

        if not subdomain:
            raise ValueError("Subdomain is required")
        if not email:
            raise ValueError("Admin email is required")
        if not api_token:
            raise ValueError("API token is required")
        if not user_name:
            raise ValueError("User name is required")
        if not user_email:
            raise ValueError("User email is required")

        url = f"{_get_base_url(subdomain)}/users.json"

        user_data: dict[str, Any] = {
            "name": user_name,
            "email": user_email,
            "role": role,
        }
        if phone:
            user_data["phone"] = phone

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"user": user_data},
                auth=_get_auth(email, api_token),
                timeout=30.0,
            )

        if response.status_code != 201:
            raise ValueError(f"Zendesk API error: {response.status_code} - {response.text}")

        data = response.json()
        user = data.get("user", {})
        return {
            "success": True,
            "user": user,
            "user_id": user.get("id"),
        }
