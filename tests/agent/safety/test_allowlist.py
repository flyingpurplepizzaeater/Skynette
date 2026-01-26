"""
Tests for Allowlist and Blocklist Rules

Covers: AutonomyRule, matches_rules
"""

import pytest

from src.agent.safety.allowlist import AutonomyRule, matches_rules


class TestAutonomyRule:
    """Test AutonomyRule dataclass."""

    def test_tool_rule_exact_match(self):
        """Tool rule should match exact tool name."""
        rule = AutonomyRule("allow", "tool", "web_search")
        assert rule.matches("web_search", {})
        assert not rule.matches("web_scrape", {})

    def test_tool_rule_glob_pattern(self):
        """Tool rule should support glob patterns."""
        rule = AutonomyRule("allow", "tool", "web_*")
        assert rule.matches("web_search", {})
        assert rule.matches("web_scrape", {})
        assert not rule.matches("file_read", {})

    def test_path_rule_exact_match(self):
        """Path rule should match exact path."""
        rule = AutonomyRule("block", "path", "/critical/data.txt")
        assert rule.matches("file_write", {"path": "/critical/data.txt"})
        assert not rule.matches("file_write", {"path": "/src/main.py"})

    def test_path_rule_glob_pattern(self):
        """Path rule should support glob patterns."""
        rule = AutonomyRule("allow", "path", "/src/*")
        assert rule.matches("file_write", {"path": "/src/main.py"})
        assert rule.matches("file_write", {"path": "/src/utils.py"})
        assert not rule.matches("file_write", {"path": "/critical/data.txt"})

    def test_path_rule_tool_restriction(self):
        """Path rule with tool_name should only match that tool."""
        rule = AutonomyRule("block", "path", "/critical/*", tool_name="file_delete")
        assert rule.matches("file_delete", {"path": "/critical/data.txt"})
        assert not rule.matches("file_write", {"path": "/critical/data.txt"})

    def test_path_rule_no_path_param(self):
        """Path rule should not match if no path in params."""
        rule = AutonomyRule("allow", "path", "/src/*")
        assert not rule.matches("file_write", {})
        assert not rule.matches("file_write", {"content": "hello"})

    def test_to_dict(self):
        """Rule should serialize to dict."""
        rule = AutonomyRule("allow", "tool", "web_*", tool_name=None)
        d = rule.to_dict()
        assert d["rule_type"] == "allow"
        assert d["scope"] == "tool"
        assert d["pattern"] == "web_*"
        assert d["tool_name"] is None

    def test_from_dict(self):
        """Rule should deserialize from dict."""
        d = {
            "rule_type": "block",
            "scope": "path",
            "pattern": "/critical/*",
            "tool_name": "file_delete",
        }
        rule = AutonomyRule.from_dict(d)
        assert rule.rule_type == "block"
        assert rule.scope == "path"
        assert rule.pattern == "/critical/*"
        assert rule.tool_name == "file_delete"


class TestMatchesRules:
    """Test matches_rules function."""

    def test_empty_rules_returns_none(self):
        """No rules should return None (use autonomy level)."""
        result = matches_rules("any_tool", {}, [], [])
        assert result is None

    def test_allowlist_match_returns_true(self):
        """Matching allowlist rule should return True."""
        allowlist = [AutonomyRule("allow", "tool", "web_search")]
        result = matches_rules("web_search", {}, allowlist, [])
        assert result is True

    def test_blocklist_match_returns_false(self):
        """Matching blocklist rule should return False."""
        blocklist = [AutonomyRule("block", "tool", "file_delete")]
        result = matches_rules("file_delete", {}, [], blocklist)
        assert result is False

    def test_blocklist_priority_over_allowlist(self):
        """Blocklist should take priority when both match."""
        allowlist = [AutonomyRule("allow", "tool", "file_*")]
        blocklist = [AutonomyRule("block", "tool", "file_delete")]
        # file_delete matches both, but blocklist wins
        result = matches_rules("file_delete", {}, allowlist, blocklist)
        assert result is False

    def test_no_match_returns_none(self):
        """Non-matching rules should return None."""
        allowlist = [AutonomyRule("allow", "tool", "web_*")]
        blocklist = [AutonomyRule("block", "tool", "file_delete")]
        # code_execute doesn't match either
        result = matches_rules("code_execute", {}, allowlist, blocklist)
        assert result is None

    def test_path_rules_with_params(self):
        """Path rules should use params for matching."""
        allowlist = [AutonomyRule("allow", "path", "/src/*")]
        blocklist = [AutonomyRule("block", "path", "/src/secret/*")]

        # /src/main.py matches allowlist
        result = matches_rules("file_write", {"path": "/src/main.py"}, allowlist, blocklist)
        assert result is True

        # /src/secret/key.txt matches blocklist (priority)
        result = matches_rules("file_write", {"path": "/src/secret/key.txt"}, allowlist, blocklist)
        assert result is False

        # /other/file.txt matches neither
        result = matches_rules("file_write", {"path": "/other/file.txt"}, allowlist, blocklist)
        assert result is None
