"""
Allowlist and Blocklist Rules

Pattern-based rules for overriding autonomy level decisions.
"""

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Literal, Optional


@dataclass
class AutonomyRule:
    """
    Rule for overriding autonomy approval decisions.

    Attributes:
        rule_type: "allow" (skip approval) or "block" (require approval)
        scope: "tool" (matches tool name) or "path" (matches file path param)
        pattern: Glob pattern to match against (e.g., "web_search" or "/src/*")
        tool_name: For path rules, optionally limit to specific tool
    """

    rule_type: Literal["allow", "block"]
    scope: Literal["tool", "path"]
    pattern: str
    tool_name: Optional[str] = None

    def matches(self, tool: str, params: dict) -> bool:
        """
        Check if this rule matches the given tool call.

        Args:
            tool: Tool name being called
            params: Tool parameters

        Returns:
            True if rule matches, False otherwise
        """
        if self.scope == "tool":
            return fnmatch(tool, self.pattern)

        if self.scope == "path":
            # Tool restriction check
            if self.tool_name is not None and self.tool_name != tool:
                return False

            # Path pattern check
            path = params.get("path", "")
            if not path:
                return False
            return fnmatch(path, self.pattern)

        return False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "rule_type": self.rule_type,
            "scope": self.scope,
            "pattern": self.pattern,
            "tool_name": self.tool_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AutonomyRule":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            rule_type=data["rule_type"],
            scope=data["scope"],
            pattern=data["pattern"],
            tool_name=data.get("tool_name"),
        )


def matches_rules(
    tool_name: str,
    params: dict,
    allowlist: list[AutonomyRule],
    blocklist: list[AutonomyRule],
) -> Optional[bool]:
    """
    Check if action matches any allowlist or blocklist rules.

    Blocklist rules take priority over allowlist rules.

    Args:
        tool_name: Name of the tool being called
        params: Tool parameters
        allowlist: List of allow rules
        blocklist: List of block rules

    Returns:
        True if explicitly allowed (skip approval)
        False if explicitly blocked (require approval)
        None if no rule matches (use autonomy level threshold)
    """
    # Check blocklist first (higher priority)
    for rule in blocklist:
        if rule.matches(tool_name, params):
            return False  # Blocked = require approval

    # Check allowlist
    for rule in allowlist:
        if rule.matches(tool_name, params):
            return True  # Allowed = skip approval

    # No matching rule
    return None
