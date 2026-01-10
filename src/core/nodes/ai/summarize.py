"""
Summarize Node - Summarize text using AI.
"""

from typing import Any

from src.core.nodes.base import BaseNode, NodeField, FieldType


class SummarizeNode(BaseNode):
    """
    Summarize text content using AI.

    Supports different summary styles and lengths.
    Can handle long documents with chunking.
    """

    type = "ai-summarize"
    name = "AI Summarize"
    category = "AI"
    description = "Summarize text using AI"
    icon = "summarize"
    color = "#8B5CF6"  # Violet

    inputs = [
        NodeField(
            name="text",
            label="Text to Summarize",
            type=FieldType.TEXT,
            required=True,
            description="The text content to summarize.",
        ),
        NodeField(
            name="style",
            label="Summary Style",
            type=FieldType.SELECT,
            required=False,
            default="concise",
            options=[
                {"value": "concise", "label": "Concise (1-2 sentences)"},
                {"value": "detailed", "label": "Detailed (paragraph)"},
                {"value": "bullets", "label": "Bullet Points"},
                {"value": "executive", "label": "Executive Summary"},
            ],
            description="Style of the summary.",
        ),
        NodeField(
            name="max_length",
            label="Max Length (words)",
            type=FieldType.NUMBER,
            required=False,
            default=100,
            description="Target maximum word count.",
        ),
        NodeField(
            name="focus",
            label="Focus Areas",
            type=FieldType.STRING,
            required=False,
            description="Specific areas to focus on (comma-separated).",
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
            name="summary",
            label="Summary",
            type=FieldType.STRING,
            description="The generated summary.",
        ),
        NodeField(
            name="original_length",
            label="Original Word Count",
            type=FieldType.NUMBER,
            description="Word count of original text.",
        ),
        NodeField(
            name="summary_length",
            label="Summary Word Count",
            type=FieldType.NUMBER,
            description="Word count of summary.",
        ),
    ]

    STYLE_PROMPTS = {
        "concise": "Provide a concise 1-2 sentence summary.",
        "detailed": "Provide a detailed paragraph summary that captures all key points.",
        "bullets": "Provide a summary as a bulleted list of key points.",
        "executive": "Provide an executive summary with key findings, implications, and recommendations.",
    }

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute summarization."""
        from src.ai import get_gateway, AIMessage, GenerationConfig

        gateway = get_gateway()

        # Get parameters
        text = config.get("text", "")
        style = config.get("style", "concise")
        max_length = int(config.get("max_length", 100))
        focus = config.get("focus", "")
        provider = config.get("provider", "auto")

        # Count original words
        original_words = len(text.split())

        # Build prompt
        style_instruction = self.STYLE_PROMPTS.get(style, self.STYLE_PROMPTS["concise"])
        focus_instruction = f"\n\nFocus especially on: {focus}" if focus else ""

        system_prompt = f"""You are a skilled summarizer. {style_instruction}
Keep the summary under {max_length} words.{focus_instruction}
Only output the summary, no preamble or explanation."""

        user_prompt = f"Please summarize the following text:\n\n{text}"

        messages = [
            AIMessage(role="system", content=system_prompt),
            AIMessage(role="user", content=user_prompt),
        ]

        # Configure generation
        gen_config = GenerationConfig(
            max_tokens=max_length * 2,  # Allow some buffer
            temperature=0.3,  # Lower temperature for factual summaries
        )

        # Use auto provider or specific one
        provider_arg = None if provider == "auto" else provider

        # Generate summary
        response = await gateway.chat(
            messages=messages,
            config=gen_config,
            provider=provider_arg,
        )

        summary = response.content.strip()
        summary_words = len(summary.split())

        return {
            "summary": summary,
            "original_length": original_words,
            "summary_length": summary_words,
        }
