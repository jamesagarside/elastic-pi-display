"""Active Observability alerts (log/metric/threshold/SLO rules).

Unlike security alerts these carry no severity, so the display shows the
active count and the most recent alerts by rule name. The alert indices are
only created when the first Observability rule runs, so "no indices" means
the capability is not in use and the tile hides.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from .base import ProbeResult, Source

INDEX = ".alerts-observability.*"
RECENT_N = 5


class ObservabilityAlertsSource(Source):
    name = "observability_alerts"

    async def probe(self) -> ProbeResult:
        # A wildcard search on absent indices succeeds with zero hits, so the
        # base fetch-probe cannot detect "never set up"; resolve instead.
        try:
            result = await self.client.es_request(
                "GET", f"/_resolve/index/{quote(INDEX, safe='')}"
            )
        except Exception as e:
            return ProbeResult(available=True, detail=f"transient: {e}")
        if not result.get("indices"):
            return ProbeResult(
                available=False,
                detail="no observability alert indices: no rules have run yet",
            )
        return await super().probe()

    async def fetch(self) -> dict[str, Any]:
        body = {
            "size": RECENT_N,
            "query": {"term": {"kibana.alert.status": "active"}},
            "sort": [{"kibana.alert.start": {"order": "desc"}}],
            "_source": [
                "kibana.alert.rule.name",
                "kibana.alert.rule.category",
                "kibana.alert.reason",
                "kibana.alert.start",
            ],
            "track_total_hits": True,
        }
        result = await self.client.es_request(
            "POST", f"/{quote(INDEX, safe='')}/_search", json=body
        )
        recent = []
        for hit in result.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            recent.append(
                {
                    "rule_name": src.get("kibana.alert.rule.name") or "Unnamed rule",
                    "category": src.get("kibana.alert.rule.category"),
                    "reason": (src.get("kibana.alert.reason") or "")[:200],
                    "started": src.get("kibana.alert.start"),
                }
            )
        return {
            "active": result.get("hits", {}).get("total", {}).get("value", 0),
            "recent": recent,
        }
