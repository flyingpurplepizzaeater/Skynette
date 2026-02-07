"""AI workflow nodes."""

from src.core.nodes.ai.chat import ChatNode
from src.core.nodes.ai.classify import ClassifyNode
from src.core.nodes.ai.extract import ExtractNode
from src.core.nodes.ai.summarize import SummarizeNode
from src.core.nodes.ai.text_generation import TextGenerationNode

__all__ = [
    "TextGenerationNode",
    "ChatNode",
    "SummarizeNode",
    "ExtractNode",
    "ClassifyNode",
]

# Register AI nodes
AI_NODES = [
    TextGenerationNode,
    ChatNode,
    SummarizeNode,
    ExtractNode,
    ClassifyNode,
]
