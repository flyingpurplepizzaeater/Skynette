"""
Approval Detail Level Renderers

Functions that render different detail levels for approval content.
Supports minimal, detailed, and progressive disclosure patterns.
"""

import json
from typing import Optional

import flet as ft

from src.agent.safety.classification import ActionClassification
from src.agent.ui.risk_badge import RiskBadge
from src.ui.theme import Theme


def render_minimal(classification: ActionClassification) -> ft.Control:
    """
    Render minimal detail level - tool name + risk badge only.

    Shows a one-line summary without parameters.

    Args:
        classification: The action classification to render

    Returns:
        ft.Container with minimal content
    """
    return ft.Container(
        padding=Theme.SPACING_SM,
        content=ft.Row(
            controls=[
                RiskBadge(classification.risk_level),
                ft.Text(
                    classification.tool_name,
                    weight=ft.FontWeight.BOLD,
                    size=Theme.FONT_MD,
                ),
            ],
            spacing=Theme.SPACING_SM,
            alignment=ft.MainAxisAlignment.START,
        ),
    )


def render_detailed(
    classification: ActionClassification,
    max_chars: int = 500,
) -> ft.Control:
    """
    Render detailed level - full parameters in scrollable code block.

    Shows tool name, risk badge, full reason text, and parameters.

    Args:
        classification: The action classification to render
        max_chars: Maximum characters for parameter display (default 500)

    Returns:
        ft.Container with detailed content
    """
    # Truncate parameters for display
    params_str = json.dumps(classification.parameters, indent=2)
    if len(params_str) > max_chars:
        params_str = params_str[:max_chars] + "\n..."

    return ft.Container(
        padding=Theme.SPACING_SM,
        content=ft.Column(
            controls=[
                # Header: Risk badge + tool name
                ft.Row(
                    controls=[
                        RiskBadge(classification.risk_level),
                        ft.Text(
                            classification.tool_name,
                            weight=ft.FontWeight.BOLD,
                            size=Theme.FONT_LG,
                        ),
                    ],
                    spacing=Theme.SPACING_SM,
                ),

                # Reason
                ft.Text(
                    classification.reason,
                    color=Theme.TEXT_SECONDARY,
                    size=Theme.FONT_SM,
                ),

                ft.Divider(height=Theme.SPACING_SM),

                # Parameters preview
                ft.Text(
                    "Parameters:",
                    size=Theme.FONT_SM,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Container(
                    bgcolor=Theme.BG_TERTIARY,
                    border_radius=Theme.RADIUS_SM,
                    padding=Theme.SPACING_SM,
                    content=ft.Text(
                        params_str,
                        font_family="monospace",
                        size=Theme.FONT_XS,
                        selectable=True,
                    ),
                ),
            ],
            spacing=Theme.SPACING_SM,
            tight=True,
        ),
    )


def render_progressive(
    classification: ActionClassification,
    expanded: bool = False,
    on_expand: Optional[callable] = None,
    max_chars: int = 500,
) -> ft.Control:
    """
    Render progressive level - start minimal, expand for detail.

    Shows minimal view by default with a "Show details" button.
    When expanded, shows full details like render_detailed.

    Args:
        classification: The action classification to render
        expanded: Whether to start in expanded state
        on_expand: Optional callback when expand state changes
        max_chars: Maximum characters for parameter display when expanded

    Returns:
        ft.Container with progressive disclosure content
    """
    # Truncate parameters for display
    params_str = json.dumps(classification.parameters, indent=2)
    if len(params_str) > max_chars:
        params_str = params_str[:max_chars] + "\n..."

    # Build the header (always visible)
    header = ft.Row(
        controls=[
            RiskBadge(classification.risk_level),
            ft.Text(
                classification.tool_name,
                weight=ft.FontWeight.BOLD,
                size=Theme.FONT_MD,
            ),
        ],
        spacing=Theme.SPACING_SM,
        alignment=ft.MainAxisAlignment.START,
    )

    # Build the detail content (shown when expanded)
    detail_content = ft.Column(
        controls=[
            # Reason
            ft.Text(
                classification.reason,
                color=Theme.TEXT_SECONDARY,
                size=Theme.FONT_SM,
            ),

            ft.Divider(height=Theme.SPACING_SM),

            # Parameters preview
            ft.Text(
                "Parameters:",
                size=Theme.FONT_SM,
                weight=ft.FontWeight.W_500,
            ),
            ft.Container(
                bgcolor=Theme.BG_TERTIARY,
                border_radius=Theme.RADIUS_SM,
                padding=Theme.SPACING_SM,
                content=ft.Text(
                    params_str,
                    font_family="monospace",
                    size=Theme.FONT_XS,
                    selectable=True,
                ),
            ),
        ],
        spacing=Theme.SPACING_SM,
        tight=True,
        visible=expanded,
    )

    # State container for tracking expansion
    class ProgressiveContainer(ft.Container):
        """Container that manages progressive disclosure state."""

        def __init__(self, header: ft.Control, details: ft.Column, is_expanded: bool):
            self._is_expanded = is_expanded
            self._details = details
            self._expand_btn = ft.TextButton(
                "Hide details" if is_expanded else "Show details",
                icon=ft.Icons.EXPAND_LESS if is_expanded else ft.Icons.EXPAND_MORE,
                on_click=self._toggle_expand,
            )

            super().__init__(
                padding=Theme.SPACING_SM,
                content=ft.Column(
                    controls=[
                        header,
                        self._expand_btn,
                        details,
                    ],
                    spacing=Theme.SPACING_XS,
                    tight=True,
                ),
            )

        def _toggle_expand(self, e):
            """Toggle expansion state."""
            self._is_expanded = not self._is_expanded
            self._details.visible = self._is_expanded
            self._expand_btn.text = "Hide details" if self._is_expanded else "Show details"
            self._expand_btn.icon = (
                ft.Icons.EXPAND_LESS if self._is_expanded else ft.Icons.EXPAND_MORE
            )
            if on_expand:
                on_expand(self._is_expanded)
            self.update()

    return ProgressiveContainer(header, detail_content, expanded)


# Type alias for detail level values
DetailLevel = str  # "minimal" | "detailed" | "progressive"

# Renderer mapping for convenience
DETAIL_RENDERERS = {
    "minimal": render_minimal,
    "detailed": render_detailed,
    "progressive": render_progressive,
}


def render_by_level(
    classification: ActionClassification,
    level: DetailLevel,
    **kwargs,
) -> ft.Control:
    """
    Render classification content by detail level name.

    Args:
        classification: The action classification to render
        level: Detail level ("minimal", "detailed", or "progressive")
        **kwargs: Additional arguments passed to the renderer

    Returns:
        ft.Control with rendered content

    Raises:
        ValueError: If level is not recognized
    """
    renderer = DETAIL_RENDERERS.get(level)
    if renderer is None:
        raise ValueError(f"Unknown detail level: {level}. Use: minimal, detailed, progressive")

    return renderer(classification, **kwargs)
