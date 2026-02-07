"""
If/Else Node

Conditional branching based on expressions.
"""

from typing import Any

from src.core.nodes.base import FieldType, FlowNode, NodeField, NodeOutput


class IfElseNode(FlowNode):
    """If/Else node - conditional branching."""

    type = "if_else"
    name = "If/Else"
    description = "Branch the workflow based on a condition"
    icon = "call_split"

    @classmethod
    def get_inputs(cls) -> list[NodeField]:
        return [
            NodeField(
                name="condition_type",
                label="Condition Type",
                type=FieldType.SELECT,
                description="How to evaluate the condition",
                required=True,
                default="expression",
                options=[
                    {"label": "Expression", "value": "expression"},
                    {"label": "Comparison", "value": "comparison"},
                    {"label": "Boolean Value", "value": "boolean"},
                ],
            ),
            NodeField(
                name="expression",
                label="Expression",
                type=FieldType.EXPRESSION,
                description="Expression that evaluates to true/false",
                required=False,
                placeholder="{{$prev.status}} == 200",
            ),
            NodeField(
                name="left_value",
                label="Left Value",
                type=FieldType.EXPRESSION,
                description="Left side of comparison",
                required=False,
            ),
            NodeField(
                name="operator",
                label="Operator",
                type=FieldType.SELECT,
                description="Comparison operator",
                required=False,
                default="equals",
                options=[
                    {"label": "Equals", "value": "equals"},
                    {"label": "Not Equals", "value": "not_equals"},
                    {"label": "Greater Than", "value": "greater"},
                    {"label": "Greater or Equal", "value": "greater_equal"},
                    {"label": "Less Than", "value": "less"},
                    {"label": "Less or Equal", "value": "less_equal"},
                    {"label": "Contains", "value": "contains"},
                    {"label": "Not Contains", "value": "not_contains"},
                    {"label": "Is Empty", "value": "is_empty"},
                    {"label": "Is Not Empty", "value": "not_empty"},
                ],
            ),
            NodeField(
                name="right_value",
                label="Right Value",
                type=FieldType.EXPRESSION,
                description="Right side of comparison",
                required=False,
            ),
            NodeField(
                name="boolean_value",
                label="Boolean Value",
                type=FieldType.EXPRESSION,
                description="Value that should be truthy/falsy",
                required=False,
            ),
        ]

    @classmethod
    def get_outputs(cls) -> list[NodeOutput]:
        return [
            NodeOutput(
                name="result",
                type="boolean",
                description="The result of the condition",
            ),
            NodeOutput(
                name="branch",
                type="string",
                description="Which branch was taken: 'true' or 'false'",
            ),
            NodeOutput(
                name="data",
                type="object",
                description="Pass-through of input data",
            ),
        ]

    async def execute(self, config: dict, context: dict) -> Any:
        """Evaluate the condition."""
        condition_type = config.get("condition_type", "expression")
        result = False

        if condition_type == "boolean":
            value = config.get("boolean_value")
            result = bool(value)

        elif condition_type == "comparison":
            left = config.get("left_value")
            right = config.get("right_value")
            operator = config.get("operator", "equals")

            result = self._compare(left, right, operator)

        else:  # expression
            expr = config.get("expression", "")
            # Simple expression evaluation
            # In a real implementation, this would be more sophisticated
            result = self._evaluate_expression(expr, context)

        return {
            "result": result,
            "branch": "true" if result else "false",
            "data": context.get("$prev", {}),
        }

    def _compare(self, left: Any, right: Any, operator: str) -> bool:
        """Compare two values."""
        if operator == "equals":
            return left == right
        elif operator == "not_equals":
            return left != right
        elif operator == "greater":
            return left > right
        elif operator == "greater_equal":
            return left >= right
        elif operator == "less":
            return left < right
        elif operator == "less_equal":
            return left <= right
        elif operator == "contains":
            return right in str(left)
        elif operator == "not_contains":
            return right not in str(left)
        elif operator == "is_empty":
            return not left
        elif operator == "not_empty":
            return bool(left)
        return False

    def _evaluate_expression(self, expr: str, context: dict) -> bool:
        """Evaluate a simple boolean expression."""
        # This is a simplified implementation
        # A real implementation would use a proper expression parser

        if not expr:
            return False

        # Check for common patterns
        if "==" in expr:
            parts = expr.split("==")
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                # Resolve expressions
                left_val = self._resolve(left, context)
                right_val = self._resolve(right, context)
                return left_val == right_val

        if "!=" in expr:
            parts = expr.split("!=")
            if len(parts) == 2:
                left_val = self._resolve(parts[0].strip(), context)
                right_val = self._resolve(parts[1].strip(), context)
                return left_val != right_val

        # Default: treat as boolean
        return bool(self._resolve(expr, context))

    def _resolve(self, value: str, context: dict) -> Any:
        """Resolve a value (expression or literal)."""
        value = value.strip()

        # Remove quotes for string literals
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]

        # Check for number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Check for boolean
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False

        # Otherwise, return as-is (could be a reference to context)
        return value
