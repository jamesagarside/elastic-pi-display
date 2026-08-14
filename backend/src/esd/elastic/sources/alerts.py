"""Open security alert counts per severity.

Queries the `.alerts-security.alerts-<space>` alias directly via the
Elasticsearch search API — this works identically on Cloud hosted,
self-managed, and serverless deployments with an API key that has `read`
on the alias.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from ..client import ElasticClient
from .base import Source

SEVERITIES = ("critical", "high", "medium", "low")


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
                    "terms": {"field": "kibana.alert.severity", "size": 10}
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
        for bucket in buckets:
            key = str(bucket.get("key", "")).lower()
            if key in counts:
                counts[key] = bucket.get("doc_count", 0)
        total = result.get("hits", {}).get("total", {})
        return {
            "counts": counts,
            "total_open": total.get("value", sum(counts.values())),
            "window": self.window,
        }
