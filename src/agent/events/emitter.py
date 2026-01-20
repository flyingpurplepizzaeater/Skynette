"""
Agent Event Emitter

Broadcasts agent events to async subscribers.
"""

import asyncio
from typing import AsyncIterator

from src.agent.models.event import AgentEvent


class AgentEventEmitter:
    """Broadcast agent events to async subscribers."""

    def __init__(self):
        self._subscribers: list[asyncio.Queue[AgentEvent]] = []

    async def emit(self, event: AgentEvent):
        """Emit event to all subscribers."""
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop event if subscriber is slow (bounded queue)
                pass

    def subscribe(self, maxsize: int = 100) -> "EventSubscription":
        """
        Create a subscription to events.
        Returns an EventSubscription that can be iterated.
        """
        queue: asyncio.Queue[AgentEvent] = asyncio.Queue(maxsize=maxsize)
        self._subscribers.append(queue)
        return EventSubscription(queue, self)

    def _unsubscribe(self, queue: asyncio.Queue):
        """Remove a subscriber queue."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)


class EventSubscription:
    """Async iterator for event subscription."""

    def __init__(self, queue: asyncio.Queue[AgentEvent], emitter: AgentEventEmitter):
        self._queue = queue
        self._emitter = emitter
        self._active = True

    def __aiter__(self) -> AsyncIterator[AgentEvent]:
        return self

    async def __anext__(self) -> AgentEvent:
        while self._active:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                if event.type in ("completed", "cancelled", "error"):
                    self._active = False
                return event
            except asyncio.TimeoutError:
                continue
        raise StopAsyncIteration

    def close(self):
        """Close the subscription."""
        self._active = False
        self._emitter._unsubscribe(self._queue)
