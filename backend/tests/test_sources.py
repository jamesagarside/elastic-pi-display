from urllib.parse import quote

import httpx
import pytest
import respx

from esd.elastic.client import ElasticClient, ElasticError
from esd.elastic.sources import AlertsSource, AttackDiscoverySource, RiskScoresSource

from conftest import ES_URL, KIBANA_URL

ALERTS_SEARCH = f"{ES_URL}/.alerts-security.alerts-default/_search"
AD_FIND = f"{KIBANA_URL}/api/attack_discovery/_find"
RISK_INDEX = "risk-score.risk-score-latest-default"
ENTITY_INDEX = ".entities.v2.latest.security_default-*"
RISK_SEARCH = f"{ES_URL}/{RISK_INDEX}/_search"
ENTITY_SEARCH = f"{ES_URL}/{quote(ENTITY_INDEX, safe='')}/_search"


def risk_source(client):
    return RiskScoresSource(client, 300, index=RISK_INDEX, entity_index=ENTITY_INDEX)


@pytest.fixture
def client(config):
    return ElasticClient(config.elastic)


def alerts_source(client):
    return AlertsSource(client, 30, index=".alerts-security.alerts-default", window="now-24h")


@respx.mock
async def test_alerts_counts(client, alerts_response):
    route = respx.post(ALERTS_SEARCH).respond(json=alerts_response)
    data = await alerts_source(client).fetch()
    assert data["counts"] == {"critical": 2, "high": 5, "medium": 0, "low": 10}
    assert data["total_open"] == 17
    body = route.calls.last.request
    assert body.headers["authorization"].startswith("ApiKey ")


@respx.mock
async def test_alerts_recent_per_severity(client, alerts_response):
    respx.post(ALERTS_SEARCH).respond(json=alerts_response)
    data = await alerts_source(client).fetch()
    critical = data["recent"]["critical"]
    assert critical[0] == {
        "rule_name": "Malware Detection",
        "timestamp": "2026-08-14T10:00:00Z",
        "host": "host-1",
        "user": "alice",
    }
    # A hit without rule name or entities still renders something sensible.
    assert critical[1]["rule_name"] == "Ransomware Behavior"
    assert critical[1]["host"] is None
    assert data["recent"]["high"][0]["rule_name"] == "Unnamed rule"
    # Buckets with no top hits (or absent entirely) yield empty lists.
    assert data["recent"]["low"] == []
    assert data["recent"]["medium"] == []


@respx.mock
async def test_alerts_missing_aggregations(client):
    respx.post(ALERTS_SEARCH).respond(json={"hits": {"total": {"value": 0}}})
    data = await alerts_source(client).fetch()
    assert data["counts"] == {"critical": 0, "high": 0, "medium": 0, "low": 0}
    assert data["recent"] == {"critical": [], "high": [], "medium": [], "low": []}


@respx.mock
async def test_alerts_error_raises(client):
    respx.post(ALERTS_SEARCH).respond(status_code=500, json={"error": "boom"})
    with pytest.raises(ElasticError):
        await alerts_source(client).fetch()


@respx.mock
async def test_attack_discovery_normalises(client, attack_discovery_response):
    route = respx.get(AD_FIND).respond(json=attack_discovery_response)
    source = AttackDiscoverySource(client, 300, window="now-7d")
    data = await source.fetch()
    assert data["total"] == 1
    d = data["discoveries"][0]
    assert d["title"] == "Credential access on host-1"
    assert d["alert_count"] == 3
    assert d["mitre_tactics"] == ["Credential Access"]
    assert len(d["summary"]) <= 400
    request = route.calls.last.request
    assert request.headers["kbn-xsrf"] == "true"
    assert request.headers["authorization"].startswith("ApiKey ")


@respx.mock
async def test_attack_discovery_probe_404_unavailable(client):
    respx.get(AD_FIND).respond(status_code=404, json={"message": "Not Found"})
    probe = await AttackDiscoverySource(client, 300, window="now-7d").probe()
    assert probe.available is False


@respx.mock
async def test_probe_network_error_is_transient(client):
    respx.get(AD_FIND).mock(side_effect=httpx.ConnectError("no route"))
    probe = await AttackDiscoverySource(client, 300, window="now-7d").probe()
    assert probe.available is True
    assert "transient" in probe.detail


@respx.mock
async def test_risk_scores_legacy(client, risk_response):
    respx.post(RISK_SEARCH).respond(json=risk_response)
    data = await risk_source(client).fetch()
    assert data["entities"][0] == {
        "name": "host-1",
        "type": "Host",
        "score": 88,
        "level": "High",
    }
    # The legacy fixture only contains a host document; the user pass must
    # not fabricate an entry from it.
    assert len(data["entities"]) == 1


@respx.mock
async def test_risk_scores_entity_store_fallback(client, entity_store_response):
    respx.post(RISK_SEARCH).respond(
        status_code=404, json={"error": {"type": "index_not_found_exception"}}
    )
    entity_route = respx.post(ENTITY_SEARCH).respond(json=entity_store_response)
    source = risk_source(client)
    data = await source.fetch()
    assert entity_route.called
    assert data["entities"][0] == {
        "name": "unifi-udm",
        "type": "Service",
        "score": 35,
        "level": "Low",
    }
    assert data["entities"][1]["type"] == "Host"
    # The legacy index is not retried on later polls.
    data = await source.fetch()
    assert respx.calls.call_count == 3


@respx.mock
async def test_risk_probe_missing_both_indices_unavailable(client):
    respx.post(RISK_SEARCH).respond(
        status_code=404, json={"error": {"type": "index_not_found_exception"}}
    )
    respx.post(ENTITY_SEARCH).respond(
        status_code=404, json={"error": {"type": "index_not_found_exception"}}
    )
    probe = await risk_source(client).probe()
    assert probe.available is False


@respx.mock
async def test_kibana_space_prefix(config, attack_discovery_response):
    cfg = config.elastic.model_copy(update={"space": "soc"})
    client = ElasticClient(cfg)
    route = respx.get(f"{KIBANA_URL}/s/soc/api/attack_discovery/_find").respond(
        json=attack_discovery_response
    )
    await AttackDiscoverySource(client, 300, window="now-7d").fetch()
    assert route.called
