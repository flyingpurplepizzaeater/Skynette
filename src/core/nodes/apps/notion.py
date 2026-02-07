"""
Notion Integration Nodes - Interact with Notion databases and pages.
"""

from typing import Any

from src.core.nodes.base import BaseNode, FieldType, NodeField


class NotionQueryDatabaseNode(BaseNode):
    """
    Query a Notion database.
    """

    type = "notion-query-database"
    name = "Notion: Query Database"
    category = "Apps"
    description = "Query items from a Notion database"
    icon = "table_chart"
    color = "#000000"  # Notion black

    inputs = [
        NodeField(
            name="api_key",
            label="Integration Token",
            type=FieldType.SECRET,
            required=True,
            description="Notion Integration secret token.",
        ),
        NodeField(
            name="database_id",
            label="Database ID",
            type=FieldType.STRING,
            required=True,
            description="Notion database ID (from URL).",
        ),
        NodeField(
            name="filter_property",
            label="Filter Property",
            type=FieldType.STRING,
            required=False,
            description="Property name to filter by.",
        ),
        NodeField(
            name="filter_value",
            label="Filter Value",
            type=FieldType.STRING,
            required=False,
            description="Value to filter for.",
        ),
        NodeField(
            name="page_size",
            label="Page Size",
            type=FieldType.NUMBER,
            required=False,
            default=100,
            description="Number of results to return.",
        ),
    ]

    outputs = [
        NodeField(
            name="results",
            label="Results",
            type=FieldType.JSON,
            description="Query results.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Query Notion database."""
        import httpx

        api_key = config.get("api_key", "")
        database_id = config.get("database_id", "")
        filter_property = config.get("filter_property")
        filter_value = config.get("filter_value")
        page_size = int(config.get("page_size", 100))

        url = f"https://api.notion.com/v1/databases/{database_id}/query"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        payload = {"page_size": page_size}

        # Add filter if specified
        if filter_property and filter_value:
            payload["filter"] = {
                "property": filter_property,
                "rich_text": {"contains": filter_value},
            }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

        results = data.get("results", [])

        # Extract simplified data
        simplified = []
        for item in results:
            props = item.get("properties", {})
            simple_item = {"id": item.get("id")}
            for prop_name, prop_data in props.items():
                simple_item[prop_name] = self._extract_property_value(prop_data)
            simplified.append(simple_item)

        return {
            "results": simplified,
            "count": len(simplified),
        }

    def _extract_property_value(self, prop_data: dict) -> Any:
        """Extract value from Notion property."""
        prop_type = prop_data.get("type")

        if prop_type == "title":
            items = prop_data.get("title", [])
            return "".join(t.get("plain_text", "") for t in items)
        elif prop_type == "rich_text":
            items = prop_data.get("rich_text", [])
            return "".join(t.get("plain_text", "") for t in items)
        elif prop_type == "number":
            return prop_data.get("number")
        elif prop_type == "select":
            select = prop_data.get("select")
            return select.get("name") if select else None
        elif prop_type == "multi_select":
            items = prop_data.get("multi_select", [])
            return [i.get("name") for i in items]
        elif prop_type == "date":
            date = prop_data.get("date")
            return date.get("start") if date else None
        elif prop_type == "checkbox":
            return prop_data.get("checkbox", False)
        elif prop_type == "url":
            return prop_data.get("url")
        elif prop_type == "email":
            return prop_data.get("email")
        elif prop_type == "phone_number":
            return prop_data.get("phone_number")
        else:
            return None


class NotionCreatePageNode(BaseNode):
    """
    Create a new page in a Notion database.
    """

    type = "notion-create-page"
    name = "Notion: Create Page"
    category = "Apps"
    description = "Create a new page in a Notion database"
    icon = "add_box"
    color = "#000000"

    inputs = [
        NodeField(
            name="api_key",
            label="Integration Token",
            type=FieldType.SECRET,
            required=True,
        ),
        NodeField(
            name="database_id",
            label="Database ID",
            type=FieldType.STRING,
            required=True,
        ),
        NodeField(
            name="properties",
            label="Properties",
            type=FieldType.JSON,
            required=True,
            description="Page properties as JSON object.",
        ),
        NodeField(
            name="content",
            label="Page Content",
            type=FieldType.TEXT,
            required=False,
            description="Initial page content (paragraph).",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
        ),
        NodeField(
            name="page_id",
            label="Page ID",
            type=FieldType.STRING,
        ),
        NodeField(
            name="page_url",
            label="Page URL",
            type=FieldType.STRING,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Create Notion page."""
        import json

        import httpx

        api_key = config.get("api_key", "")
        database_id = config.get("database_id", "")
        properties = config.get("properties", {})
        content = config.get("content", "")

        # Parse properties if string
        if isinstance(properties, str):
            properties = json.loads(properties)

        url = "https://api.notion.com/v1/pages"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        # Convert simple properties to Notion format
        notion_props = {}
        for key, value in properties.items():
            if isinstance(value, str):
                # Assume title for first property, rich_text for others
                if not notion_props:
                    notion_props[key] = {"title": [{"text": {"content": value}}]}
                else:
                    notion_props[key] = {"rich_text": [{"text": {"content": value}}]}
            elif isinstance(value, bool):
                notion_props[key] = {"checkbox": value}
            elif isinstance(value, (int, float)):
                notion_props[key] = {"number": value}

        payload = {
            "parent": {"database_id": database_id},
            "properties": notion_props,
        }

        # Add content if provided
        if content:
            payload["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": content}}]},
                }
            ]

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "page_id": data.get("id", ""),
                "page_url": data.get("url", ""),
            }

        return {
            "success": False,
            "page_id": "",
            "page_url": "",
        }


class NotionUpdatePageNode(BaseNode):
    """
    Update a Notion page.
    """

    type = "notion-update-page"
    name = "Notion: Update Page"
    category = "Apps"
    description = "Update properties of a Notion page"
    icon = "edit"
    color = "#000000"

    inputs = [
        NodeField(
            name="api_key",
            label="Integration Token",
            type=FieldType.SECRET,
            required=True,
        ),
        NodeField(
            name="page_id",
            label="Page ID",
            type=FieldType.STRING,
            required=True,
        ),
        NodeField(
            name="properties",
            label="Properties to Update",
            type=FieldType.JSON,
            required=True,
            description="Properties to update as JSON object.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Update Notion page."""
        import json

        import httpx

        api_key = config.get("api_key", "")
        page_id = config.get("page_id", "")
        properties = config.get("properties", {})

        if isinstance(properties, str):
            properties = json.loads(properties)

        url = f"https://api.notion.com/v1/pages/{page_id}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        # Convert simple properties to Notion format
        notion_props = {}
        for key, value in properties.items():
            if isinstance(value, str):
                notion_props[key] = {"rich_text": [{"text": {"content": value}}]}
            elif isinstance(value, bool):
                notion_props[key] = {"checkbox": value}
            elif isinstance(value, (int, float)):
                notion_props[key] = {"number": value}

        payload = {"properties": notion_props}

        async with httpx.AsyncClient() as client:
            response = await client.patch(url, json=payload, headers=headers)

        return {
            "success": response.status_code == 200,
        }
