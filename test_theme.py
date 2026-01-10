from src.ui.theme import SkynetteTheme

print(f"Initial mode: {SkynetteTheme.get_theme_mode()}")
print(f"BG_PRIMARY (dark): {SkynetteTheme.BG_PRIMARY}")

SkynetteTheme.set_theme_mode("light")
print(f"\nAfter switching to light:")
print(f"Mode: {SkynetteTheme.get_theme_mode()}")
print(f"BG_PRIMARY (light): {SkynetteTheme.BG_PRIMARY}")

SkynetteTheme.set_theme_mode("dark")
print(f"\nAfter switching back to dark:")
print(f"BG_PRIMARY (dark): {SkynetteTheme.BG_PRIMARY}")
