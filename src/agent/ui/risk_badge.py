"""
Risk Badge Component

Color-coded badge showing action risk level.
"""

import flet as ft

from src.agent.safety.classification import RiskLevel, RISK_COLORS, RISK_LABELS
from src.ui.theme import Theme


class RiskBadge(ft.Container):
    """
    Color-coded badge displaying risk level.

    Shows a colored dot + label (e.g., "[*] Destructive" in orange).
    Follows Theme patterns for consistent styling.
    """

    def __init__(self, risk_level: RiskLevel, compact: bool = False):
        """
        Initialize risk badge.

        Args:
            risk_level: The risk level to display
            compact: If True, show only the dot (no label)
        """
        self.risk_level = risk_level
        self.compact = compact

        color = RISK_COLORS.get(risk_level, Theme.TEXT_MUTED)
        label = RISK_LABELS.get(risk_level, risk_level)

        # Build content
        if compact:
            content = ft.Container(
                width=10,
                height=10,
                border_radius=5,
                bgcolor=color,
                tooltip=label,
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
                        label,
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

    def update_risk_level(self, risk_level: RiskLevel):
        """Update the displayed risk level."""
        self.risk_level = risk_level
        color = RISK_COLORS.get(risk_level, Theme.TEXT_MUTED)
        label = RISK_LABELS.get(risk_level, risk_level)

        self.bgcolor = f"{color}20"
        self.border = ft.border.all(1, color)

        if not self.compact:
            # Update the dot and text
            row = self.content
            if isinstance(row, ft.Row) and len(row.controls) >= 2:
                row.controls[0].bgcolor = color
                row.controls[1].color = color
                row.controls[1].value = label

        self.update()
