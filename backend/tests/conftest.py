import pytest

from esd.config import Config, ElasticConfig

ES_URL = "https://test.es.example.com"
KIBANA_URL = "https://test.kb.example.com"


@pytest.fixture
def config() -> Config:
    return Config(
        elastic=ElasticConfig(
            deployment_type="cloud",
            es_url=ES_URL,
            kibana_url=KIBANA_URL,
            api_key="dGVzdDp0ZXN0",
            space="default",
        )
    )


def _recent_hits(*hits: dict) -> dict:
    return {"recent": {"hits": {"hits": [{"_source": h} for h in hits]}}}


@pytest.fixture
def alerts_response() -> dict:
    return {
        "hits": {"total": {"value": 17}},
        "aggregations": {
            "severity": {
                "buckets": [
                    {
                        "key": "critical",
                        "doc_count": 2,
                        **_recent_hits(
                            {
                                "kibana": {"alert": {"rule": {"name": "Malware Detection"}}},
                                "@timestamp": "2026-08-14T10:00:00Z",
                                "host": {"name": "host-1"},
                                "user": {"name": "alice"},
                            },
                            {
                                "kibana": {"alert": {"rule": {"name": "Ransomware Behavior"}}},
                                "@timestamp": "2026-08-14T09:30:00Z",
                            },
                        ),
                    },
                    {
                        "key": "high",
                        "doc_count": 5,
                        **_recent_hits(
                            {"@timestamp": "2026-08-14T08:00:00Z"},
                        ),
                    },
                    {"key": "low", "doc_count": 10},
                ]
            }
        },
    }


@pytest.fixture
def attack_discovery_response() -> dict:
    return {
        "total": 1,
        "data": [
            {
                "id": "abc-123",
                "title": "Credential access on host-1",
                "summary_markdown": "An attacker did a thing " * 40,
                "timestamp": "2026-08-14T09:00:00Z",
                "alert_ids": ["a", "b", "c"],
                "risk_score": 73,
                "mitre_attack_tactics": ["Credential Access"],
                "alert_workflow_status": "open",
            }
        ],
    }


@pytest.fixture
def risk_response() -> dict:
    return {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "host": {
                            "name": "host-1",
                            "risk": {"calculated_score_norm": 88.4, "calculated_level": "High"},
                        }
                    }
                }
            ]
        }
    }
