# src/ui/views/ai_hub/state.py
"""Centralized state for AI Hub components."""

from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class AIHubState:
    """Centralized state for AI Hub components.

    Provides reactive state management with listener pattern for
    coordinating updates across wizard, providers, and model library components.
    """

    # Wizard state
    wizard_step: int = 0
    selected_providers: list[str] = field(default_factory=list)
    provider_configs: dict[str, Any] = field(default_factory=dict)

    # Ollama status
    ollama_connected: bool = False
    ollama_models: list[str] = field(default_factory=list)

    # Listeners for reactive updates
    _listeners: list[Callable[[], None]] = field(default_factory=list, repr=False)

    def add_listener(self, callback: Callable[[], None]) -> None:
        """Register a callback to be notified of state changes."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[], None]) -> None:
        """Unregister a callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify(self) -> None:
        """Notify all listeners of state change."""
        for listener in self._listeners:
            listener()

    # State mutation methods
    def set_wizard_step(self, step: int) -> None:
        """Set wizard step and notify listeners."""
        self.wizard_step = step
        self.notify()

    def toggle_provider(self, provider: str) -> None:
        """Toggle provider selection and notify listeners."""
        if provider in self.selected_providers:
            self.selected_providers.remove(provider)
        else:
            self.selected_providers.append(provider)
        self.notify()

    def set_provider_config(self, provider: str, config: dict) -> None:
        """Set provider configuration and notify listeners."""
        self.provider_configs[provider] = config
        self.notify()

    def update_provider_config(self, provider: str, key: str, value: Any) -> None:
        """Update a specific key in provider config."""
        if provider not in self.provider_configs:
            self.provider_configs[provider] = {}
        self.provider_configs[provider][key] = value
        self.notify()

    def set_ollama_status(self, connected: bool, models: list[str] = None) -> None:
        """Update Ollama connection status."""
        self.ollama_connected = connected
        if models is not None:
            self.ollama_models = models
        self.notify()

    def reset_wizard(self) -> None:
        """Reset wizard state to initial values."""
        self.wizard_step = 0
        self.selected_providers = []
        self.provider_configs = {}
        self.notify()
