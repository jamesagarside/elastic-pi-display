"""APM service health aggregated from trace documents.

Aggregates transactions by service: throughput, failure rate, and average
latency over the lookback window. Probes unavailable when no service has
ever reported a transaction (nothing instrumented), so the tile only shows
on deployments that actually use APM/OTel tracing.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from .base import ProbeResult, Source

INDEX = "traces-apm*"
WINDOW = "now-15m"
TOP_SERVICES = 8


class ApmServicesSource(Source):
    name = "apm_services"

    async def probe(self) -> ProbeResult:
        try:
            result = await self.client.es_request(
                "POST",
                f"/{quote(INDEX, safe='')}/_search",
                json={
                    "size": 0,
                    "query": {"exists": {"field": "service.name"}},
                    "terminate_after": 1,
                },
            )
        except Exception as e:
            return ProbeResult(available=True, detail=f"transient: {e}")
        if not result.get("hits", {}).get("total", {}).get("value"):
            return ProbeResult(available=False, detail="no APM trace data")
        return await super().probe()

    async def fetch(self) -> dict[str, Any]:
        body = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {"range": {"@timestamp": {"gte": WINDOW}}},
                        {"term": {"processor.event": "transaction"}},
                    ]
                }
            },
            "aggs": {
                "services": {
                    "terms": {"field": "service.name", "size": TOP_SERVICES},
                    "aggs": {
                        "latency_us": {"avg": {"field": "transaction.duration.us"}},
                        "failures": {
                            "filter": {"term": {"event.outcome": "failure"}}
                        },
                    },
                }
            },
        }
        result = await self.client.es_request(
            "POST", f"/{quote(INDEX, safe='')}/_search", json=body
        )
        services = []
        for bucket in result.get("aggregations", {}).get("services", {}).get("buckets", []):
            count = bucket.get("doc_count", 0)
            failures = bucket.get("failures", {}).get("doc_count", 0)
            latency = bucket.get("latency_us", {}).get("value")
            services.append(
                {
                    "name": bucket.get("key"),
                    "transactions": count,
                    "error_rate_pct": round(100 * failures / count, 1) if count else 0.0,
                    "latency_ms": round(latency / 1000, 1) if latency else None,
                }
            )
        services.sort(key=lambda s: s["error_rate_pct"], reverse=True)
        return {"services": services, "window": WINDOW}
