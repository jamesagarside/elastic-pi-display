"""Top entity risk scores from the risk engine's latest index.

The risk engine is tier-gated (Platinum / Security Complete) and off by
default, so a missing index is an expected, silent "unavailable" state.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from .base import Source

TOP_N = 5


class RiskScoresSource(Source):
    name = "risk_scores"

    def __init__(self, client, interval_seconds: int, index: str):
        super().__init__(client, interval_seconds)
        self.index = index

    async def fetch(self) -> dict[str, Any]:
        return {
            "hosts": await self._top("host"),
            "users": await self._top("user"),
        }

    async def _top(self, entity: str) -> list[dict[str, Any]]:
        score_field = f"{entity}.risk.calculated_score_norm"
        level_field = f"{entity}.risk.calculated_level"
        name_field = f"{entity}.name"
        body = {
            "size": TOP_N,
            "query": {"bool": {"filter": [{"exists": {"field": name_field}}]}},
            "sort": [{score_field: {"order": "desc"}}],
            "_source": [name_field, score_field, level_field],
        }
        result = await self.client.es_request(
            "POST", f"/{quote(self.index, safe='')}/_search", json=body
        )
        entities = []
        for hit in result.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            entity_obj = src.get(entity, {})
            risk = entity_obj.get("risk", {})
            entities.append(
                {
                    "name": entity_obj.get("name"),
                    "score": round(risk.get("calculated_score_norm") or 0),
                    "level": risk.get("calculated_level"),
                }
            )
        return entities
