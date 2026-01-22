"""
Kill Switch

Emergency stop mechanism that operates outside the agent event loop.
Uses multiprocessing.Event for cross-thread/process communication.
"""

import logging
import multiprocessing
from datetime import UTC, datetime
from typing import Optional

logger = logging.getLogger(__name__)


class KillSwitch:
    """
    Kill switch for emergency agent termination.

    Uses multiprocessing.Event for inter-process communication,
    allowing the kill switch to work even if the agent loop is blocked.

    Usage:
        kill_switch = KillSwitch()

        # In UI/external thread:
        kill_switch.trigger()

        # In agent loop:
        if kill_switch.is_triggered():
            # Stop execution
            pass

        # Reset for new execution:
        kill_switch.reset()
    """

    def __init__(self):
        """Initialize kill switch with multiprocessing Event."""
        self._stop_event = multiprocessing.Event()
        self._triggered_at: Optional[datetime] = None
        self._trigger_reason: Optional[str] = None

    def trigger(self, reason: str = "Kill switch activated"):
        """
        Trigger the kill switch.

        Can be called from any thread or process.

        Args:
            reason: Human-readable reason for triggering
        """
        self._stop_event.set()
        self._triggered_at = datetime.now(UTC)
        self._trigger_reason = reason
        logger.warning(f"Kill switch triggered: {reason}")

    def is_triggered(self) -> bool:
        """
        Check if kill switch has been triggered.

        Non-blocking check that can be called frequently.

        Returns:
            True if triggered, False otherwise
        """
        return self._stop_event.is_set()

    def reset(self):
        """
        Reset the kill switch for a new execution.

        Should be called before starting a new agent task.
        """
        self._stop_event.clear()
        self._triggered_at = None
        self._trigger_reason = None
        logger.debug("Kill switch reset")

    @property
    def triggered_at(self) -> Optional[datetime]:
        """Timestamp when kill switch was triggered."""
        return self._triggered_at

    @property
    def trigger_reason(self) -> Optional[str]:
        """Reason provided when kill switch was triggered."""
        return self._trigger_reason

    def get_status(self) -> dict:
        """
        Get kill switch status as dict.

        Returns:
            Dict with triggered, triggered_at, and reason fields
        """
        return {
            "triggered": self.is_triggered(),
            "triggered_at": self._triggered_at.isoformat() if self._triggered_at else None,
            "reason": self._trigger_reason,
        }
