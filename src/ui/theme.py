"""
Skynette Theme Configuration

Defines colors, fonts, and styling for the application.
"""

import flet as ft


class ThemeMeta(type):
    """Metaclass to handle dynamic theme properties."""

    _dynamic_attrs = {
        "BG_PRIMARY": ("DARK_BG_PRIMARY", "LIGHT_BG_PRIMARY"),
        "BG_SECONDARY": ("DARK_BG_SECONDARY", "LIGHT_BG_SECONDARY"),
        "BG_TERTIARY": ("DARK_BG_TERTIARY", "LIGHT_BG_TERTIARY"),
        "BG_ELEVATED": ("DARK_BG_SECONDARY", "LIGHT_BG_SECONDARY"),
        "SURFACE": ("DARK_BG_SECONDARY", "LIGHT_BG_SECONDARY"),
        "TEXT_PRIMARY": ("DARK_TEXT_PRIMARY", "LIGHT_TEXT_PRIMARY"),
        "TEXT_SECONDARY": ("DARK_TEXT_SECONDARY", "LIGHT_TEXT_SECONDARY"),
        "TEXT_MUTED": ("DARK_TEXT_MUTED", "LIGHT_TEXT_MUTED"),
        "BORDER": ("DARK_BORDER", "LIGHT_BORDER"),
        "BORDER_LIGHT": ("DARK_BORDER_LIGHT", "LIGHT_BORDER_LIGHT"),
    }

    def __getattribute__(cls, name):
        """Override attribute access to provide dynamic theme colors."""
        # Get _dynamic_attrs dict without triggering recursion
        dynamic_attrs = object.__getattribute__(cls, "_dynamic_attrs")

        if name in dynamic_attrs:
            dark_attr, light_attr = dynamic_attrs[name]
            current_mode = type.__getattribute__(cls, "_current_mode")
            attr_name = dark_attr if current_mode == "dark" else light_attr
            return type.__getattribute__(cls, attr_name)

        return type.__getattribute__(cls, name)


class SkynetteTheme(metaclass=ThemeMeta):
    """Theme configuration for Skynette application."""

    # Current theme mode
    _current_mode = "dark"  # "dark" or "light"

    # Brand Colors (same for both themes)
    PRIMARY = "#6366F1"  # Indigo
    PRIMARY_LIGHT = "#818CF8"
    PRIMARY_DARK = "#4F46E5"

    SECONDARY = "#10B981"  # Emerald
    SECONDARY_LIGHT = "#34D399"
    SECONDARY_DARK = "#059669"

    # Semantic Colors (same for both themes)
    SUCCESS = "#22C55E"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"

    # Dark Theme Colors
    DARK_BG_PRIMARY = "#0F172A"  # Slate 900
    DARK_BG_SECONDARY = "#1E293B"  # Slate 800
    DARK_BG_TERTIARY = "#334155"  # Slate 700
    DARK_TEXT_PRIMARY = "#F8FAFC"  # Slate 50
    DARK_TEXT_SECONDARY = "#94A3B8"  # Slate 400
    DARK_TEXT_MUTED = "#64748B"  # Slate 500
    DARK_BORDER = "#334155"  # Slate 700
    DARK_BORDER_LIGHT = "#475569"  # Slate 600

    # Light Theme Colors
    LIGHT_BG_PRIMARY = "#F8FAFC"  # Slate 50
    LIGHT_BG_SECONDARY = "#FFFFFF"  # White
    LIGHT_BG_TERTIARY = "#E2E8F0"  # Slate 200
    LIGHT_TEXT_PRIMARY = "#0F172A"  # Slate 900
    LIGHT_TEXT_SECONDARY = "#64748B"  # Slate 500
    LIGHT_TEXT_MUTED = "#94A3B8"  # Slate 400
    LIGHT_BORDER = "#CBD5E1"  # Slate 300
    LIGHT_BORDER_LIGHT = "#E2E8F0"  # Slate 200

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

    @classmethod
    def set_theme_mode(cls, mode: str):
        """Set the current theme mode."""
        if mode in ("dark", "light"):
            cls._current_mode = mode

    @classmethod
    def get_theme_mode(cls) -> str:
        """Get the current theme mode."""
        return cls._current_mode


# Alias for convenience
Theme = SkynetteTheme
