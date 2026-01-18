# src/services/editor/highlighter.py
"""Pygments-based syntax highlighting service for Flet code editor."""

import flet as ft
from pygments import lex
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
from pygments.token import Token
from pygments.util import ClassNotFound


class PygmentsHighlighter:
    """Convert code to Flet TextSpans with syntax highlighting.

    Uses Pygments for tokenization and maps token types to colors
    based on the GitHub Dark theme for consistent styling.

    Example:
        highlighter = PygmentsHighlighter()
        spans = highlighter.highlight("def hello(): pass", "python")
        text = ft.Text(spans=spans, font_family="monospace")
    """

    # GitHub Dark theme color mapping
    TOKEN_COLORS = {
        # Keywords
        Token.Keyword: "#ff7b72",
        Token.Keyword.Constant: "#79c0ff",
        Token.Keyword.Declaration: "#ff7b72",
        Token.Keyword.Namespace: "#ff7b72",
        Token.Keyword.Pseudo: "#ff7b72",
        Token.Keyword.Reserved: "#ff7b72",
        Token.Keyword.Type: "#79c0ff",
        # Names
        Token.Name.Function: "#d2a8ff",
        Token.Name.Function.Magic: "#d2a8ff",
        Token.Name.Class: "#f0883e",
        Token.Name.Builtin: "#ffa657",
        Token.Name.Builtin.Pseudo: "#79c0ff",
        Token.Name.Decorator: "#d2a8ff",
        Token.Name.Exception: "#f0883e",
        Token.Name.Variable: "#c9d1d9",
        Token.Name.Variable.Class: "#c9d1d9",
        Token.Name.Variable.Global: "#c9d1d9",
        Token.Name.Variable.Instance: "#c9d1d9",
        Token.Name.Variable.Magic: "#79c0ff",
        Token.Name.Attribute: "#c9d1d9",
        Token.Name.Tag: "#7ee787",
        Token.Name.Label: "#c9d1d9",
        Token.Name.Namespace: "#c9d1d9",
        Token.Name.Constant: "#79c0ff",
        # Strings
        Token.String: "#a5d6ff",
        Token.String.Affix: "#79c0ff",
        Token.String.Backtick: "#a5d6ff",
        Token.String.Char: "#a5d6ff",
        Token.String.Delimiter: "#a5d6ff",
        Token.String.Doc: "#8b949e",
        Token.String.Double: "#a5d6ff",
        Token.String.Escape: "#79c0ff",
        Token.String.Heredoc: "#a5d6ff",
        Token.String.Interpol: "#c9d1d9",
        Token.String.Other: "#a5d6ff",
        Token.String.Regex: "#7ee787",
        Token.String.Single: "#a5d6ff",
        Token.String.Symbol: "#79c0ff",
        # Comments
        Token.Comment: "#8b949e",
        Token.Comment.Hashbang: "#8b949e",
        Token.Comment.Multiline: "#8b949e",
        Token.Comment.Preproc: "#ff7b72",
        Token.Comment.PreprocFile: "#a5d6ff",
        Token.Comment.Single: "#8b949e",
        Token.Comment.Special: "#8b949e",
        # Numbers
        Token.Number: "#79c0ff",
        Token.Number.Bin: "#79c0ff",
        Token.Number.Float: "#79c0ff",
        Token.Number.Hex: "#79c0ff",
        Token.Number.Integer: "#79c0ff",
        Token.Number.Integer.Long: "#79c0ff",
        Token.Number.Oct: "#79c0ff",
        # Operators
        Token.Operator: "#ff7b72",
        Token.Operator.Word: "#ff7b72",
        # Punctuation
        Token.Punctuation: "#c9d1d9",
        Token.Punctuation.Marker: "#c9d1d9",
        # Generic tokens
        Token.Generic.Deleted: "#ffa198",
        Token.Generic.Emph: "#c9d1d9",
        Token.Generic.Error: "#ffa198",
        Token.Generic.Heading: "#79c0ff",
        Token.Generic.Inserted: "#7ee787",
        Token.Generic.Output: "#8b949e",
        Token.Generic.Prompt: "#8b949e",
        Token.Generic.Strong: "#c9d1d9",
        Token.Generic.Subheading: "#79c0ff",
        Token.Generic.Traceback: "#ffa198",
        # Literal
        Token.Literal: "#79c0ff",
        Token.Literal.Date: "#79c0ff",
        # Error
        Token.Error: "#ffa198",
    }
    DEFAULT_COLOR = "#c9d1d9"

    def highlight(self, code: str, language: str) -> list[ft.TextSpan]:
        """Convert code to list of styled TextSpans.

        Args:
            code: The source code to highlight.
            language: The language name (e.g., "python", "javascript").

        Returns:
            A list of Flet TextSpan objects with appropriate styling.
            If the language is unknown, returns unstyled text.
        """
        try:
            lexer = get_lexer_by_name(language)
        except ClassNotFound:
            # Fallback: return unstyled text
            return [
                ft.TextSpan(
                    code,
                    style=ft.TextStyle(
                        color=self.DEFAULT_COLOR,
                        font_family="monospace",
                    ),
                )
            ]

        spans = []
        for token_type, token_value in lex(code, lexer):
            color = self._get_color_for_token(token_type)
            spans.append(
                ft.TextSpan(
                    token_value,
                    style=ft.TextStyle(
                        color=color,
                        font_family="monospace",
                    ),
                )
            )
        return spans

    def get_language_from_filename(self, filename: str) -> str:
        """Detect language from filename extension.

        Args:
            filename: The filename including extension.

        Returns:
            The detected language name, or "text" if unknown.
        """
        try:
            lexer = get_lexer_for_filename(filename)
            return lexer.aliases[0] if lexer.aliases else lexer.name.lower()
        except ClassNotFound:
            return "text"

    def _get_color_for_token(self, token_type) -> str:
        """Get color for token type, checking parent types.

        Args:
            token_type: A Pygments token type.

        Returns:
            The hex color string for the token type.
        """
        # Walk up the token type hierarchy to find a matching color
        current = token_type
        while current:
            if current in self.TOKEN_COLORS:
                return self.TOKEN_COLORS[current]
            current = current.parent
        return self.DEFAULT_COLOR
