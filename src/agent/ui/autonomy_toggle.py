"""
Autonomy Toggle Component

Quick dropdown for selecting autonomy level.
"""

from typing import Callable, Optional

import flet as ft

from src.agent.safety.autonomy import (
    AutonomyLevel,
    AUTONOMY_COLORS,
    AUTONOMY_LABELS,
)
from src.agent.ui.autonomy_badge import AutonomyBadge
from src.ui.theme import Theme


class AutonomyToggle(ft.Container):
    """
    Clickable autonomy badge that opens a dropdown for level selection.

    Provides instant level switching without confirmation dialog.
    """

    def __init__(
        self,
        level: AutonomyLevel = "L2",
        on_level_change: Optional[Callable[[AutonomyLevel], None]] = None,
    ):
        """
        Initialize autonomy toggle.

        Args:
            level: Initial autonomy level
            on_level_change: Callback when level changes
        """
        self._level = level
        self._on_level_change = on_level_change

        # Badge display
        self._badge = AutonomyBadge(level=level, compact=False)

        # Popup menu for level selection
        self._popup = ft.PopupMenuButton(
            items=self._build_menu_items(),
            tooltip="Change autonomy level",
            content=self._badge,
        )

        super().__init__(
            content=self._popup,
        )

    def _build_menu_items(self) -> list[ft.PopupMenuItem]:
        """Build popup menu items for each level."""
        items = []
        for lvl in ["L1", "L2", "L3", "L4"]:
            color = AUTONOMY_COLORS.get(lvl, Theme.TEXT_MUTED)
            label = AUTONOMY_LABELS.get(lvl, lvl)
            is_current = lvl == self._level

            items.append(ft.PopupMenuItem(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            width=8,
                            height=8,
                            border_radius=4,
                            bgcolor=color,
                        ),
                        ft.Text(
                            f"{lvl}: {label}",
                            color=Theme.TEXT_PRIMARY if is_current else Theme.TEXT_SECONDARY,
                            weight=ft.FontWeight.W_600 if is_current else ft.FontWeight.W_400,
                            size=Theme.FONT_SM,
                        ),
                        ft.Icon(
                            ft.Icons.CHECK,
                            size=14,
                            color=color,
                            visible=is_current,
                        ),
                    ],
                    spacing=Theme.SPACING_SM,
                ),
                on_click=lambda e, l=lvl: self._select_level(l),
            ))

        return items

    def _select_level(self, level: str):
        """Handle level selection from menu."""
        if level in ("L1", "L2", "L3", "L4") and level != self._level:
            self._level = level  # type: ignore
            self._badge.update_level(level)  # type: ignore

            # Rebuild menu to update checkmarks
            self._popup.items = self._build_menu_items()
            self._popup.update()

            # Notify callback
            if self._on_level_change:
                self._on_level_change(level)  # type: ignore

    def set_level(self, level: AutonomyLevel):
        """
        Set the autonomy level programmatically.

        Args:
            level: New autonomy level
        """
        if level != self._level:
            self._level = level
            self._badge.update_level(level)
            self._popup.items = self._build_menu_items()
            self._popup.update()

    @property
    def level(self) -> AutonomyLevel:
        """Get current autonomy level."""
        return self._level
