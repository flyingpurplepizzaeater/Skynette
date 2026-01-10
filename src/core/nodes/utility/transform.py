"""
Data Transform Utility Nodes - Transform and manipulate data.
"""

import json
from typing import Any

from src.core.nodes.base import BaseNode, NodeField, FieldType


class JSONParseNode(BaseNode):
    """
    Parse JSON string to object.
    """

    type = "json-parse"
    name = "JSON: Parse"
    category = "Utility"
    description = "Parse JSON string to object"
    icon = "data_object"
    color = "#6B7280"  # Gray

    inputs = [
        NodeField(
            name="json_string",
            label="JSON String",
            type=FieldType.TEXT,
            required=True,
        ),
    ]

    outputs = [
        NodeField(
            name="data",
            label="Parsed Data",
            type=FieldType.JSON,
        ),
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        json_string = config.get("json_string", "")
        try:
            data = json.loads(json_string)
            return {"data": data, "success": True}
        except:
            return {"data": {}, "success": False}


class JSONStringifyNode(BaseNode):
    """
    Convert object to JSON string.
    """

    type = "json-stringify"
    name = "JSON: Stringify"
    category = "Utility"
    description = "Convert object to JSON string"
    icon = "text_fields"
    color = "#6B7280"

    inputs = [
        NodeField(
            name="data",
            label="Data",
            type=FieldType.JSON,
            required=True,
        ),
        NodeField(
            name="indent",
            label="Indent",
            type=FieldType.NUMBER,
            required=False,
            default=2,
            description="Indentation spaces (0 for compact).",
        ),
    ]

    outputs = [
        NodeField(
            name="json_string",
            label="JSON String",
            type=FieldType.STRING,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        data = config.get("data", {})
        indent = int(config.get("indent", 2)) or None
        json_string = json.dumps(data, indent=indent)
        return {"json_string": json_string}


class TextSplitNode(BaseNode):
    """
    Split text into array.
    """

    type = "text-split"
    name = "Text: Split"
    category = "Utility"
    description = "Split text into array"
    icon = "call_split"
    color = "#6B7280"

    inputs = [
        NodeField(
            name="text",
            label="Text",
            type=FieldType.TEXT,
            required=True,
        ),
        NodeField(
            name="delimiter",
            label="Delimiter",
            type=FieldType.STRING,
            required=False,
            default=",",
            description="Split delimiter (use \\n for newline).",
        ),
        NodeField(
            name="trim",
            label="Trim Items",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
        ),
    ]

    outputs = [
        NodeField(
            name="items",
            label="Items",
            type=FieldType.JSON,
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        text = config.get("text", "")
        delimiter = config.get("delimiter", ",").replace("\\n", "\n")
        trim = config.get("trim", True)

        items = text.split(delimiter)
        if trim:
            items = [i.strip() for i in items]
        items = [i for i in items if i]  # Remove empty

        return {"items": items, "count": len(items)}


class TextJoinNode(BaseNode):
    """
    Join array items into text.
    """

    type = "text-join"
    name = "Text: Join"
    category = "Utility"
    description = "Join array items into text"
    icon = "merge"
    color = "#6B7280"

    inputs = [
        NodeField(
            name="items",
            label="Items",
            type=FieldType.JSON,
            required=True,
        ),
        NodeField(
            name="delimiter",
            label="Delimiter",
            type=FieldType.STRING,
            required=False,
            default=", ",
        ),
    ]

    outputs = [
        NodeField(
            name="text",
            label="Joined Text",
            type=FieldType.STRING,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        items = config.get("items", [])
        delimiter = config.get("delimiter", ", ").replace("\\n", "\n")

        if isinstance(items, str):
            items = json.loads(items)

        text = delimiter.join(str(i) for i in items)
        return {"text": text}


class TextReplaceNode(BaseNode):
    """
    Find and replace in text.
    """

    type = "text-replace"
    name = "Text: Replace"
    category = "Utility"
    description = "Find and replace in text"
    icon = "find_replace"
    color = "#6B7280"

    inputs = [
        NodeField(
            name="text",
            label="Text",
            type=FieldType.TEXT,
            required=True,
        ),
        NodeField(
            name="find",
            label="Find",
            type=FieldType.STRING,
            required=True,
        ),
        NodeField(
            name="replace",
            label="Replace With",
            type=FieldType.STRING,
            required=False,
            default="",
        ),
        NodeField(
            name="use_regex",
            label="Use Regex",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
        ),
    ]

    outputs = [
        NodeField(
            name="result",
            label="Result",
            type=FieldType.STRING,
        ),
        NodeField(
            name="replacements",
            label="Replacements Made",
            type=FieldType.NUMBER,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        text = config.get("text", "")
        find = config.get("find", "")
        replace = config.get("replace", "")
        use_regex = config.get("use_regex", False)

        if use_regex:
            import re
            result, count = re.subn(find, replace, text)
        else:
            count = text.count(find)
            result = text.replace(find, replace)

        return {"result": result, "replacements": count}


class ArrayFilterNode(BaseNode):
    """
    Filter array items by condition.
    """

    type = "array-filter"
    name = "Array: Filter"
    category = "Utility"
    description = "Filter array items"
    icon = "filter_list"
    color = "#6B7280"

    inputs = [
        NodeField(
            name="items",
            label="Items",
            type=FieldType.JSON,
            required=True,
        ),
        NodeField(
            name="property",
            label="Property",
            type=FieldType.STRING,
            required=False,
            description="Property to filter by (for object arrays).",
        ),
        NodeField(
            name="operator",
            label="Operator",
            type=FieldType.SELECT,
            required=False,
            default="equals",
            options=[
                {"value": "equals", "label": "Equals"},
                {"value": "not_equals", "label": "Not Equals"},
                {"value": "contains", "label": "Contains"},
                {"value": "starts_with", "label": "Starts With"},
                {"value": "ends_with", "label": "Ends With"},
                {"value": "greater_than", "label": "Greater Than"},
                {"value": "less_than", "label": "Less Than"},
                {"value": "exists", "label": "Exists"},
            ],
        ),
        NodeField(
            name="value",
            label="Value",
            type=FieldType.STRING,
            required=False,
            description="Value to compare against.",
        ),
    ]

    outputs = [
        NodeField(
            name="filtered",
            label="Filtered Items",
            type=FieldType.JSON,
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        items = config.get("items", [])
        prop = config.get("property", "")
        operator = config.get("operator", "equals")
        value = config.get("value", "")

        if isinstance(items, str):
            items = json.loads(items)

        def check(item):
            if prop:
                item_val = item.get(prop) if isinstance(item, dict) else item
            else:
                item_val = item

            if operator == "equals":
                return str(item_val) == value
            elif operator == "not_equals":
                return str(item_val) != value
            elif operator == "contains":
                return value in str(item_val)
            elif operator == "starts_with":
                return str(item_val).startswith(value)
            elif operator == "ends_with":
                return str(item_val).endswith(value)
            elif operator == "greater_than":
                try:
                    return float(item_val) > float(value)
                except:
                    return False
            elif operator == "less_than":
                try:
                    return float(item_val) < float(value)
                except:
                    return False
            elif operator == "exists":
                return item_val is not None
            return True

        filtered = [i for i in items if check(i)]

        return {"filtered": filtered, "count": len(filtered)}


class DateFormatNode(BaseNode):
    """
    Format dates and times.
    """

    type = "date-format"
    name = "Date: Format"
    category = "Utility"
    description = "Format dates and times"
    icon = "calendar_today"
    color = "#6B7280"

    inputs = [
        NodeField(
            name="date",
            label="Date",
            type=FieldType.STRING,
            required=False,
            description="Date string (leave empty for current time).",
        ),
        NodeField(
            name="format",
            label="Output Format",
            type=FieldType.STRING,
            required=False,
            default="%Y-%m-%d %H:%M:%S",
            description="Python strftime format.",
        ),
        NodeField(
            name="input_format",
            label="Input Format",
            type=FieldType.STRING,
            required=False,
            description="Input date format (if not ISO).",
        ),
    ]

    outputs = [
        NodeField(
            name="formatted",
            label="Formatted Date",
            type=FieldType.STRING,
        ),
        NodeField(
            name="timestamp",
            label="Unix Timestamp",
            type=FieldType.NUMBER,
        ),
        NodeField(
            name="iso",
            label="ISO Format",
            type=FieldType.STRING,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        from datetime import datetime

        date_str = config.get("date", "")
        output_format = config.get("format", "%Y-%m-%d %H:%M:%S")
        input_format = config.get("input_format", "")

        if not date_str:
            dt = datetime.now()
        else:
            if input_format:
                dt = datetime.strptime(date_str, input_format)
            else:
                # Try ISO format
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        return {
            "formatted": dt.strftime(output_format),
            "timestamp": int(dt.timestamp()),
            "iso": dt.isoformat(),
        }
