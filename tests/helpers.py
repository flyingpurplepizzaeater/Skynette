"""Shared test utilities."""

import flet as ft


def extract_text_from_control(control) -> str:
    """Recursively extract all text from a Flet control tree."""
    texts = []

    if isinstance(control, ft.Text):
        if control.value:
            texts.append(str(control.value))

    if isinstance(control, ft.ElevatedButton):
        # ElevatedButton doesn't have 'text' attribute, just skip it
        # The button text would be in its content/controls if any
        pass

    if hasattr(control, 'controls') and control.controls:
        for child in control.controls:
            texts.append(extract_text_from_control(child))

    if hasattr(control, 'content') and control.content:
        if isinstance(control.content, str):
            texts.append(control.content)
        elif isinstance(control.content, list):
            for item in control.content:
                texts.append(extract_text_from_control(item))
        else:
            texts.append(extract_text_from_control(control.content))

    return ' '.join(filter(None, texts))
