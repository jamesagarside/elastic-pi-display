"""Data-source contract.

Every source is probed once at startup. A probe can fail in two ways:
  - `available=False`: the capability genuinely isn't there (404 on the API,
    missing tier-gated index, insufficient privileges). The source is skipped
    for the whole run and its tile hidden on the display.
  - transient error (network, 5xx): the source is still scheduled; fetches
    will retry and surface stale/pending states instead.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..client import ElasticClient, ElasticError

# Status codes that mean "this capability does not exist for this deployment
# or key" rather than "something went wrong right now".
UNAVAILABLE_STATUS_CODES = {403, 404}


@dataclass
class ProbeResult:
    available: bool
    detail: str = ""


class Source(ABC):
    name: str

    def __init__(self, client: ElasticClient, interval_seconds: int):
        self.client = client
        self.interval_seconds = interval_seconds

    async def probe(self) -> ProbeResult:
        try:
            await self.fetch()
        except ElasticError as e:
            if e.status_code in UNAVAILABLE_STATUS_CODES:
                return ProbeResult(available=False, detail=str(e))
            return ProbeResult(available=True, detail=f"transient: {e}")
        except Exception as e:  # network errors etc. — assume transient
            return ProbeResult(available=True, detail=f"transient: {e}")
        return ProbeResult(available=True, detail="ok")

    @abstractmethod
    async def fetch(self) -> Any:
        """Fetch and normalise the source's data. Raises on failure."""
