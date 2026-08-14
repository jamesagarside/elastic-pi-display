"""Attack Discovery findings via the public Kibana `_find` API.

`GET /api/attack_discovery/_find` is documented for both stack Kibana and
serverless security projects, but it is a recent API: older 8.x stacks only
have internal endpoints, which we never call. The startup probe handles this:
a 404/403 marks the source unavailable and the display hides the tile.
"""

from __future__ import annotations

from typing import Any

from .base import Source

MAX_DISCOVERIES = 5
SUMMARY_TRUNCATE = 400


class AttackDiscoverySource(Source):
    name = "attack_discovery"

    def __init__(self, client, interval_seconds: int, window: str):
        super().__init__(client, interval_seconds)
        self.window = window

    async def fetch(self) -> dict[str, Any]:
        result = await self.client.kbn_request(
            "GET",
            "/api/attack_discovery/_find",
            params={
                "page": 1,
                "per_page": MAX_DISCOVERIES,
                "sort_field": "@timestamp",
                "sort_order": "desc",
                "start": self.window,
                "end": "now",
            },
        )
        discoveries = [self._normalise(d) for d in result.get("data", [])]
        return {
            "total": result.get("total", len(discoveries)),
            "discoveries": discoveries,
            "window": self.window,
        }

    @staticmethod
    def _normalise(d: dict[str, Any]) -> dict[str, Any]:
        summary = d.get("summary_markdown") or ""
        if len(summary) > SUMMARY_TRUNCATE:
            summary = summary[: SUMMARY_TRUNCATE - 3] + "..."
        return {
            "id": d.get("id"),
            "title": d.get("title") or "Untitled discovery",
            "summary": summary,
            "timestamp": d.get("timestamp"),
            "alert_count": len(d.get("alert_ids") or []),
            "risk_score": d.get("risk_score"),
            "mitre_tactics": d.get("mitre_attack_tactics") or [],
            "workflow_status": d.get("alert_workflow_status"),
        }
