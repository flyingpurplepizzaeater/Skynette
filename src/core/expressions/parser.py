"""
Expression Parser and Evaluator

Handles parsing and evaluation of {{expressions}} in workflow configurations.

Supported expression formats:
- $prev - Previous node output
- $prev.data.field - Nested field access
- $trigger - Trigger data
- $vars.myVar - Workflow variables
- $env.MY_VAR - Environment variables
- $node.NodeName - Output from specific node
- $now() - Current timestamp
- $uuid() - Generate UUID
- $json($prev) - Convert to JSON string
- $length($prev.items) - Array/string length

Array operations:
- $prev.items.0 - Index access
- $prev.items.first - First element
- $prev.items.last - Last element
- $prev.items.length - Array length
"""

import os
import re
import json
from datetime import datetime, UTC
from typing import Any, Callable
from uuid import uuid4
import hashlib


class ExpressionError(Exception):
    """Error during expression evaluation."""
    pass


class ExpressionParser:
    """
    Parses and evaluates expressions in workflow configurations.

    Expressions are wrapped in double curly braces: {{expression}}
    """

    # Pattern to match expressions
    EXPRESSION_PATTERN = re.compile(r"\{\{([^}]+)\}\}")

    # Built-in functions
    BUILTIN_FUNCTIONS: dict[str, Callable] = {}

    def __init__(self):
        self._register_builtins()

    def _register_builtins(self):
        """Register built-in functions."""
        self.BUILTIN_FUNCTIONS = {
            "now": lambda: datetime.now(UTC).isoformat() + "Z",
            "uuid": lambda: str(uuid4()),
            "date": lambda: datetime.now(UTC).strftime("%Y-%m-%d"),
            "time": lambda: datetime.now(UTC).strftime("%H:%M:%S"),
            "timestamp": lambda: int(datetime.now(UTC).timestamp()),
            "json": lambda x: json.dumps(x, default=str),
            "parse_json": lambda x: json.loads(x) if isinstance(x, str) else x,
            "length": lambda x: len(x) if hasattr(x, "__len__") else 0,
            "string": lambda x: str(x),
            "number": lambda x: float(x) if x else 0,
            "int": lambda x: int(float(x)) if x else 0,
            "bool": lambda x: bool(x),
            "lower": lambda x: str(x).lower() if x else "",
            "upper": lambda x: str(x).upper() if x else "",
            "trim": lambda x: str(x).strip() if x else "",
            "split": lambda x, sep=",": str(x).split(sep) if x else [],
            "join": lambda x, sep=",": sep.join(str(i) for i in x) if x else "",
            "first": lambda x: x[0] if x and len(x) > 0 else None,
            "last": lambda x: x[-1] if x and len(x) > 0 else None,
            "reverse": lambda x: list(reversed(x)) if isinstance(x, list) else str(x)[::-1],
            "sort": lambda x: sorted(x) if isinstance(x, list) else x,
            "unique": lambda x: list(set(x)) if isinstance(x, list) else x,
            "keys": lambda x: list(x.keys()) if isinstance(x, dict) else [],
            "values": lambda x: list(x.values()) if isinstance(x, dict) else [],
            "default": lambda x, default="": x if x is not None else default,
            "hash": lambda x: hashlib.sha256(str(x).encode()).hexdigest(),
            "md5": lambda x: hashlib.md5(str(x).encode()).hexdigest(),
            "base64_encode": lambda x: __import__("base64").b64encode(str(x).encode()).decode(),
            "base64_decode": lambda x: __import__("base64").b64decode(str(x)).decode(),
            "abs": lambda x: abs(float(x)) if x else 0,
            "round": lambda x, digits=0: round(float(x), int(digits)) if x else 0,
            "floor": lambda x: int(float(x)) if x else 0,
            "ceil": lambda x: int(float(x)) + (1 if float(x) % 1 else 0) if x else 0,
            "min": lambda *args: min(args) if args else None,
            "max": lambda *args: max(args) if args else None,
            "sum": lambda x: sum(x) if isinstance(x, list) else float(x) if x else 0,
            "avg": lambda x: sum(x) / len(x) if isinstance(x, list) and len(x) > 0 else 0,
            "range": lambda start, end, step=1: list(range(int(start), int(end), int(step))),
            "slice": lambda x, start=0, end=None: x[int(start):int(end) if end else None] if x else [],
            "contains": lambda x, item: item in x if x else False,
            "starts_with": lambda x, prefix: str(x).startswith(prefix) if x else False,
            "ends_with": lambda x, suffix: str(x).endswith(suffix) if x else False,
            "replace": lambda x, old, new: str(x).replace(old, new) if x else "",
            "format": lambda template, **kwargs: template.format(**kwargs) if template else "",
            "typeof": lambda x: type(x).__name__,
            "empty": lambda x: x is None or x == "" or x == [] or x == {},
            "not_empty": lambda x: not (x is None or x == "" or x == [] or x == {}),
            "ternary": lambda cond, if_true, if_false: if_true if cond else if_false,
        }

    def resolve(self, value: Any, context: dict) -> Any:
        """
        Resolve all expressions in a value.

        Args:
            value: The value to resolve (can be string, dict, list, or other)
            context: The execution context containing $prev, $trigger, etc.

        Returns:
            The resolved value with all expressions evaluated
        """
        if isinstance(value, str):
            return self._resolve_string(value, context)
        elif isinstance(value, dict):
            return {k: self.resolve(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve(item, context) for item in value]
        return value

    def _resolve_string(self, value: str, context: dict) -> Any:
        """Resolve expressions in a string value."""
        matches = self.EXPRESSION_PATTERN.findall(value)

        if not matches:
            return value

        # If the entire string is a single expression, return the raw value
        if value.strip() == f"{{{{{matches[0]}}}}}":
            return self.evaluate(matches[0].strip(), context)

        # Otherwise, convert all expressions to strings and substitute
        result = value
        for match in matches:
            expr_value = self.evaluate(match.strip(), context)
            result = result.replace(f"{{{{{match}}}}}", str(expr_value) if expr_value is not None else "")

        return result

    def evaluate(self, expression: str, context: dict) -> Any:
        """
        Evaluate a single expression.

        Args:
            expression: The expression without the {{}} wrapper
            context: The execution context

        Returns:
            The evaluated value
        """
        expression = expression.strip()

        # Check for function call
        if "(" in expression:
            return self._evaluate_function(expression, context)

        # Check for comparison operators
        if any(op in expression for op in [" == ", " != ", " > ", " < ", " >= ", " <= "]):
            return self._evaluate_comparison(expression, context)

        # Check for logical operators
        if " && " in expression or " || " in expression or expression.startswith("!"):
            return self._evaluate_logical(expression, context)

        # Check for arithmetic
        if any(op in expression for op in [" + ", " - ", " * ", " / ", " % "]):
            return self._evaluate_arithmetic(expression, context)

        # Simple variable reference
        return self._evaluate_variable(expression, context)

    def _evaluate_variable(self, expression: str, context: dict) -> Any:
        """Evaluate a variable reference like $prev.data.items."""
        if not expression.startswith("$"):
            # Literal value
            # Try to parse as number
            try:
                if "." in expression:
                    return float(expression)
                return int(expression)
            except ValueError:
                pass

            # String literal (quoted)
            if expression.startswith('"') and expression.endswith('"'):
                return expression[1:-1]
            if expression.startswith("'") and expression.endswith("'"):
                return expression[1:-1]

            # Boolean
            if expression.lower() == "true":
                return True
            if expression.lower() == "false":
                return False
            if expression.lower() in ("null", "none"):
                return None

            return expression

        parts = expression.split(".")
        var_name = parts[0]

        # Get base value from context
        if var_name == "$trigger":
            value = context.get("$trigger", {})
            parts = parts[1:]
        elif var_name == "$prev":
            value = context.get("$prev", {})
            parts = parts[1:]
        elif var_name == "$vars":
            value = context.get("$vars", {})
            parts = parts[1:]
        elif var_name == "$env":
            # Environment variables
            if len(parts) > 1:
                return os.environ.get(parts[1], "")
            return {}
        elif var_name == "$node" or var_name == "$nodes":
            # Node output: $node.NodeName.field or $nodes.node_id.field
            if len(parts) > 1:
                node_ref = parts[1]
                value = context.get("$nodes", {}).get(node_ref, {})
                parts = parts[2:]
            else:
                value = context.get("$nodes", {})
                parts = []
        elif var_name == "$workflow":
            value = context.get("$workflow", {})
            parts = parts[1:]
        elif var_name == "$execution":
            value = context.get("$execution", {})
            parts = parts[1:]
        else:
            value = context.get(var_name, None)
            parts = parts[1:]

        # Navigate path
        for part in parts:
            if value is None:
                return None

            # Special array properties
            if part == "length" and isinstance(value, (list, str, dict)):
                return len(value)
            elif part == "first" and isinstance(value, list):
                return value[0] if len(value) > 0 else None
            elif part == "last" and isinstance(value, list):
                return value[-1] if len(value) > 0 else None
            elif part == "keys" and isinstance(value, dict):
                return list(value.keys())
            elif part == "values" and isinstance(value, dict):
                return list(value.values())

            # Normal access
            if isinstance(value, dict):
                value = value.get(part, None)
            elif isinstance(value, list):
                if part.isdigit() or (part.startswith("-") and part[1:].isdigit()):
                    idx = int(part)
                    value = value[idx] if -len(value) <= idx < len(value) else None
                else:
                    value = None
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

        return value

    def _evaluate_function(self, expression: str, context: dict) -> Any:
        """Evaluate a function call like $now() or $json($prev)."""
        # Parse function name and arguments
        match = re.match(r"\$?(\w+)\s*\((.*)\)$", expression, re.DOTALL)
        if not match:
            return None

        func_name = match.group(1)
        args_str = match.group(2).strip()

        # Get the function
        func = self.BUILTIN_FUNCTIONS.get(func_name)
        if not func:
            raise ExpressionError(f"Unknown function: {func_name}")

        # Parse arguments
        args = []
        kwargs = {}

        if args_str:
            # Simple argument parsing (doesn't handle nested functions well yet)
            raw_args = self._split_args(args_str)

            for arg in raw_args:
                arg = arg.strip()

                # Check for keyword argument
                if "=" in arg and not any(op in arg for op in ["==", "!=", ">=", "<="]):
                    key, value = arg.split("=", 1)
                    kwargs[key.strip()] = self.evaluate(value.strip(), context)
                else:
                    args.append(self.evaluate(arg, context))

        # Call the function
        try:
            if kwargs:
                return func(*args, **kwargs)
            return func(*args)
        except Exception as e:
            raise ExpressionError(f"Error calling {func_name}: {e}")

    def _split_args(self, args_str: str) -> list[str]:
        """Split function arguments handling nested parentheses."""
        args = []
        current = ""
        depth = 0
        in_string = False
        string_char = None

        for char in args_str:
            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
                current += char
            elif char == string_char and in_string:
                in_string = False
                string_char = None
                current += char
            elif char == "(" and not in_string:
                depth += 1
                current += char
            elif char == ")" and not in_string:
                depth -= 1
                current += char
            elif char == "," and depth == 0 and not in_string:
                args.append(current.strip())
                current = ""
            else:
                current += char

        if current.strip():
            args.append(current.strip())

        return args

    def _evaluate_comparison(self, expression: str, context: dict) -> bool:
        """Evaluate a comparison expression."""
        for op in [" == ", " != ", " >= ", " <= ", " > ", " < "]:
            if op in expression:
                left, right = expression.split(op, 1)
                left_val = self.evaluate(left.strip(), context)
                right_val = self.evaluate(right.strip(), context)

                if op == " == ":
                    return left_val == right_val
                elif op == " != ":
                    return left_val != right_val
                elif op == " >= ":
                    return left_val >= right_val
                elif op == " <= ":
                    return left_val <= right_val
                elif op == " > ":
                    return left_val > right_val
                elif op == " < ":
                    return left_val < right_val

        return False

    def _evaluate_logical(self, expression: str, context: dict) -> bool:
        """Evaluate a logical expression."""
        if expression.startswith("!"):
            return not bool(self.evaluate(expression[1:].strip(), context))

        if " && " in expression:
            parts = expression.split(" && ")
            return all(bool(self.evaluate(p.strip(), context)) for p in parts)

        if " || " in expression:
            parts = expression.split(" || ")
            return any(bool(self.evaluate(p.strip(), context)) for p in parts)

        return bool(self.evaluate(expression, context))

    def _evaluate_arithmetic(self, expression: str, context: dict) -> float:
        """Evaluate an arithmetic expression."""
        # Simple evaluation - doesn't handle operator precedence properly
        # For complex expressions, consider using a proper parser

        for op in [" + ", " - ", " * ", " / ", " % "]:
            if op in expression:
                parts = expression.rsplit(op, 1)
                left_val = self.evaluate(parts[0].strip(), context)
                right_val = self.evaluate(parts[1].strip(), context)

                # Convert to numbers
                try:
                    left_num = float(left_val) if left_val is not None else 0
                    right_num = float(right_val) if right_val is not None else 0
                except (ValueError, TypeError):
                    # String concatenation for +
                    if op == " + ":
                        return str(left_val or "") + str(right_val or "")
                    return 0

                if op == " + ":
                    return left_num + right_num
                elif op == " - ":
                    return left_num - right_num
                elif op == " * ":
                    return left_num * right_num
                elif op == " / ":
                    return left_num / right_num if right_num != 0 else 0
                elif op == " % ":
                    return left_num % right_num if right_num != 0 else 0

        return 0


# Singleton instance
_parser: ExpressionParser | None = None


def get_parser() -> ExpressionParser:
    """Get the global expression parser instance."""
    global _parser
    if _parser is None:
        _parser = ExpressionParser()
    return _parser


def resolve_expressions(value: Any, context: dict) -> Any:
    """Convenience function to resolve expressions."""
    return get_parser().resolve(value, context)


def evaluate_expression(expression: str, context: dict) -> Any:
    """Convenience function to evaluate a single expression."""
    return get_parser().evaluate(expression, context)
