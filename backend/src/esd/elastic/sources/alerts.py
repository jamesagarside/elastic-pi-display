"""Open security alert counts per severity.

Queries the `.alerts-security.alerts-<space>` alias directly via the
Elasticsearch search API: this works identically on Cloud hosted,
self-managed, and serverless deployments with an API key that has `read`
on the alias.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from ..client import ElasticClient
from .base import Source

SEVERITIES = ("critical", "high", "medium", "low")

# How many recent alerts to carry per severity for the tile drill-down.
RECENT_PER_SEVERITY = 5


def _dig(source: dict[str, Any], *path: str) -> Any:
    """Walk a nested _source dict; returns None if any level is missing."""
    node: Any = source
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


class AlertsSource(Source):
    name = "alerts"

    def __init__(
        self,
        client: ElasticClient,
        interval_seconds: int,
        index: str,
        window: str,
    ):
        super().__init__(client, interval_seconds)
        self.index = index
        self.window = window

    async def fetch(self) -> dict[str, Any]:
        body = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"kibana.alert.workflow_status": "open"}},
                        {"range": {"@timestamp": {"gte": self.window}}},
                    ]
                }
            },
            "aggs": {
                "severity": {
                    "terms": {"field": "kibana.alert.severity", "size": 10},
                    "aggs": {
                        "recent": {
                            "top_hits": {
                                "size": RECENT_PER_SEVERITY,
                                "sort": [{"@timestamp": {"order": "desc"}}],
                                "_source": [
                                    "kibana.alert.rule.name",
                                    "@timestamp",
                                    "host.name",
                                    "user.name",
                                ],
                            }
                        }
                    },
                }
            },
        }
        result = await self.client.es_request(
            "POST", f"/{quote(self.index, safe='')}/_search", json=body
        )
        buckets = (
            result.get("aggregations", {}).get("severity", {}).get("buckets", [])
        )
        counts = {sev: 0 for sev in SEVERITIES}
        recent: dict[str, list[dict[str, Any]]] = {sev: [] for sev in SEVERITIES}
        for bucket in buckets:
            key = str(bucket.get("key", "")).lower()
            if key not in counts:
                continue
            counts[key] = bucket.get("doc_count", 0)
            hits = bucket.get("recent", {}).get("hits", {}).get("hits", [])
            for hit in hits:
                src = hit.get("_source", {})
                recent[key].append(
                    {
                        "rule_name": _dig(src, "kibana", "alert", "rule", "name")
                        or "Unnamed rule",
                        "timestamp": src.get("@timestamp"),
                        "host": _dig(src, "host", "name"),
                        "user": _dig(src, "user", "name"),
                    }
                )
        total = result.get("hits", {}).get("total", {})
        return {
            "counts": counts,
            "recent": recent,
            "total_open": total.get("value", sum(counts.values())),
            "window": self.window,
        }
