"""
Skynette Theme Configuration

Defines colors, fonts, and styling for the application.
"""

import flet as ft


class SkynetteTheme:
    """Theme configuration for Skynette application."""

    # Brand Colors
    PRIMARY = "#6366F1"  # Indigo
    PRIMARY_LIGHT = "#818CF8"
    PRIMARY_DARK = "#4F46E5"

    SECONDARY = "#10B981"  # Emerald
    SECONDARY_LIGHT = "#34D399"
    SECONDARY_DARK = "#059669"

    # Semantic Colors
    SUCCESS = "#22C55E"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"

    # Neutral Colors (Dark Theme)
    BG_PRIMARY = "#0F172A"  # Slate 900
    BG_SECONDARY = "#1E293B"  # Slate 800
    BG_TERTIARY = "#334155"  # Slate 700
    BG_ELEVATED = "#1E293B"
    SURFACE = "#1E293B"  # Same as BG_SECONDARY for surface elements

    TEXT_PRIMARY = "#F8FAFC"  # Slate 50
    TEXT_SECONDARY = "#94A3B8"  # Slate 400
    TEXT_MUTED = "#64748B"  # Slate 500

    BORDER = "#334155"  # Slate 700
    BORDER_LIGHT = "#475569"  # Slate 600

    # Node Category Colors
    NODE_COLORS = {
        "ai": "#8B5CF6",  # Violet
        "trigger": "#F59E0B",  # Amber
        "http": "#3B82F6",  # Blue
        "data": "#10B981",  # Emerald
        "flow": "#EC4899",  # Pink
        "database": "#06B6D4",  # Cyan
        "apps": "#F97316",  # Orange
        "utility": "#6B7280",  # Gray
    }

    # Spacing
    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 16
    SPACING_LG = 24
    SPACING_XL = 32

    # Border Radius
    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 12
    RADIUS_XL = 16

    # Font Sizes
    FONT_XS = 11
    FONT_SM = 13
    FONT_MD = 14
    FONT_LG = 16
    FONT_XL = 20
    FONT_XXL = 24

    # Sidebar
    SIDEBAR_WIDTH = 64
    SIDEBAR_EXPANDED_WIDTH = 240

    @classmethod
    def get_flet_theme(cls) -> ft.Theme:
        """Get the Flet theme configuration."""
        return ft.Theme(
            color_scheme_seed=cls.PRIMARY,
            color_scheme=ft.ColorScheme(
                primary=cls.PRIMARY,
                secondary=cls.SECONDARY,
                surface=cls.BG_SECONDARY,
                error=cls.ERROR,
                on_primary=cls.TEXT_PRIMARY,
                on_secondary=cls.TEXT_PRIMARY,
                on_surface=cls.TEXT_PRIMARY,
                on_error=cls.TEXT_PRIMARY,
            ),
            text_theme=ft.TextTheme(
                body_large=ft.TextStyle(size=cls.FONT_LG, color=cls.TEXT_PRIMARY),
                body_medium=ft.TextStyle(size=cls.FONT_MD, color=cls.TEXT_PRIMARY),
                body_small=ft.TextStyle(size=cls.FONT_SM, color=cls.TEXT_SECONDARY),
                title_large=ft.TextStyle(
                    size=cls.FONT_XXL, weight=ft.FontWeight.BOLD, color=cls.TEXT_PRIMARY
                ),
                title_medium=ft.TextStyle(
                    size=cls.FONT_XL, weight=ft.FontWeight.W_600, color=cls.TEXT_PRIMARY
                ),
                title_small=ft.TextStyle(
                    size=cls.FONT_LG, weight=ft.FontWeight.W_500, color=cls.TEXT_PRIMARY
                ),
            ),
        )

    @classmethod
    def card_style(cls) -> dict:
        """Get common card styling."""
        return {
            "bgcolor": cls.BG_SECONDARY,
            "border_radius": cls.RADIUS_LG,
            "padding": cls.SPACING_MD,
        }

    @classmethod
    def button_style(cls, variant: str = "primary") -> dict:
        """Get button styling based on variant."""
        if variant == "primary":
            return {
                "bgcolor": cls.PRIMARY,
                "color": cls.TEXT_PRIMARY,
            }
        elif variant == "secondary":
            return {
                "bgcolor": cls.BG_TERTIARY,
                "color": cls.TEXT_PRIMARY,
            }
        elif variant == "ghost":
            return {
                "bgcolor": "transparent",
                "color": cls.TEXT_SECONDARY,
            }
        return {}


# Alias for convenience
Theme = SkynetteTheme
