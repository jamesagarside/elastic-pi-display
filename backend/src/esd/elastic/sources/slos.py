"""SLO health via the Kibana SLO API.

Probes unavailable when the API is absent (404 on older stacks or when the
plugin is not served) and also when no SLOs are defined, so the tile only
shows once there is something to display. Create your first SLO, then
restart the backend to pick it up.
"""

from __future__ import annotations

from typing import Any

from .base import ProbeResult, Source

PER_PAGE = 25


class SloSource(Source):
    name = "slos"

    async def probe(self) -> ProbeResult:
        result = await super().probe()
        if not result.available:
            return result
        if result.detail.startswith("transient"):
            return result
        data = await self.fetch()
        if data["total"] == 0:
            return ProbeResult(available=False, detail="no SLOs defined")
        return result

    async def fetch(self) -> dict[str, Any]:
        result = await self.client.kbn_request(
            "GET",
            "/api/observability/slos",
            params={"page": 1, "perPage": PER_PAGE},
        )
        slos = []
        for slo in result.get("results", []):
            summary = slo.get("summary", {})
            budget = summary.get("errorBudget", {})
            slos.append(
                {
                    "name": slo.get("name"),
                    "status": summary.get("status"),
                    "sli": summary.get("sliValue"),
                    "target": slo.get("objective", {}).get("target"),
                    "budget_remaining": budget.get("remaining"),
                }
            )
        # Violated and degraded SLOs first, then by name for a stable order.
        rank = {"VIOLATED": 0, "DEGRADING": 1, "NO_DATA": 2, "HEALTHY": 3}
        slos.sort(key=lambda s: (rank.get(s["status"], 2), s["name"] or ""))
        return {"total": result.get("total", len(slos)), "slos": slos}
