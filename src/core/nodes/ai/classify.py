"""
Classify Node - Classify text into categories using AI.
"""

from typing import Any

from src.core.nodes.base import BaseNode, NodeField, FieldType


class ClassifyNode(BaseNode):
    """
    Classify text into predefined categories using AI.

    Supports multiple classification types:
    - Single label (one category)
    - Multi-label (multiple categories)
    - Confidence scores
    """

    type = "ai-classify"
    name = "AI Classify"
    category = "AI"
    description = "Classify text into categories"
    icon = "label"
    color = "#8B5CF6"  # Violet

    inputs = [
        NodeField(
            name="text",
            label="Text to Classify",
            type=FieldType.TEXT,
            required=True,
            description="The text to classify.",
        ),
        NodeField(
            name="categories",
            label="Categories",
            type=FieldType.TEXT,
            required=True,
            description="Comma-separated list of categories (e.g., 'positive, negative, neutral').",
        ),
        NodeField(
            name="multi_label",
            label="Allow Multiple Labels",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Allow classifying into multiple categories.",
        ),
        NodeField(
            name="include_confidence",
            label="Include Confidence",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
            description="Include confidence scores for each category.",
        ),
        NodeField(
            name="context",
            label="Classification Context",
            type=FieldType.TEXT,
            required=False,
            description="Additional context about the classification task.",
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
            name="label",
            label="Primary Label",
            type=FieldType.STRING,
            description="The primary classification label.",
        ),
        NodeField(
            name="labels",
            label="All Labels",
            type=FieldType.JSON,
            description="All applicable labels (for multi-label).",
        ),
        NodeField(
            name="confidence",
            label="Confidence Scores",
            type=FieldType.JSON,
            description="Confidence scores for each category.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute classification."""
        import json
        from src.ai import get_gateway, AIMessage, GenerationConfig

        gateway = get_gateway()

        # Get parameters
        text = config.get("text", "")
        categories_str = config.get("categories", "")
        multi_label = config.get("multi_label", False)
        include_confidence = config.get("include_confidence", True)
        classification_context = config.get("context", "")
        provider = config.get("provider", "auto")

        # Parse categories
        categories = [c.strip() for c in categories_str.split(",") if c.strip()]

        if not categories:
            return {
                "label": "",
                "labels": [],
                "confidence": {},
            }

        # Build prompt
        categories_list = ", ".join(categories)
        multi_instruction = "You may select multiple categories if applicable." if multi_label else "Select exactly one category."
        confidence_instruction = "Include a confidence score (0.0-1.0) for each category." if include_confidence else ""
        context_instruction = f"\n\nContext: {classification_context}" if classification_context else ""

        system_prompt = f"""You are a text classification assistant. Classify the given text into one or more of these categories: {categories_list}

{multi_instruction}
{confidence_instruction}

Return your answer as a JSON object with:
- "labels": array of selected category names
- "confidence": object mapping each category to its confidence score{context_instruction}

Only output valid JSON, no explanation."""

        user_prompt = f"Classify this text:\n\n{text}"

        messages = [
            AIMessage(role="system", content=system_prompt),
            AIMessage(role="user", content=user_prompt),
        ]

        # Configure generation
        gen_config = GenerationConfig(
            max_tokens=512,
            temperature=0.1,  # Low temperature for consistent classification
        )

        # Use auto provider or specific one
        provider_arg = None if provider == "auto" else provider

        # Generate classification
        response = await gateway.chat(
            messages=messages,
            config=gen_config,
            provider=provider_arg,
        )

        # Parse JSON response
        content = response.content.strip()

        try:
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            labels = result.get("labels", [])
            confidence = result.get("confidence", {})

            # If not multi-label, take only the first/highest confidence label
            if not multi_label and labels:
                if confidence:
                    # Sort by confidence and take highest
                    labels = [max(labels, key=lambda l: confidence.get(l, 0))]
                else:
                    labels = [labels[0]]

        except json.JSONDecodeError:
            # Fallback: try to find category in response
            labels = []
            for cat in categories:
                if cat.lower() in content.lower():
                    labels.append(cat)
                    if not multi_label:
                        break
            confidence = {cat: 0.5 for cat in labels}

        return {
            "label": labels[0] if labels else "",
            "labels": labels,
            "confidence": confidence,
        }
