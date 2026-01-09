"""
Extract Node - Extract structured data from text using AI.
"""

import json
from typing import Any

from src.core.nodes.base import BaseNode, NodeField, FieldType


class ExtractNode(BaseNode):
    """
    Extract structured data from text using AI.

    Can extract specific fields, entities, or patterns.
    Returns data in JSON format for easy processing.
    """

    type = "ai-extract"
    name = "AI Extract"
    category = "AI"
    description = "Extract structured data from text"
    icon = "data_object"
    color = "#8B5CF6"  # Violet

    inputs = [
        NodeField(
            name="text",
            label="Input Text",
            type=FieldType.TEXT,
            required=True,
            description="The text to extract data from.",
        ),
        NodeField(
            name="fields",
            label="Fields to Extract",
            type=FieldType.TEXT,
            required=True,
            description="Comma-separated list of fields to extract (e.g., 'name, email, phone').",
        ),
        NodeField(
            name="instructions",
            label="Additional Instructions",
            type=FieldType.TEXT,
            required=False,
            description="Additional extraction instructions.",
        ),
        NodeField(
            name="provider",
            label="AI Provider",
            type=FieldType.SELECT,
            required=False,
            default="auto",
            options=[
                {"value": "auto", "label": "Auto (Best Available)"},
                {"value": "local", "label": "Local (Free)"},
                {"value": "openai", "label": "OpenAI"},
                {"value": "anthropic", "label": "Anthropic"},
            ],
        ),
    ]

    outputs = [
        NodeField(
            name="data",
            label="Extracted Data",
            type=FieldType.JSON,
            description="Extracted data as JSON object.",
        ),
        NodeField(
            name="fields_found",
            label="Fields Found",
            type=FieldType.NUMBER,
            description="Number of fields successfully extracted.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute data extraction."""
        from src.ai import get_gateway, AIMessage, GenerationConfig

        gateway = get_gateway()

        # Get parameters
        text = config.get("text", "")
        fields_str = config.get("fields", "")
        instructions = config.get("instructions", "")
        provider = config.get("provider", "auto")

        # Parse fields
        fields = [f.strip() for f in fields_str.split(",") if f.strip()]

        if not fields:
            return {
                "data": {},
                "fields_found": 0,
            }

        # Build prompt
        fields_list = "\n".join([f"- {field}" for field in fields])
        additional = f"\n\nAdditional instructions: {instructions}" if instructions else ""

        system_prompt = f"""You are a data extraction assistant. Extract the requested fields from the given text.
Return ONLY a valid JSON object with the extracted fields. Use null for fields that cannot be found.
Do not include any explanation, just the JSON object.{additional}"""

        user_prompt = f"""Extract these fields from the text:
{fields_list}

Text:
{text}

Return as JSON:"""

        messages = [
            AIMessage(role="system", content=system_prompt),
            AIMessage(role="user", content=user_prompt),
        ]

        # Configure generation
        gen_config = GenerationConfig(
            max_tokens=1024,
            temperature=0.1,  # Low temperature for precise extraction
        )

        # Use auto provider or specific one
        provider_arg = None if provider == "auto" else provider

        # Generate extraction
        response = await gateway.chat(
            messages=messages,
            config=gen_config,
            provider=provider_arg,
        )

        # Parse JSON response
        content = response.content.strip()

        # Try to extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON object in response
            import re
            json_match = re.search(r"\{[^{}]*\}", content, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    data = {"error": "Failed to parse extraction", "raw": content}
            else:
                data = {"error": "Failed to parse extraction", "raw": content}

        # Count found fields
        fields_found = sum(1 for f in fields if f in data and data[f] is not None)

        return {
            "data": data,
            "fields_found": fields_found,
        }
