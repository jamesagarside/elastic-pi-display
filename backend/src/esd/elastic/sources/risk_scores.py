"""Top entity risk scores.

Two generations of storage, probed in order:
  - Legacy risk engine: `risk-score.risk-score-latest-<space>` with per-type
    `host.risk` / `user.risk` documents.
  - Entity Store V2 (which replaces the legacy engine on newer stacks): one
    `.entities.v2.latest.security_<space>-*` index where every document is an
    entity of any type (Host, User, Service, ...) carrying `entity.risk`.

Both are tier-gated (Platinum / Security Complete) and off by default, so a
missing index in both generations is an expected, silent "unavailable" state.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from ..client import ElasticError
from .base import Source

TOP_N = 8

# Legacy documents only ever describe these entity types.
LEGACY_TYPES = {"host": "Host", "user": "User"}


class RiskScoresSource(Source):
    name = "risk_scores"

    def __init__(self, client, interval_seconds: int, index: str, entity_index: str):
        super().__init__(client, interval_seconds)
        self.index = index
        self.entity_index = entity_index
        # Set after the first successful generation probe; a legacy 403/404 is
        # permanent for the process, so don't re-try it every poll.
        self._mode: str | None = None

    async def fetch(self) -> dict[str, Any]:
        if self._mode != "entity_store":
            try:
                data = await self._fetch_legacy()
                self._mode = "legacy"
                return data
            except ElasticError as e:
                if e.status_code not in (403, 404):
                    raise
                self._mode = "entity_store"
        return await self._fetch_entity_store()

    async def _search(self, index: str, body: dict[str, Any]) -> dict[str, Any]:
        return await self.client.es_request(
            "POST", f"/{quote(index, safe='')}/_search", json=body
        )

    async def _fetch_legacy(self) -> dict[str, Any]:
        entities: list[dict[str, Any]] = []
        for field, type_label in LEGACY_TYPES.items():
            result = await self._search(
                self.index,
                {
                    "size": TOP_N,
                    "query": {
                        "bool": {"filter": [{"exists": {"field": f"{field}.name"}}]}
                    },
                    "sort": [{f"{field}.risk.calculated_score_norm": {"order": "desc"}}],
                    "_source": [
                        f"{field}.name",
                        f"{field}.risk.calculated_score_norm",
                        f"{field}.risk.calculated_level",
                    ],
                },
            )
            for hit in result.get("hits", {}).get("hits", []):
                entity_obj = hit.get("_source", {}).get(field, {})
                if not entity_obj.get("name"):
                    continue
                risk = entity_obj.get("risk", {})
                entities.append(
                    {
                        "name": entity_obj.get("name"),
                        "type": type_label,
                        "score": round(risk.get("calculated_score_norm") or 0),
                        "level": risk.get("calculated_level"),
                    }
                )
        entities.sort(key=lambda e: e["score"], reverse=True)
        return {"entities": entities[:TOP_N]}

    async def _fetch_entity_store(self) -> dict[str, Any]:
        result = await self._search(
            self.entity_index,
            {
                "size": TOP_N,
                "query": {
                    "bool": {
                        "filter": [
                            {"exists": {"field": "entity.name"}},
                            {"exists": {"field": "entity.risk.calculated_score_norm"}},
                        ]
                    }
                },
                "sort": [{"entity.risk.calculated_score_norm": {"order": "desc"}}],
                "_source": [
                    "entity.name",
                    "entity.type",
                    "entity.risk.calculated_score_norm",
                    "entity.risk.calculated_level",
                ],
            },
        )
        entities = []
        for hit in result.get("hits", {}).get("hits", []):
            entity_obj = hit.get("_source", {}).get("entity", {})
            if not entity_obj.get("name"):
                continue
            risk = entity_obj.get("risk", {})
            entities.append(
                {
                    "name": entity_obj.get("name"),
                    "type": entity_obj.get("type"),
                    "score": round(risk.get("calculated_score_norm") or 0),
                    "level": risk.get("calculated_level"),
                }
            )
        return {"entities": entities}
