import httpx
import pytest
import respx

from esd.elastic.client import ElasticClient, ElasticError
from esd.elastic.sources import AlertsSource, AttackDiscoverySource, RiskScoresSource

from conftest import ES_URL, KIBANA_URL

ALERTS_SEARCH = f"{ES_URL}/.alerts-security.alerts-default/_search"
AD_FIND = f"{KIBANA_URL}/api/attack_discovery/_find"
RISK_SEARCH = f"{ES_URL}/risk-score.risk-score-latest-default/_search"


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
async def test_risk_scores(client, risk_response):
    respx.post(RISK_SEARCH).respond(json=risk_response)
    source = RiskScoresSource(client, 300, index="risk-score.risk-score-latest-default")
    data = await source.fetch()
    assert data["hosts"][0] == {"name": "host-1", "score": 88, "level": "High"}


@respx.mock
async def test_risk_probe_missing_index_unavailable(client):
    respx.post(RISK_SEARCH).respond(
        status_code=404, json={"error": {"type": "index_not_found_exception"}}
    )
    probe = await RiskScoresSource(client, 300, index="risk-score.risk-score-latest-default").probe()
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
