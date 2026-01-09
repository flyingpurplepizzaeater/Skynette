"""
Text Generation Node - Generate text using AI.
"""

from typing import Any

from src.core.nodes.base import BaseNode, NodeField, FieldType


class TextGenerationNode(BaseNode):
    """
    Generate text using AI models.

    Can use local models (free) or cloud providers.
    Supports prompt templates with variable substitution.
    """

    type = "ai-text-generation"
    name = "AI Text Generation"
    category = "AI"
    description = "Generate text using AI models"
    icon = "auto_awesome"
    color = "#8B5CF6"  # Violet

    inputs = [
        NodeField(
            name="prompt",
            label="Prompt",
            type=FieldType.TEXT,
            required=True,
            description="The prompt to send to the AI. Use {{variable}} for substitution.",
        ),
        NodeField(
            name="system_prompt",
            label="System Prompt",
            type=FieldType.TEXT,
            required=False,
            description="Optional system prompt to set AI behavior.",
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
            description="Which AI provider to use.",
        ),
        NodeField(
            name="model",
            label="Model",
            type=FieldType.STRING,
            required=False,
            description="Specific model to use. Leave empty for provider default.",
        ),
        NodeField(
            name="max_tokens",
            label="Max Tokens",
            type=FieldType.NUMBER,
            required=False,
            default=2048,
            description="Maximum tokens to generate.",
        ),
        NodeField(
            name="temperature",
            label="Temperature",
            type=FieldType.NUMBER,
            required=False,
            default=0.7,
            description="Creativity (0.0-2.0). Higher = more creative.",
        ),
    ]

    outputs = [
        NodeField(
            name="text",
            label="Generated Text",
            type=FieldType.STRING,
            description="The AI-generated text.",
        ),
        NodeField(
            name="usage",
            label="Token Usage",
            type=FieldType.JSON,
            description="Token usage information.",
        ),
        NodeField(
            name="provider_used",
            label="Provider Used",
            type=FieldType.STRING,
            description="Which provider was actually used.",
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute text generation."""
        from src.ai import get_gateway, AIMessage, GenerationConfig

        gateway = get_gateway()

        # Get parameters
        prompt = self._resolve_expression(config.get("prompt", ""), context)
        system_prompt = self._resolve_expression(config.get("system_prompt", ""), context)
        provider = config.get("provider", "auto")
        max_tokens = int(config.get("max_tokens", 2048))
        temperature = float(config.get("temperature", 0.7))

        # Build messages
        messages = []
        if system_prompt:
            messages.append(AIMessage(role="system", content=system_prompt))
        messages.append(AIMessage(role="user", content=prompt))

        # Configure generation
        gen_config = GenerationConfig(
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Use auto provider or specific one
        provider_arg = None if provider == "auto" else provider

        # Generate response
        response = await gateway.chat(
            messages=messages,
            config=gen_config,
            provider=provider_arg,
        )

        return {
            "text": response.content,
            "usage": response.usage,
            "provider_used": response.provider,
        }

    def _resolve_expression(self, value: str, context: dict) -> str:
        """Resolve {{variable}} expressions in text."""
        if not isinstance(value, str):
            return value

        import re

        def replace_var(match):
            var_path = match.group(1).strip()
            # Navigate the context to find the value
            parts = var_path.split(".")
            current = context
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return match.group(0)  # Keep original if not found
            return str(current)

        return re.sub(r"\{\{([^}]+)\}\}", replace_var, value)
