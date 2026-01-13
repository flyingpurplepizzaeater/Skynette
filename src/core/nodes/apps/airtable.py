"""
Airtable Integration Nodes - Query and manipulate Airtable bases.

Uses Airtable REST API with Personal Access Token authentication.
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


def _get_api_key(config: dict) -> str:
    """Get API key from config or credential."""
    credential_id = config.get("credential")
    cred_data = _get_credential(credential_id) if credential_id else None

    if cred_data:
        return cred_data.get("api_key", "") or cred_data.get("access_token", "")

    return config.get("api_key", "")


class AirtableListBasesNode(BaseNode):
    """
    List all Airtable bases accessible to the user.
    """

    type = "airtable-list-bases"
    name = "Airtable: List Bases"
    category = "Apps"
    description = "List all Airtable bases"
    icon = "table_chart"
    color = "#18BFFF"  # Airtable blue

    inputs = [
        NodeField(
            name="credential",
            label="Airtable Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Airtable credential.",
            credential_service="airtable",
        ),
        NodeField(
            name="api_key",
            label="API Key / PAT",
            type=FieldType.SECRET,
            required=False,
            description="Airtable Personal Access Token (or use saved credential).",
        ),
    ]

    outputs = [
        NodeField(
            name="bases",
            label="Bases",
            type=FieldType.JSON,
            description="List of bases.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of bases.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List Airtable bases."""
        import httpx

        api_key = _get_api_key(config)
        if not api_key:
            raise ValueError("API key required")

        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        url = "https://api.airtable.com/v0/meta/bases"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                bases = data.get("bases", [])
                return {
                    "bases": bases,
                    "count": len(bases),
                }
            else:
                return {
                    "bases": [],
                    "count": 0,
                }


