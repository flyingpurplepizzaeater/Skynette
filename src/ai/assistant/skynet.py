"""
Skynet Assistant - AI-powered workflow building assistant.

Provides natural language conversation, workflow generation,
and context-aware help for building automations.
"""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from src.ai.gateway import AIGateway, AIMessage, GenerationConfig, get_gateway
from src.core.nodes.registry import NodeRegistry
from src.core.workflow.models import Workflow, WorkflowNode


@dataclass
class ChatMessage:
    """A message in the assistant conversation."""

    id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


@dataclass
class WorkflowSuggestion:
    """A suggested workflow from the assistant."""

    name: str
    description: str
    nodes: list[dict]
    connections: list[dict]
    confidence: float = 0.0


class SkynetAssistant:
    """
    Skynet - The AI assistant for Skynette.

    Capabilities:
    - Natural language conversation
    - Workflow generation from descriptions
    - Node recommendations
    - Error explanation and debugging help
    - Expression assistance
    """

    SYSTEM_PROMPT = """You are Skynet, the AI assistant for Skynette - an AI-native workflow automation platform.

Your capabilities:
1. Help users build workflows through natural language
2. Explain what nodes do and recommend which ones to use
3. Debug workflow errors and explain issues in plain English
4. Suggest improvements to existing workflows
5. Generate complete workflows from descriptions

Available node categories and types:
{node_categories}

When generating workflows, output JSON in this format:
```json
{{
    "workflow": {{
        "name": "Workflow Name",
        "description": "What this workflow does",
        "nodes": [
            {{"type": "node_type", "name": "Display Name", "config": {{}}, "position": {{"x": 0, "y": 0}}}}
        ],
        "connections": [
            {{"from_node": 0, "to_node": 1}}
        ]
    }}
}}
```

Be helpful, concise, and practical. When users describe a task, suggest the simplest workflow that accomplishes it.
Don't over-engineer - prefer fewer nodes when possible."""

    def __init__(
        self,
        gateway: AIGateway | None = None,
        registry: NodeRegistry | None = None,
        on_message: Callable[[ChatMessage], None] | None = None,
    ):
        self.gateway = gateway or get_gateway()
        self.registry = registry or NodeRegistry()
        self.on_message = on_message

        self.conversation: list[ChatMessage] = []
        self.current_workflow: Workflow | None = None
        self.config = GenerationConfig(
            max_tokens=2048,
            temperature=0.7,
        )

    def _get_system_prompt(self) -> str:
        """Build system prompt with current node information."""
        categories = self.registry.categories
        node_info = []

        for category in categories:
            nodes = self.registry.get_by_category(category)
            node_names = [n.name for n in nodes[:10]]  # Limit for context
            if len(nodes) > 10:
                node_names.append(f"... and {len(nodes) - 10} more")
            node_info.append(f"- {category}: {', '.join(node_names)}")

        return self.SYSTEM_PROMPT.format(node_categories="\n".join(node_info))

    def _add_message(self, role: str, content: str, metadata: dict = None) -> ChatMessage:
        """Add a message to the conversation."""
        msg = ChatMessage(
            id=str(uuid4()),
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.conversation.append(msg)

        if self.on_message:
            self.on_message(msg)

        return msg

    def set_context(self, workflow: Workflow | None = None):
        """Set the current workflow context."""
        self.current_workflow = workflow

    def get_conversation_messages(self) -> list[AIMessage]:
        """Convert conversation to AI messages."""
        messages = [AIMessage(role="system", content=self._get_system_prompt())]

        # Add workflow context if available
        if self.current_workflow:
            context = f"\nCurrent workflow: {self.current_workflow.name}\n"
            context += f"Nodes: {len(self.current_workflow.nodes)}\n"
            if self.current_workflow.nodes:
                node_list = [f"- {n.name} ({n.type})" for n in self.current_workflow.nodes]
                context += "Current nodes:\n" + "\n".join(node_list)
            messages[0] = AIMessage(role="system", content=messages[0].content + context)

        # Add conversation history
        for msg in self.conversation[-20:]:  # Last 20 messages for context
            if msg.role in ("user", "assistant"):
                messages.append(AIMessage(role=msg.role, content=msg.content))

        return messages

    async def chat(self, user_message: str) -> ChatMessage:
        """
        Send a message and get a response.

        Args:
            user_message: The user's message

        Returns:
            The assistant's response message
        """
        # Add user message
        self._add_message("user", user_message)

        # Get AI response
        messages = self.get_conversation_messages()

        try:
            response = await self.gateway.chat(messages, self.config)
            assistant_msg = self._add_message(
                "assistant",
                response.content,
                {"provider": response.provider, "model": response.model},
            )
            return assistant_msg
        except Exception as e:
            error_msg = self._add_message(
                "assistant",
                f"I'm sorry, I encountered an error: {str(e)}\n\n"
                "This might be because no AI provider is configured. "
                "Go to Settings > AI Providers to set up a provider, or "
                "download a local model from the AI Hub.",
                {"error": str(e)},
            )
            return error_msg

    async def generate_workflow(self, description: str) -> WorkflowSuggestion | None:
        """
        Generate a workflow from a natural language description.

        Args:
            description: What the workflow should do

        Returns:
            WorkflowSuggestion if successful, None otherwise
        """
        prompt = f"""Generate a workflow that does the following:
{description}

Output ONLY valid JSON with the workflow structure. No explanation needed."""

        self._add_message("user", f"Create a workflow: {description}")

        messages = self.get_conversation_messages()
        messages.append(AIMessage(role="user", content=prompt))

        try:
            response = await self.gateway.chat(messages, self.config)

            # Extract JSON from response
            json_match = re.search(r"```json\s*(.*?)\s*```", response.content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_str = response.content

            data = json.loads(json_str)
            workflow_data = data.get("workflow", data)

            suggestion = WorkflowSuggestion(
                name=workflow_data.get("name", "Generated Workflow"),
                description=workflow_data.get("description", description),
                nodes=workflow_data.get("nodes", []),
                connections=workflow_data.get("connections", []),
                confidence=0.8,
            )

            self._add_message(
                "assistant",
                f"I've generated a workflow called '{suggestion.name}' with "
                f"{len(suggestion.nodes)} nodes. Would you like me to create it?",
                {"workflow_suggestion": suggestion},
            )

            return suggestion

        except json.JSONDecodeError:
            self._add_message(
                "assistant",
                "I understood your request but had trouble generating the workflow structure. "
                "Could you provide more details about what you want to automate?",
            )
            return None
        except Exception as e:
            self._add_message(
                "assistant",
                f"I encountered an error while generating the workflow: {str(e)}",
                {"error": str(e)},
            )
            return None

    def create_workflow_from_suggestion(self, suggestion: WorkflowSuggestion) -> Workflow:
        """
        Create an actual Workflow from a suggestion.

        Args:
            suggestion: The workflow suggestion to create

        Returns:
            A new Workflow object
        """
        workflow = Workflow(
            name=suggestion.name,
            description=suggestion.description,
        )

        # Create nodes
        node_id_map = {}
        for i, node_data in enumerate(suggestion.nodes):
            node = WorkflowNode(
                type=node_data.get("type", "manual_trigger"),
                name=node_data.get("name", f"Node {i + 1}"),
                config=node_data.get("config", {}),
                position=node_data.get("position", {"x": i * 200, "y": 100}),
            )
            workflow.nodes.append(node)
            node_id_map[i] = node.id

        # Create connections
        for conn in suggestion.connections:
            from_idx = conn.get("from_node", 0)
            to_idx = conn.get("to_node", 1)

            if from_idx in node_id_map and to_idx in node_id_map:
                from_node = workflow.nodes[from_idx]
                from_node.connections.append(node_id_map[to_idx])

        return workflow

    def suggest_next_node(self, current_node_type: str) -> list[dict]:
        """
        Suggest next nodes based on current node type.

        Args:
            current_node_type: The type of the current node

        Returns:
            List of suggested nodes with reasons
        """
        # Common patterns
        patterns = {
            "manual_trigger": ["http_request", "ai_text_generation", "read_file"],
            "schedule_trigger": ["http_request", "database_query", "send_email"],
            "http_request": ["if_else", "transform", "ai_extract"],
            "ai_text_generation": ["write_file", "send_email", "slack_message"],
            "ai_chat": ["if_else", "write_file", "transform"],
            "if_else": ["send_email", "slack_message", "log_debug"],
            "read_file": ["transform", "ai_text_generation", "ai_summarize"],
        }

        suggestions = []
        recommended = patterns.get(current_node_type, ["transform", "if_else", "log_debug"])

        for node_type in recommended:
            node_def = self.registry.get_definition(node_type)
            if node_def:
                suggestions.append(
                    {
                        "type": node_type,
                        "name": node_def.name,
                        "description": node_def.description,
                        "category": node_def.category,
                    }
                )

        return suggestions

    def explain_error(self, error_message: str, node_type: str = None) -> str:
        """
        Provide a plain-English explanation of an error.

        Args:
            error_message: The error message
            node_type: The node type where the error occurred (optional)

        Returns:
            Human-readable explanation
        """
        # Common error patterns and explanations
        explanations = {
            "connection refused": "The server you're trying to connect to isn't accepting connections. Check if the URL is correct and the server is running.",
            "timeout": "The request took too long to complete. The server might be slow or unreachable.",
            "401": "Authentication failed. Check your API key or credentials.",
            "403": "Access denied. You don't have permission to access this resource.",
            "404": "The resource wasn't found. Check if the URL or endpoint is correct.",
            "429": "Too many requests. You've hit a rate limit. Wait a bit before trying again.",
            "500": "The server encountered an error. This is usually not your fault - try again later.",
            "json": "There was a problem parsing the JSON data. Make sure the response is valid JSON.",
            "key error": "A required field is missing from the data. Check your input configuration.",
        }

        error_lower = error_message.lower()
        for pattern, explanation in explanations.items():
            if pattern in error_lower:
                return explanation

        return f"An error occurred: {error_message}. Check your node configuration and try again."

    def clear_conversation(self):
        """Clear the conversation history."""
        self.conversation = []

    def get_welcome_message(self) -> str:
        """Get the welcome message for new conversations."""
        return (
            "Hi! I'm Skynet, your AI assistant for building workflows. "
            "I can help you:\n\n"
            "- **Create workflows** from natural language descriptions\n"
            "- **Explain nodes** and recommend which ones to use\n"
            "- **Debug errors** and explain what went wrong\n"
            "- **Suggest improvements** to your workflows\n\n"
            "Try saying something like:\n"
            '- "Create a workflow that sends a Slack message every morning"\n'
            '- "What\'s the best way to call an API and save the response?"\n'
            '- "Why did my HTTP request fail?"'
        )


# Singleton instance
_assistant: SkynetAssistant | None = None


def get_assistant() -> SkynetAssistant:
    """Get the global Skynet assistant instance."""
    global _assistant
    if _assistant is None:
        _assistant = SkynetAssistant()
    return _assistant
