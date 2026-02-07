"""
Chat Node - Multi-turn conversation with AI.
"""

from src.core.nodes.base import BaseNode, FieldType, NodeField


class ChatNode(BaseNode):
    """
    Multi-turn chat conversation with AI.

    Maintains conversation history within the workflow execution.
    Can continue conversations across multiple chat nodes.
    """

    type = "ai-chat"
    name = "AI Chat"
    category = "AI"
    description = "Multi-turn conversation with AI"
    icon = "chat"
    color = "#8B5CF6"  # Violet

    inputs = [
        NodeField(
            name="message",
            label="Message",
            type=FieldType.TEXT,
            required=True,
            description="The message to send to the AI.",
        ),
        NodeField(
            name="conversation_id",
            label="Conversation ID",
            type=FieldType.STRING,
            required=False,
            default="default",
            description="ID to track conversation history. Use same ID to continue a conversation.",
        ),
        NodeField(
            name="system_prompt",
            label="System Prompt",
            type=FieldType.TEXT,
            required=False,
            description="System prompt (only used at start of conversation).",
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
        NodeField(
            name="max_tokens",
            label="Max Tokens",
            type=FieldType.NUMBER,
            required=False,
            default=2048,
        ),
        NodeField(
            name="temperature",
            label="Temperature",
            type=FieldType.NUMBER,
            required=False,
            default=0.7,
        ),
        NodeField(
            name="clear_history",
            label="Clear History",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Clear conversation history before this message.",
        ),
    ]

    outputs = [
        NodeField(
            name="response",
            label="AI Response",
            type=FieldType.STRING,
            description="The AI's response.",
        ),
        NodeField(
            name="history",
            label="Conversation History",
            type=FieldType.JSON,
            description="Full conversation history.",
        ),
        NodeField(
            name="message_count",
            label="Message Count",
            type=FieldType.NUMBER,
            description="Number of messages in conversation.",
        ),
    ]

    # Class-level conversation storage
    _conversations: dict[str, list] = {}

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute chat message."""
        from src.ai import AIMessage, GenerationConfig, get_gateway

        gateway = get_gateway()

        # Get parameters
        message = config.get("message", "")
        conversation_id = config.get("conversation_id", "default")
        system_prompt = config.get("system_prompt", "")
        provider = config.get("provider", "auto")
        max_tokens = int(config.get("max_tokens", 2048))
        temperature = float(config.get("temperature", 0.7))
        clear_history = config.get("clear_history", False)

        # Get or create conversation
        if clear_history or conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
            # Add system prompt if this is a new conversation
            if system_prompt:
                self._conversations[conversation_id].append(
                    {
                        "role": "system",
                        "content": system_prompt,
                    }
                )

        # Add user message
        self._conversations[conversation_id].append(
            {
                "role": "user",
                "content": message,
            }
        )

        # Build AIMessage list
        messages = [
            AIMessage(role=m["role"], content=m["content"])
            for m in self._conversations[conversation_id]
        ]

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

        # Add assistant response to history
        self._conversations[conversation_id].append(
            {
                "role": "assistant",
                "content": response.content,
            }
        )

        return {
            "response": response.content,
            "history": self._conversations[conversation_id],
            "message_count": len(self._conversations[conversation_id]),
        }

    @classmethod
    def clear_conversation(cls, conversation_id: str):
        """Clear a conversation's history."""
        if conversation_id in cls._conversations:
            del cls._conversations[conversation_id]

    @classmethod
    def clear_all_conversations(cls):
        """Clear all conversation histories."""
        cls._conversations.clear()
