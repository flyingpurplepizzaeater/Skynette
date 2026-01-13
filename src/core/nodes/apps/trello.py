"""
Trello Integration Nodes - Manage boards, lists, and cards.

Uses Trello REST API with API key + token authentication.
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


def _get_auth_params(config: dict) -> dict:
    """Get API key and token from config or credential."""
    credential_id = config.get("credential")
    cred_data = _get_credential(credential_id) if credential_id else None

    if cred_data:
        return {
            "key": cred_data.get("api_key", ""),
            "token": cred_data.get("token", ""),
        }

    return {
        "key": config.get("api_key", ""),
        "token": config.get("token", ""),
    }


class TrelloListBoardsNode(BaseNode):
    """
    List all Trello boards accessible to the user.
    """

    type = "trello-list-boards"
    name = "Trello: List Boards"
    category = "Apps"
    description = "List all Trello boards"
    icon = "dashboard"
    color = "#0079BF"  # Trello blue

    inputs = [
        NodeField(
            name="credential",
            label="Trello Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Trello credential.",
            credential_service="trello",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="Trello API key (or use saved credential).",
        ),
        NodeField(
            name="token",
            label="Token",
            type=FieldType.SECRET,
            required=False,
            description="Trello API token (or use saved credential).",
        ),
        NodeField(
            name="filter",
            label="Filter",
            type=FieldType.SELECT,
            required=False,
            default="all",
            options=[
                {"value": "all", "label": "All"},
                {"value": "open", "label": "Open"},
                {"value": "closed", "label": "Closed"},
                {"value": "starred", "label": "Starred"},
            ],
            description="Filter boards by status.",
        ),
    ]

    outputs = [
        NodeField(
            name="boards",
            label="Boards",
            type=FieldType.JSON,
            description="List of boards.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of boards.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List Trello boards."""
        import httpx

        auth = _get_auth_params(config)
        if not auth["key"] or not auth["token"]:
            raise ValueError("API key and token required")

        filter_type = config.get("filter", "all")

        params = {
            "key": auth["key"],
            "token": auth["token"],
            "filter": filter_type,
        }

        url = "https://api.trello.com/1/members/me/boards"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                boards = response.json()
                return {
                    "boards": boards,
                    "count": len(boards),
                }
            else:
                return {
                    "boards": [],
                    "count": 0,
                }


