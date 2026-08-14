"""In-memory display state shared between the poller and the API."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SourceStatus(StrEnum):
    PENDING = "pending"          # no successful fetch yet
    OK = "ok"
    STALE = "stale"              # last data kept, but fetches keep failing
    UNAVAILABLE = "unavailable"  # probe failed (404/403/tier-gated): hide the tile


# A source flips OK -> STALE after this many consecutive fetch failures.
STALE_AFTER_FAILURES = 3


@dataclass
class SourceState:
    status: SourceStatus = SourceStatus.PENDING
    updated_at: float | None = None
    data: Any = None
    error: str | None = None
    consecutive_failures: int = 0

    def record_success(self, data: Any) -> None:
        self.status = SourceStatus.OK
        self.updated_at = time.time()
        self.data = data
        self.error = None
        self.consecutive_failures = 0

    def record_failure(self, error: str) -> None:
        self.consecutive_failures += 1
        self.error = error
        if self.status == SourceStatus.OK and self.consecutive_failures >= STALE_AFTER_FAILURES:
            self.status = SourceStatus.STALE
        elif self.status == SourceStatus.PENDING:
            # Never had data; stay pending so the UI shows a loading state.
            pass

    def mark_unavailable(self, reason: str) -> None:
        self.status = SourceStatus.UNAVAILABLE
        self.error = reason

    def snapshot(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "updated_at": self.updated_at,
            "data": self.data,
            "error": self.error,
        }


@dataclass
class DisplayState:
    sources: dict[str, SourceState] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    def source(self, name: str) -> SourceState:
        return self.sources.setdefault(name, SourceState())

    @property
    def elastic_reachable(self) -> bool:
        """False only when every non-unavailable source is failing."""
        active = [
            s for s in self.sources.values() if s.status != SourceStatus.UNAVAILABLE
        ]
        if not active:
            return False
        return any(s.consecutive_failures == 0 for s in active)

    def snapshot(self) -> dict[str, Any]:
        return {
            "sources": {name: s.snapshot() for name, s in self.sources.items()},
            "meta": {**self.meta, "elastic_reachable": self.elastic_reachable},
            "generated_at": time.time(),
        }
