"""
Google Sheets Integration Nodes - Read and write spreadsheet data.
"""

from typing import Any, Optional

from src.core.nodes.base import BaseNode, NodeField, FieldType


class GoogleSheetsReadNode(BaseNode):
    """
    Read data from Google Sheets.

    Supports:
    - Reading entire sheets or ranges
    - Multiple output formats
    - Header row detection
    """

    type = "google-sheets-read"
    name = "Google Sheets: Read"
    category = "Apps"
    description = "Read data from Google Sheets"
    icon = "table_chart"
    color = "#0F9D58"  # Google green

    inputs = [
        NodeField(
            name="credentials_json",
            label="Service Account JSON",
            type=FieldType.SECRET,
            required=True,
            description="Google Service Account credentials JSON.",
        ),
        NodeField(
            name="spreadsheet_id",
            label="Spreadsheet ID",
            type=FieldType.STRING,
            required=True,
            description="Google Sheets spreadsheet ID from URL.",
        ),
        NodeField(
            name="range",
            label="Range",
            type=FieldType.STRING,
            required=False,
            default="Sheet1",
            description="Cell range (e.g., 'Sheet1!A1:D10' or 'Sheet1').",
        ),
        NodeField(
            name="has_header",
            label="First Row is Header",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
            description="Treat first row as column headers.",
        ),
        NodeField(
            name="output_format",
            label="Output Format",
            type=FieldType.SELECT,
            required=False,
            default="objects",
            options=[
                {"value": "objects", "label": "List of Objects"},
                {"value": "arrays", "label": "List of Arrays"},
                {"value": "raw", "label": "Raw API Response"},
            ],
            description="How to format the output data.",
        ),
    ]

    outputs = [
        NodeField(
            name="data",
            label="Data",
            type=FieldType.JSON,
            description="Spreadsheet data.",
        ),
        NodeField(
            name="row_count",
            label="Row Count",
            type=FieldType.NUMBER,
            description="Number of rows returned.",
        ),
        NodeField(
            name="columns",
            label="Columns",
            type=FieldType.JSON,
            description="Column headers (if has_header is true).",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Read data from Google Sheets."""
        import json

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except ImportError:
            raise RuntimeError(
                "Google API libraries not installed. Install with: "
                "pip install google-auth google-auth-oauthlib google-api-python-client"
            )

        credentials_json = config.get("credentials_json", "")
        spreadsheet_id = config.get("spreadsheet_id", "")
        range_name = config.get("range", "Sheet1")
        has_header = config.get("has_header", True)
        output_format = config.get("output_format", "objects")

        # Parse credentials
        if isinstance(credentials_json, str):
            creds_dict = json.loads(credentials_json)
        else:
            creds_dict = credentials_json

        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )

        # Build service
        service = build("sheets", "v4", credentials=credentials)
        sheet = service.spreadsheets()

        # Fetch data
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name,
        ).execute()

        values = result.get("values", [])

        if not values:
            return {
                "data": [],
                "row_count": 0,
                "columns": [],
            }

        if output_format == "raw":
            return {
                "data": values,
                "row_count": len(values),
                "columns": values[0] if values else [],
            }

        if output_format == "arrays":
            if has_header:
                return {
                    "data": values[1:],
                    "row_count": len(values) - 1,
                    "columns": values[0],
                }
            return {
                "data": values,
                "row_count": len(values),
                "columns": [],
            }

        # Default: objects format
        if has_header and len(values) > 1:
            headers = values[0]
            rows = []
            for row in values[1:]:
                obj = {}
                for i, header in enumerate(headers):
                    obj[header] = row[i] if i < len(row) else ""
                rows.append(obj)
            return {
                "data": rows,
                "row_count": len(rows),
                "columns": headers,
            }

        return {
            "data": values,
            "row_count": len(values),
            "columns": [],
        }


class GoogleSheetsWriteNode(BaseNode):
    """
    Write data to Google Sheets.

    Supports:
    - Appending rows
    - Updating specific ranges
    - Creating new sheets
    """

    type = "google-sheets-write"
    name = "Google Sheets: Write"
    category = "Apps"
    description = "Write data to Google Sheets"
    icon = "edit_note"
    color = "#0F9D58"

    inputs = [
        NodeField(
            name="credentials_json",
            label="Service Account JSON",
            type=FieldType.SECRET,
            required=True,
            description="Google Service Account credentials JSON.",
        ),
        NodeField(
            name="spreadsheet_id",
            label="Spreadsheet ID",
            type=FieldType.STRING,
            required=True,
            description="Google Sheets spreadsheet ID.",
        ),
        NodeField(
            name="range",
            label="Range",
            type=FieldType.STRING,
            required=False,
            default="Sheet1",
            description="Cell range to write to.",
        ),
        NodeField(
            name="data",
            label="Data",
            type=FieldType.JSON,
            required=True,
            description="Data to write (array of arrays or array of objects).",
        ),
        NodeField(
            name="operation",
            label="Operation",
            type=FieldType.SELECT,
            required=False,
            default="append",
            options=[
                {"value": "append", "label": "Append Rows"},
                {"value": "update", "label": "Update Range"},
                {"value": "clear_and_write", "label": "Clear and Write"},
            ],
            description="Write operation type.",
        ),
        NodeField(
            name="include_headers",
            label="Include Headers",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Include object keys as header row (for object data).",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
            description="Whether the write was successful.",
        ),
        NodeField(
            name="updated_cells",
            label="Updated Cells",
            type=FieldType.NUMBER,
            description="Number of cells updated.",
        ),
        NodeField(
            name="updated_range",
            label="Updated Range",
            type=FieldType.STRING,
            description="Range that was updated.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Write data to Google Sheets."""
        import json

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except ImportError:
            raise RuntimeError(
                "Google API libraries not installed. Install with: "
                "pip install google-auth google-auth-oauthlib google-api-python-client"
            )

        credentials_json = config.get("credentials_json", "")
        spreadsheet_id = config.get("spreadsheet_id", "")
        range_name = config.get("range", "Sheet1")
        data = config.get("data", [])
        operation = config.get("operation", "append")
        include_headers = config.get("include_headers", False)

        # Parse credentials
        if isinstance(credentials_json, str):
            creds_dict = json.loads(credentials_json)
        else:
            creds_dict = credentials_json

        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )

        # Build service
        service = build("sheets", "v4", credentials=credentials)
        sheet = service.spreadsheets()

        # Parse data
        if isinstance(data, str):
            data = json.loads(data)

        # Convert object array to value array if needed
        values = []
        if data and isinstance(data[0], dict):
            headers = list(data[0].keys())
            if include_headers:
                values.append(headers)
            for row in data:
                values.append([row.get(h, "") for h in headers])
        else:
            values = data

        body = {"values": values}

        if operation == "append":
            result = sheet.values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            ).execute()

            return {
                "success": True,
                "updated_cells": result.get("updates", {}).get("updatedCells", 0),
                "updated_range": result.get("updates", {}).get("updatedRange", ""),
            }

        elif operation == "update":
            result = sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()

            return {
                "success": True,
                "updated_cells": result.get("updatedCells", 0),
                "updated_range": result.get("updatedRange", ""),
            }

        elif operation == "clear_and_write":
            # Clear first
            sheet.values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name,
            ).execute()

            # Then write
            result = sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()

            return {
                "success": True,
                "updated_cells": result.get("updatedCells", 0),
                "updated_range": result.get("updatedRange", ""),
            }

        return {
            "success": False,
            "updated_cells": 0,
            "updated_range": "",
        }