class AirtableListRecordsNode(BaseNode):
    """
    List records from an Airtable table.
    """

    type = "airtable-list-records"
    name = "Airtable: List Records"
    category = "Apps"
    description = "List records from an Airtable table"
    icon = "list"
    color = "#18BFFF"

    inputs = [
        NodeField(
            name="credential",
            label="Airtable Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Airtable credential.",
            credential_service="airtable",
        ),
        NodeField(
            name="api_key",
            label="API Key / PAT",
            type=FieldType.SECRET,
            required=False,
            description="Airtable Personal Access Token.",
        ),
        NodeField(
            name="base_id",
            label="Base ID",
            type=FieldType.STRING,
            required=True,
            description="Airtable base ID (starts with 'app').",
        ),
        NodeField(
            name="table_name",
            label="Table Name",
            type=FieldType.STRING,
            required=True,
            description="Name or ID of the table.",
        ),
        NodeField(
            name="view",
            label="View",
            type=FieldType.STRING,
            required=False,
            description="View name to filter records.",
        ),
        NodeField(
            name="filter_formula",
            label="Filter Formula",
            type=FieldType.STRING,
            required=False,
            description="Airtable formula to filter records.",
        ),
        NodeField(
            name="sort_field",
            label="Sort Field",
            type=FieldType.STRING,
            required=False,
            description="Field name to sort by.",
        ),
        NodeField(
            name="sort_direction",
            label="Sort Direction",
            type=FieldType.SELECT,
            required=False,
            default="asc",
            options=[
                {"value": "asc", "label": "Ascending"},
                {"value": "desc", "label": "Descending"},
            ],
            description="Sort direction.",
        ),
        NodeField(
            name="max_records",
            label="Max Records",
            type=FieldType.NUMBER,
            required=False,
            default=100,
            description="Maximum number of records to return.",
        ),
    ]

    outputs = [
        NodeField(
            name="records",
            label="Records",
            type=FieldType.JSON,
            description="List of records with fields.",
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
            description="Number of records returned.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List Airtable records."""
        import httpx
        from urllib.parse import quote

        api_key = _get_api_key(config)
        if not api_key:
            raise ValueError("API key required")

        base_id = config.get("base_id", "")
        table_name = config.get("table_name", "")

        if not base_id:
            raise ValueError("Base ID is required")
        if not table_name:
            raise ValueError("Table name is required")

        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        params = {}

        if config.get("view"):
            params["view"] = config["view"]
        if config.get("filter_formula"):
            params["filterByFormula"] = config["filter_formula"]
        if config.get("max_records"):
            params["maxRecords"] = str(config["max_records"])
        if config.get("sort_field"):
            params["sort[0][field]"] = config["sort_field"]
            params["sort[0][direction]"] = config.get("sort_direction", "asc")

        # URL-encode table name
        encoded_table = quote(table_name, safe="")
        url = f"https://api.airtable.com/v0/{base_id}/{encoded_table}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                records = data.get("records", [])
                return {
                    "records": records,
                    "count": len(records),
                }
            else:
                return {
                    "records": [],
                    "count": 0,
                }


class AirtableGetRecordNode(BaseNode):
    """
    Get a single record from Airtable by ID.
    """

    type = "airtable-get-record"
    name = "Airtable: Get Record"
    category = "Apps"
    description = "Get a single record by ID"
    icon = "search"
    color = "#18BFFF"

    inputs = [
        NodeField(
            name="credential",
            label="Airtable Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Airtable credential.",
            credential_service="airtable",
        ),
        NodeField(
            name="api_key",
            label="API Key / PAT",
            type=FieldType.SECRET,
            required=False,
            description="Airtable Personal Access Token.",
        ),
        NodeField(
            name="base_id",
            label="Base ID",
            type=FieldType.STRING,
            required=True,
            description="Airtable base ID.",
        ),
        NodeField(
            name="table_name",
            label="Table Name",
            type=FieldType.STRING,
            required=True,
            description="Name or ID of the table.",
        ),
        NodeField(
            name="record_id",
            label="Record ID",
            type=FieldType.STRING,
            required=True,
            description="ID of the record (starts with 'rec').",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the record was found.",
        ),
        NodeField(
            name="record",
            label="Record",
            type=FieldType.JSON,
            description="The record data.",
        ),
        NodeField(
            name="fields",
            label="Fields",
            type=FieldType.JSON,
            description="The record's fields.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Get single Airtable record."""
        import httpx
        from urllib.parse import quote

        api_key = _get_api_key(config)
        if not api_key:
            raise ValueError("API key required")

        base_id = config.get("base_id", "")
        table_name = config.get("table_name", "")
        record_id = config.get("record_id", "")

        if not base_id:
            raise ValueError("Base ID is required")
        if not table_name:
            raise ValueError("Table name is required")
        if not record_id:
            raise ValueError("Record ID is required")

        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        encoded_table = quote(table_name, safe="")
        url = f"https://api.airtable.com/v0/{base_id}/{encoded_table}/{record_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                record = response.json()
                return {
                    "success": True,
                    "record": record,
                    "fields": record.get("fields", {}),
                }
            else:
                return {
                    "success": False,
                    "record": {},
                    "fields": {},
                }


class AirtableCreateRecordNode(BaseNode):
    """
    Create a new record in Airtable.
    """

    type = "airtable-create-record"
    name = "Airtable: Create Record"
    category = "Apps"
    description = "Create a new record in Airtable"
    icon = "add_box"
    color = "#18BFFF"

    inputs = [
        NodeField(
            name="credential",
            label="Airtable Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Airtable credential.",
            credential_service="airtable",
        ),
        NodeField(
            name="api_key",
            label="API Key / PAT",
            type=FieldType.SECRET,
            required=False,
            description="Airtable Personal Access Token.",
        ),
        NodeField(
            name="base_id",
            label="Base ID",
            type=FieldType.STRING,
            required=True,
            description="Airtable base ID.",
        ),
        NodeField(
            name="table_name",
            label="Table Name",
            type=FieldType.STRING,
            required=True,
            description="Name or ID of the table.",
        ),
        NodeField(
            name="fields",
            label="Fields",
            type=FieldType.JSON,
            required=True,
            description="Record fields as JSON object.",
        ),
        NodeField(
            name="typecast",
            label="Typecast",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Auto-convert field values to correct types.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the record was created.",
        ),
        NodeField(
            name="record_id",
            label="Record ID",
            type=FieldType.STRING,
            description="ID of the created record.",
        ),
        NodeField(
            name="record",
            label="Record",
            type=FieldType.JSON,
            description="The created record.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Create Airtable record."""
        import httpx
        import json
        from urllib.parse import quote

        api_key = _get_api_key(config)
        if not api_key:
            raise ValueError("API key required")

        base_id = config.get("base_id", "")
        table_name = config.get("table_name", "")
        fields = config.get("fields", {})
        typecast = config.get("typecast", False)

        if not base_id:
            raise ValueError("Base ID is required")
        if not table_name:
            raise ValueError("Table name is required")

        # Parse fields if string
        if isinstance(fields, str):
            try:
                fields = json.loads(fields)
            except:
                fields = {}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "fields": fields,
            "typecast": typecast,
        }

        encoded_table = quote(table_name, safe="")
        url = f"https://api.airtable.com/v0/{base_id}/{encoded_table}"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)

            if response.status_code == 200:
                record = response.json()
                return {
                    "success": True,
                    "record_id": record.get("id", ""),
                    "record": record,
                }
            else:
                return {
                    "success": False,
                    "record_id": "",
                    "record": {},
                }


class AirtableUpdateRecordNode(BaseNode):
    """
    Update an existing record in Airtable.
    """

    type = "airtable-update-record"
    name = "Airtable: Update Record"
    category = "Apps"
    description = "Update an existing record in Airtable"
    icon = "edit"
    color = "#18BFFF"

    inputs = [
        NodeField(
            name="credential",
            label="Airtable Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Airtable credential.",
            credential_service="airtable",
        ),
        NodeField(
            name="api_key",
            label="API Key / PAT",
            type=FieldType.SECRET,
            required=False,
            description="Airtable Personal Access Token.",
        ),
        NodeField(
            name="base_id",
            label="Base ID",
            type=FieldType.STRING,
            required=True,
            description="Airtable base ID.",
        ),
        NodeField(
            name="table_name",
            label="Table Name",
            type=FieldType.STRING,
            required=True,
            description="Name or ID of the table.",
        ),
        NodeField(
            name="record_id",
            label="Record ID",
            type=FieldType.STRING,
            required=True,
            description="ID of the record to update.",
        ),
        NodeField(
            name="fields",
            label="Fields",
            type=FieldType.JSON,
            required=True,
            description="Fields to update as JSON object.",
        ),
        NodeField(
            name="typecast",
            label="Typecast",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Auto-convert field values.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the record was updated.",
        ),
        NodeField(
            name="record",
            label="Record",
            type=FieldType.JSON,
            description="The updated record.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Update Airtable record."""
        import httpx
        import json
        from urllib.parse import quote

        api_key = _get_api_key(config)
        if not api_key:
            raise ValueError("API key required")

        base_id = config.get("base_id", "")
        table_name = config.get("table_name", "")
        record_id = config.get("record_id", "")
        fields = config.get("fields", {})
        typecast = config.get("typecast", False)

        if not base_id:
            raise ValueError("Base ID is required")
        if not table_name:
            raise ValueError("Table name is required")
        if not record_id:
            raise ValueError("Record ID is required")

        # Parse fields if string
        if isinstance(fields, str):
            try:
                fields = json.loads(fields)
            except:
                fields = {}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "fields": fields,
            "typecast": typecast,
        }

        encoded_table = quote(table_name, safe="")
        url = f"https://api.airtable.com/v0/{base_id}/{encoded_table}/{record_id}"

        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=headers, json=body)

            if response.status_code == 200:
                record = response.json()
                return {
                    "success": True,
                    "record": record,
                }
            else:
                return {
                    "success": False,
                    "record": {},
                }


class AirtableDeleteRecordNode(BaseNode):
    """
    Delete a record from Airtable.
    """

    type = "airtable-delete-record"
    name = "Airtable: Delete Record"
    category = "Apps"
    description = "Delete a record from Airtable"
    icon = "delete"
    color = "#18BFFF"

    inputs = [
        NodeField(
            name="credential",
            label="Airtable Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Airtable credential.",
            credential_service="airtable",
        ),
        NodeField(
            name="api_key",
            label="API Key / PAT",
            type=FieldType.SECRET,
            required=False,
            description="Airtable Personal Access Token.",
        ),
        NodeField(
            name="base_id",
            label="Base ID",
            type=FieldType.STRING,
            required=True,
            description="Airtable base ID.",
        ),
        NodeField(
            name="table_name",
            label="Table Name",
            type=FieldType.STRING,
            required=True,
            description="Name or ID of the table.",
        ),
        NodeField(
            name="record_id",
            label="Record ID",
            type=FieldType.STRING,
            required=True,
            description="ID of the record to delete.",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the record was deleted.",
        ),
        NodeField(
            name="deleted_id",
            label="Deleted ID",
            type=FieldType.STRING,
            description="ID of the deleted record.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Delete Airtable record."""
        import httpx
        from urllib.parse import quote

        api_key = _get_api_key(config)
        if not api_key:
            raise ValueError("API key required")

        base_id = config.get("base_id", "")
        table_name = config.get("table_name", "")
        record_id = config.get("record_id", "")

        if not base_id:
            raise ValueError("Base ID is required")
        if not table_name:
            raise ValueError("Table name is required")
        if not record_id:
            raise ValueError("Record ID is required")

        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        encoded_table = quote(table_name, safe="")
        url = f"https://api.airtable.com/v0/{base_id}/{encoded_table}/{record_id}"

        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": data.get("deleted", False),
                    "deleted_id": data.get("id", ""),
                }
            else:
                return {
                    "success": False,
                    "deleted_id": "",
                }
