"""Server-sent-events bus: the poller publishes, browser clients subscribe."""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator

HEARTBEAT_SECONDS = 15
QUEUE_SIZE = 8


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def publish(self, snapshot: dict[str, Any]) -> None:
        for queue in self._subscribers:
            # A kiosk client that stops reading shouldn't block the poller:
            # drop the oldest snapshot, newest state always wins.
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(snapshot)

    async def stream(self, initial: dict[str, Any]) -> AsyncIterator[str]:
        """Yield SSE-formatted frames: full snapshot on connect, then updates
        as they are published. Heartbeats are real events (not SSE comments)
        because the browser EventSource API cannot observe comments, and the
        frontend's stale watchdog needs to see them."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=QUEUE_SIZE)
        self._subscribers.add(queue)
        try:
            yield _format_event("state", initial)
            while True:
                try:
                    snapshot = await asyncio.wait_for(
                        queue.get(), timeout=HEARTBEAT_SECONDS
                    )
                    yield _format_event("state", snapshot)
                except asyncio.TimeoutError:
                    yield _format_event("heartbeat", {"ts": None})
        finally:
            self._subscribers.discard(queue)


def _format_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