class TrelloListListsNode(BaseNode):
    """
    List all lists in a Trello board.
    """

    type = "trello-list-lists"
    name = "Trello: List Lists"
    category = "Apps"
    description = "List all lists in a Trello board"
    icon = "view_list"
    color = "#0079BF"

    inputs = [
        NodeField(
            name="credential",
            label="Trello Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Trello credential.",
            credential_service="trello",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="Trello API key.",
        ),
        NodeField(
            name="token",
            label="Token",
            type=FieldType.SECRET,
            required=False,
            description="Trello API token.",
        ),
        NodeField(
            name="board_id",
            label="Board ID",
            type=FieldType.STRING,
            required=True,
            description="ID of the board.",
        ),
        NodeField(
            name="filter",
            label="Filter",
            type=FieldType.SELECT,
            required=False,
            default="open",
            options=[
                {"value": "all", "label": "All"},
                {"value": "open", "label": "Open"},
                {"value": "closed", "label": "Closed"},
            ],
            description="Filter lists by status.",
        ),
    ]

    outputs = [
        NodeField(
            name="lists",
            label="Lists",
            type=FieldType.JSON,
            description="List of lists in the board.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of lists.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List Trello lists in a board."""
        import httpx

        auth = _get_auth_params(config)
        if not auth["key"] or not auth["token"]:
            raise ValueError("API key and token required")

        board_id = config.get("board_id", "")
        if not board_id:
            raise ValueError("Board ID is required")

        filter_type = config.get("filter", "open")

        params = {
            "key": auth["key"],
            "token": auth["token"],
            "filter": filter_type,
        }

        url = f"https://api.trello.com/1/boards/{board_id}/lists"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                lists = response.json()
                return {
                    "lists": lists,
                    "count": len(lists),
                }
            else:
                return {
                    "lists": [],
                    "count": 0,
                }


class TrelloListCardsNode(BaseNode):
    """
    List cards in a Trello board or list.
    """

    type = "trello-list-cards"
    name = "Trello: List Cards"
    category = "Apps"
    description = "List cards in a board or list"
    icon = "assignment"
    color = "#0079BF"

    inputs = [
        NodeField(
            name="credential",
            label="Trello Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Trello credential.",
            credential_service="trello",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="Trello API key.",
        ),
        NodeField(
            name="token",
            label="Token",
            type=FieldType.SECRET,
            required=False,
            description="Trello API token.",
        ),
        NodeField(
            name="source_type",
            label="Source",
            type=FieldType.SELECT,
            required=True,
            default="list",
            options=[
                {"value": "list", "label": "From List"},
                {"value": "board", "label": "From Board"},
            ],
            description="Get cards from a list or entire board.",
        ),
        NodeField(
            name="board_id",
            label="Board ID",
            type=FieldType.STRING,
            required=False,
            description="Board ID (required if source is board).",
        ),
        NodeField(
            name="list_id",
            label="List ID",
            type=FieldType.STRING,
            required=False,
            description="List ID (required if source is list).",
        ),
        NodeField(
            name="filter",
            label="Filter",
            type=FieldType.SELECT,
            required=False,
            default="open",
            options=[
                {"value": "all", "label": "All"},
                {"value": "open", "label": "Open"},
                {"value": "closed", "label": "Closed"},
            ],
            description="Filter cards by status.",
        ),
    ]

    outputs = [
        NodeField(
            name="cards",
            label="Cards",
            type=FieldType.JSON,
            description="List of cards.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of cards.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List Trello cards."""
        import httpx

        auth = _get_auth_params(config)
        if not auth["key"] or not auth["token"]:
            raise ValueError("API key and token required")

        source_type = config.get("source_type", "list")
        filter_type = config.get("filter", "open")

        params = {
            "key": auth["key"],
            "token": auth["token"],
            "filter": filter_type,
        }

        if source_type == "list":
            list_id = config.get("list_id", "")
            if not list_id:
                raise ValueError("List ID is required")
            url = f"https://api.trello.com/1/lists/{list_id}/cards"
        else:
            board_id = config.get("board_id", "")
            if not board_id:
                raise ValueError("Board ID is required")
            url = f"https://api.trello.com/1/boards/{board_id}/cards"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                cards = response.json()
                return {
                    "cards": cards,
                    "count": len(cards),
                }
            else:
                return {
                    "cards": [],
                    "count": 0,
                }


class TrelloCreateCardNode(BaseNode):
    """
    Create a new card in a Trello list.
    """

    type = "trello-create-card"
    name = "Trello: Create Card"
    category = "Apps"
    description = "Create a new card in a Trello list"
    icon = "add_box"
    color = "#0079BF"

    inputs = [
        NodeField(
            name="credential",
            label="Trello Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Trello credential.",
            credential_service="trello",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="Trello API key.",
        ),
        NodeField(
            name="token",
            label="Token",
            type=FieldType.SECRET,
            required=False,
            description="Trello API token.",
        ),
        NodeField(
            name="list_id",
            label="List ID",
            type=FieldType.STRING,
            required=True,
            description="ID of the list to add the card to.",
        ),
        NodeField(
            name="name",
            label="Card Name",
            type=FieldType.STRING,
            required=True,
            description="Name/title of the card.",
        ),
        NodeField(
            name="description",
            label="Description",
            type=FieldType.TEXT,
            required=False,
            description="Card description (supports Markdown).",
        ),
        NodeField(
            name="position",
            label="Position",
            type=FieldType.SELECT,
            required=False,
            default="bottom",
            options=[
                {"value": "top", "label": "Top"},
                {"value": "bottom", "label": "Bottom"},
            ],
            description="Position in the list.",
        ),
        NodeField(
            name="due_date",
            label="Due Date",
            type=FieldType.STRING,
            required=False,
            description="Due date in ISO 8601 format.",
        ),
        NodeField(
            name="labels",
            label="Label IDs",
            type=FieldType.STRING,
            required=False,
            description="Comma-separated label IDs.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the card was created.",
        ),
        NodeField(
            name="card_id",
            label="Card ID",
            type=FieldType.STRING,
            description="ID of the created card.",
        ),
        NodeField(
            name="card_url",
            label="Card URL",
            type=FieldType.STRING,
            description="URL to view the card.",
        ),
        NodeField(
            name="card",
            label="Card",
            type=FieldType.JSON,
            description="Full card data.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Create Trello card."""
        import httpx

        auth = _get_auth_params(config)
        if not auth["key"] or not auth["token"]:
            raise ValueError("API key and token required")

        list_id = config.get("list_id", "")
        name = config.get("name", "")

        if not list_id:
            raise ValueError("List ID is required")
        if not name:
            raise ValueError("Card name is required")

        params = {
            "key": auth["key"],
            "token": auth["token"],
            "idList": list_id,
            "name": name,
            "pos": config.get("position", "bottom"),
        }

        if config.get("description"):
            params["desc"] = config["description"]
        if config.get("due_date"):
            params["due"] = config["due_date"]
        if config.get("labels"):
            params["idLabels"] = config["labels"]

        url = "https://api.trello.com/1/cards"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, params=params)

            if response.status_code == 200:
                card = response.json()
                return {
                    "success": True,
                    "card_id": card.get("id", ""),
                    "card_url": card.get("url", ""),
                    "card": card,
                }
            else:
                return {
                    "success": False,
                    "card_id": "",
                    "card_url": "",
                    "card": {},
                }


class TrelloUpdateCardNode(BaseNode):
    """
    Update an existing Trello card.
    """

    type = "trello-update-card"
    name = "Trello: Update Card"
    category = "Apps"
    description = "Update an existing Trello card"
    icon = "edit"
    color = "#0079BF"

    inputs = [
        NodeField(
            name="credential",
            label="Trello Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Trello credential.",
            credential_service="trello",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="Trello API key.",
        ),
        NodeField(
            name="token",
            label="Token",
            type=FieldType.SECRET,
            required=False,
            description="Trello API token.",
        ),
        NodeField(
            name="card_id",
            label="Card ID",
            type=FieldType.STRING,
            required=True,
            description="ID of the card to update.",
        ),
        NodeField(
            name="name",
            label="Card Name",
            type=FieldType.STRING,
            required=False,
            description="New name for the card.",
        ),
        NodeField(
            name="description",
            label="Description",
            type=FieldType.TEXT,
            required=False,
            description="New description.",
        ),
        NodeField(
            name="list_id",
            label="Move to List ID",
            type=FieldType.STRING,
            required=False,
            description="Move card to this list.",
        ),
        NodeField(
            name="due_date",
            label="Due Date",
            type=FieldType.STRING,
            required=False,
            description="New due date (ISO 8601 format).",
        ),
        NodeField(
            name="closed",
            label="Archive Card",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Archive (close) the card.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the update succeeded.",
        ),
        NodeField(
            name="card",
            label="Card",
            type=FieldType.JSON,
            description="Updated card data.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Update Trello card."""
        import httpx

        auth = _get_auth_params(config)
        if not auth["key"] or not auth["token"]:
            raise ValueError("API key and token required")

        card_id = config.get("card_id", "")
        if not card_id:
            raise ValueError("Card ID is required")

        params = {
            "key": auth["key"],
            "token": auth["token"],
        }

        # Add optional update fields
        if config.get("name"):
            params["name"] = config["name"]
        if config.get("description") is not None:
            params["desc"] = config["description"]
        if config.get("list_id"):
            params["idList"] = config["list_id"]
        if config.get("due_date"):
            params["due"] = config["due_date"]
        if config.get("closed"):
            params["closed"] = "true"

        url = f"https://api.trello.com/1/cards/{card_id}"

        async with httpx.AsyncClient() as client:
            response = await client.put(url, params=params)

            if response.status_code == 200:
                card = response.json()
                return {
                    "success": True,
                    "card": card,
                }
            else:
                return {
                    "success": False,
                    "card": {},
                }


class TrelloDeleteCardNode(BaseNode):
    """
    Delete a Trello card.
    """

    type = "trello-delete-card"
    name = "Trello: Delete Card"
    category = "Apps"
    description = "Delete a Trello card"
    icon = "delete"
    color = "#0079BF"

    inputs = [
        NodeField(
            name="credential",
            label="Trello Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Trello credential.",
            credential_service="trello",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="Trello API key.",
        ),
        NodeField(
            name="token",
            label="Token",
            type=FieldType.SECRET,
            required=False,
            description="Trello API token.",
        ),
        NodeField(
            name="card_id",
            label="Card ID",
            type=FieldType.STRING,
            required=True,
            description="ID of the card to delete.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the card was deleted.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Delete Trello card."""
        import httpx

        auth = _get_auth_params(config)
        if not auth["key"] or not auth["token"]:
            raise ValueError("API key and token required")

        card_id = config.get("card_id", "")
        if not card_id:
            raise ValueError("Card ID is required")

        params = {
            "key": auth["key"],
            "token": auth["token"],
        }

        url = f"https://api.trello.com/1/cards/{card_id}"

        async with httpx.AsyncClient() as client:
            response = await client.delete(url, params=params)

            return {
                "success": response.status_code == 200,
            }


class TrelloAddCommentNode(BaseNode):
    """
    Add a comment to a Trello card.
    """

    type = "trello-add-comment"
    name = "Trello: Add Comment"
    category = "Apps"
    description = "Add a comment to a Trello card"
    icon = "comment"
    color = "#0079BF"

    inputs = [
        NodeField(
            name="credential",
            label="Trello Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Trello credential.",
            credential_service="trello",
        ),
        NodeField(
            name="api_key",
            label="API Key",
            type=FieldType.SECRET,
            required=False,
            description="Trello API key.",
        ),
        NodeField(
            name="token",
            label="Token",
            type=FieldType.SECRET,
            required=False,
            description="Trello API token.",
        ),
        NodeField(
            name="card_id",
            label="Card ID",
            type=FieldType.STRING,
            required=True,
            description="ID of the card to comment on.",
        ),
        NodeField(
            name="text",
            label="Comment Text",
            type=FieldType.TEXT,
            required=True,
            description="The comment text.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the comment was added.",
        ),
        NodeField(
            name="comment_id",
            label="Comment ID",
            type=FieldType.STRING,
            description="ID of the created comment.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Add comment to Trello card."""
        import httpx

        auth = _get_auth_params(config)
        if not auth["key"] or not auth["token"]:
            raise ValueError("API key and token required")

        card_id = config.get("card_id", "")
        text = config.get("text", "")

        if not card_id:
            raise ValueError("Card ID is required")
        if not text:
            raise ValueError("Comment text is required")

        params = {
            "key": auth["key"],
            "token": auth["token"],
            "text": text,
        }

        url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, params=params)

            if response.status_code == 200:
                comment = response.json()
                return {
                    "success": True,
                    "comment_id": comment.get("id", ""),
                }
            else:
                return {
                    "success": False,
                    "comment_id": "",
                }
