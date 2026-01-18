"""Execution nodes for running code in workflows."""

from src.core.nodes.execution.code_runner import CodeExecutionNode

__all__ = ["CodeExecutionNode"]

# Register execution nodes
EXECUTION_NODES = [CodeExecutionNode]
