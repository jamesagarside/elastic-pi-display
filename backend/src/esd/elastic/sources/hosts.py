"""Infrastructure host CPU and memory from metrics data.

Supports both metric dialects in one aggregation and uses whichever a host
actually reports:
  - OTel hostmetrics: per-state fractions in `system.cpu.utilization`
    (cpu% = 1 - idle) and `system.memory.utilization` (state "used").
  - Elastic system integration: `system.cpu.total.norm.pct` and
    `system.memory.actual.used.pct`.

Probes unavailable when no host has reported either dialect at all; a host
that merely went quiet recently still shows (values from the lookback
window, empty list if nothing reported in it).
"""

from __future__ import annotations

from typing import Any

from .base import ProbeResult, Source

INDEX = "metrics-*"
WINDOW = "now-10m"
TOP_HOSTS = 12


def _agg_value(bucket: dict[str, Any], *path: str) -> float | None:
    node: Any = bucket
    for key in path:
        node = node.get(key, {}) if isinstance(node, dict) else {}
    return node if isinstance(node, (int, float)) else None


class HostsSource(Source):
    name = "hosts"

    async def probe(self) -> ProbeResult:
        try:
            result = await self.client.es_request(
                "POST",
                f"/{INDEX}/_search",
                json={
                    "size": 0,
                    "query": {
                        "bool": {
                            "should": [
                                {"exists": {"field": "system.cpu.utilization"}},
                                {"exists": {"field": "system.cpu.total.norm.pct"}},
                            ],
                            "minimum_should_match": 1,
                        }
                    },
                    "terminate_after": 1,
                },
            )
        except Exception as e:
            return ProbeResult(available=True, detail=f"transient: {e}")
        if not result.get("hits", {}).get("total", {}).get("value"):
            return ProbeResult(available=False, detail="no host metrics data")
        return await super().probe()

    async def fetch(self) -> dict[str, Any]:
        body = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [{"range": {"@timestamp": {"gte": WINDOW}}}],
                    "should": [
                        {"exists": {"field": "system.cpu.utilization"}},
                        {"exists": {"field": "system.memory.utilization"}},
                        {"exists": {"field": "system.cpu.total.norm.pct"}},
                        {"exists": {"field": "system.memory.actual.used.pct"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "aggs": {
                "hosts": {
                    "terms": {"field": "host.name", "size": TOP_HOSTS},
                    "aggs": {
                        "cpu_idle_otel": {
                            "filter": {"term": {"attributes.state": "idle"}},
                            "aggs": {"v": {"avg": {"field": "system.cpu.utilization"}}},
                        },
                        "mem_used_otel": {
                            "filter": {"term": {"attributes.state": "used"}},
                            "aggs": {"v": {"avg": {"field": "system.memory.utilization"}}},
                        },
                        "cpu_elastic": {"avg": {"field": "system.cpu.total.norm.pct"}},
                        "mem_elastic": {"avg": {"field": "system.memory.actual.used.pct"}},
                    },
                }
            },
        }
        result = await self.client.es_request("POST", f"/{INDEX}/_search", json=body)
        hosts = []
        buckets = result.get("aggregations", {}).get("hosts", {}).get("buckets", [])
        for bucket in buckets:
            idle = _agg_value(bucket, "cpu_idle_otel", "v", "value")
            cpu = 1 - idle if idle is not None else _agg_value(bucket, "cpu_elastic", "value")
            mem = _agg_value(bucket, "mem_used_otel", "v", "value")
            if mem is None:
                mem = _agg_value(bucket, "mem_elastic", "value")
            if cpu is None and mem is None:
                continue
            hosts.append(
                {
                    "name": bucket.get("key"),
                    "cpu_pct": round(cpu * 100) if cpu is not None else None,
                    "memory_pct": round(mem * 100) if mem is not None else None,
                }
            )
        hosts.sort(key=lambda h: h["cpu_pct"] or 0, reverse=True)
        return {"hosts": hosts, "window": WINDOW}
