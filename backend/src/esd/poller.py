"""Per-source polling loops."""

from __future__ import annotations

import asyncio
import logging

from .elastic.sources.base import Source
from .sse import EventBus
from .state import DisplayState

logger = logging.getLogger(__name__)


class Poller:
    def __init__(self, sources: list[Source], state: DisplayState, bus: EventBus):
        self.sources = sources
        self.state = state
        self.bus = bus
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Probe each source once, then start a polling loop for the available
        ones. Unavailable sources (missing API/tier/privilege) are recorded so
        the frontend can hide their tiles."""
        results = await asyncio.gather(*(s.probe() for s in self.sources))
        for source, probe in zip(self.sources, results):
            source_state = self.state.source(source.name)
            if not probe.available:
                logger.warning("source %s unavailable: %s", source.name, probe.detail)
                source_state.mark_unavailable(probe.detail)
                continue
            self._tasks.append(
                asyncio.create_task(self._loop(source), name=f"poll-{source.name}")
            )
        self.bus.publish(self.state.snapshot())

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _loop(self, source: Source) -> None:
        source_state = self.state.source(source.name)
        while True:
            try:
                data = await source.fetch()
                source_state.record_success(data)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning("source %s fetch failed: %s", source.name, e)
                source_state.record_failure(str(e))
            self.bus.publish(self.state.snapshot())
            await asyncio.sleep(source.interval_seconds)
