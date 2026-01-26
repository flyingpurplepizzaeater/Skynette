"""
Autonomy Badge Component

Color-coded badge showing current autonomy level.
"""

import flet as ft

from src.agent.safety.autonomy import (
    AutonomyLevel,
    AUTONOMY_COLORS,
    AUTONOMY_LABELS,
)
from src.ui.theme import Theme


class AutonomyBadge(ft.Container):
    """
    Color-coded badge displaying autonomy level.

    Shows a colored dot + level label (e.g., "[*] L2" in emerald).
    Follows RiskBadge pattern for consistent styling.
    """

    def __init__(self, level: AutonomyLevel, compact: bool = False):
        """
        Initialize autonomy badge.

        Args:
            level: The autonomy level to display
            compact: If True, show only the dot (no label)
        """
        self.level = level
        self.compact = compact

        color = AUTONOMY_COLORS.get(level, Theme.TEXT_MUTED)
        label = AUTONOMY_LABELS.get(level, level)

        # Build content
        if compact:
            content = ft.Container(
                width=10,
                height=10,
                border_radius=5,
                bgcolor=color,
                tooltip=f"{level}: {label}",
            )
            padding_val = 0
        else:
            content = ft.Row(
                controls=[
                    ft.Container(
                        width=8,
                        height=8,
                        border_radius=4,
                        bgcolor=color,
                    ),
                    ft.Text(
                        level,
                        color=color,
                        size=Theme.FONT_SM,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                spacing=Theme.SPACING_XS,
            )
            padding_val = ft.padding.symmetric(
                horizontal=Theme.SPACING_SM,
                vertical=2,
            )

        super().__init__(
            content=content,
            bgcolor=f"{color}20",  # 20% opacity background
            border=ft.border.all(1, color),
            border_radius=Theme.RADIUS_SM,
            padding=padding_val,
        )

    def update_level(self, level: AutonomyLevel):
        """Update the displayed autonomy level."""
        self.level = level
        color = AUTONOMY_COLORS.get(level, Theme.TEXT_MUTED)
        label = AUTONOMY_LABELS.get(level, level)

        self.bgcolor = f"{color}20"
        self.border = ft.border.all(1, color)

        if self.compact:
            # Update tooltip
            self.content.tooltip = f"{level}: {label}"
            self.content.bgcolor = color
        else:
            # Update the dot and text
            row = self.content
            if isinstance(row, ft.Row) and len(row.controls) >= 2:
                row.controls[0].bgcolor = color
                row.controls[1].color = color
                row.controls[1].value = level

        self.update()
