"""
Demo Provider - A mock provider for testing without API keys.

Provides helpful responses for common workflow questions using
pattern matching and templates.
"""

import asyncio
import random
from collections.abc import AsyncIterator

from src.ai.gateway import (
    AICapability,
    AIMessage,
    AIResponse,
    AIStreamChunk,
    GenerationConfig,
)
from src.ai.providers.base import BaseProvider


class DemoProvider(BaseProvider):
    """
    Demo AI provider for testing without external APIs.

    Provides helpful template responses for common questions
    about workflow building.
    """

    name = "demo"
    display_name = "Demo (No API Required)"
    capabilities = {
        AICapability.TEXT_GENERATION,
        AICapability.CHAT,
        AICapability.CODE_GENERATION,
    }

    # Response templates for common questions
    RESPONSES = {
        "workflow": """I can help you create that workflow! Here's what I'd suggest:

1. **Start with a trigger** - Choose what kicks off the workflow (manual, schedule, webhook, etc.)
2. **Add your main action** - What should happen? (HTTP request, file operation, AI task, etc.)
3. **Handle the result** - Store it, send a notification, or pass it to another step

Would you like me to generate the specific nodes for this? Just describe what you want in more detail.""",
        "api": """To call an API in Skynette:

1. Add an **HTTP Request** node
2. Configure the **Method** (GET, POST, PUT, DELETE)
3. Enter the **URL** of the API endpoint
4. Add **Headers** if needed (like `Authorization: Bearer your-token`)
5. For POST/PUT, add the **Body** content

The response will be available for the next node as `{{$prev.data}}`.""",
        "email": """For email workflows, you have a few options:

1. **SMTP Email** node - Send emails directly via your email server
2. **Email Trigger** node - Trigger workflows when emails arrive
3. **Gmail/Outlook** plugins - Full integration with those services

Do you want to send emails, or trigger workflows based on incoming emails?""",
        "schedule": """To run a workflow on a schedule:

1. Use the **Schedule Trigger** node as your first node
2. Set the **Cron Expression** or use the visual schedule builder
3. Common schedules:
   - `0 9 * * *` - Every day at 9 AM
   - `0 */2 * * *` - Every 2 hours
   - `0 0 * * 1` - Every Monday at midnight

Your workflow will run automatically at the specified times.""",
        "ai": """Skynette has several AI nodes:

1. **Text Generation** - Generate text from a prompt
2. **AI Chat** - Conversational AI with memory
3. **Summarize** - Condense long text
4. **Extract** - Pull structured data from text
5. **Classify** - Categorize inputs

You can use local models (free) or cloud APIs (OpenAI, Claude, etc.).""",
        "file": """For file operations:

1. **Read File** - Load a file's contents
2. **Write File** - Save data to a file
3. **File Watcher** trigger - React to new/changed files

Files are stored locally. Use `{{$prev.data}}` to pass file contents between nodes.""",
        "help": """I'm Skynet, your AI assistant! I can help you:

- **Build workflows** from natural language descriptions
- **Explain nodes** and what they do
- **Suggest improvements** to your workflows
- **Debug errors** when things go wrong

Just describe what you want to automate, and I'll suggest the best approach!""",
        "default": """I'd be happy to help with that! Here are some things I can assist with:

- Creating new workflows
- Explaining how nodes work
- Connecting to APIs and services
- Setting up schedules and triggers
- Using AI in your workflows

Could you tell me more about what you're trying to accomplish?""",
    }

    def __init__(self):
        super().__init__()
        self._is_initialized = True
        self._is_available = True

    async def initialize(self) -> bool:
        """Initialize the demo provider."""
        self._is_initialized = True
        self._is_available = True
        return True

    def is_available(self) -> bool:
        """Demo provider is always available."""
        return True

    def _get_response(self, messages: list[AIMessage]) -> str:
        """Get a response based on the conversation."""
        # Get the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.role == "user":
                user_message = msg.content.lower()
                break

        # Match keywords to responses
        if any(w in user_message for w in ["create", "build", "make", "workflow", "automate"]):
            return self.RESPONSES["workflow"]
        elif any(w in user_message for w in ["api", "http", "request", "endpoint", "rest"]):
            return self.RESPONSES["api"]
        elif any(w in user_message for w in ["email", "mail", "smtp", "gmail"]):
            return self.RESPONSES["email"]
        elif any(
            w in user_message for w in ["schedule", "cron", "time", "every", "daily", "hourly"]
        ):
            return self.RESPONSES["schedule"]
        elif any(w in user_message for w in ["ai", "gpt", "llm", "model", "generate", "summarize"]):
            return self.RESPONSES["ai"]
        elif any(w in user_message for w in ["file", "read", "write", "folder", "watch"]):
            return self.RESPONSES["file"]
        elif any(w in user_message for w in ["help", "what can", "how do"]):
            return self.RESPONSES["help"]
        else:
            return self.RESPONSES["default"]

    async def generate(
        self,
        prompt: str,
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate text from a prompt."""
        # Simulate thinking time
        await asyncio.sleep(random.uniform(0.3, 0.8))

        return AIResponse(
            content=self._get_response([AIMessage(role="user", content=prompt)]),
            provider=self.name,
            model="demo-v1",
            usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": 50,
                "total_tokens": 50 + len(prompt.split()),
            },
            finish_reason="stop",
        )

    async def chat(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate a chat response."""
        # Simulate thinking time
        await asyncio.sleep(random.uniform(0.5, 1.2))

        return AIResponse(
            content=self._get_response(messages),
            provider=self.name,
            model="demo-v1",
            usage={
                "prompt_tokens": sum(len(m.content.split()) for m in messages),
                "completion_tokens": 80,
                "total_tokens": 100,
            },
            finish_reason="stop",
        )

    async def chat_stream(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AsyncIterator[AIStreamChunk]:
        """Stream a chat response."""
        response = self._get_response(messages)
        words = response.split()

        # Stream word by word
        for i, word in enumerate(words):
            await asyncio.sleep(0.02)  # 50 words per second
            yield AIStreamChunk(
                content=word + " ",
                is_final=(i == len(words) - 1),
            )

    def get_models(self) -> list[dict]:
        """Get available demo models."""
        return [
            {
                "id": "demo-v1",
                "name": "Demo Model",
                "description": "A helpful demo model for testing",
                "context_length": 4096,
            }
        ]
