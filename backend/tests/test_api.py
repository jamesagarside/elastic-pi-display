import json

import pytest
import respx
from fastapi.testclient import TestClient

from esd.main import create_app
from esd.sse import EventBus

from conftest import ES_URL, KIBANA_URL

from urllib.parse import quote

ALERTS_SEARCH = f"{ES_URL}/.alerts-security.alerts-default/_search"
AD_FIND = f"{KIBANA_URL}/api/attack_discovery/_find"
RISK_SEARCH = f"{ES_URL}/risk-score.risk-score-latest-default/_search"
ENTITY_SEARCH = f"{ES_URL}/{quote('.entities.v2.latest.security_default-*', safe='')}/_search"
OBS_RESOLVE = f"{ES_URL}/_resolve/index/{quote('.alerts-observability.*', safe='')}"
SLO_FIND = f"{KIBANA_URL}/api/observability/slos"
METRICS_SEARCH = f"{ES_URL}/metrics-*/_search"
APM_SEARCH = f"{ES_URL}/{quote('traces-apm*', safe='')}/_search"


def mock_observability_unavailable(mock):
    """Default state for API tests: no observability capability anywhere."""
    mock.get(OBS_RESOLVE).respond(json={"indices": [], "aliases": [], "data_streams": []})
    mock.get(SLO_FIND).respond(status_code=404, json={"message": "Not Found"})
    mock.post(METRICS_SEARCH).respond(json={"hits": {"total": {"value": 0}}})
    mock.post(APM_SEARCH).respond(json={"hits": {"total": {"value": 0}}})


@pytest.fixture
def app_client(config, alerts_response, attack_discovery_response, risk_response):
    with respx.mock(assert_all_called=False) as mock:
        mock.post(ALERTS_SEARCH).respond(json=alerts_response)
        mock.get(AD_FIND).respond(json=attack_discovery_response)
        mock.post(RISK_SEARCH).respond(json=risk_response)
        mock_observability_unavailable(mock)
        # TestClient's context manager runs the lifespan (probes + first polls).
        with TestClient(create_app(config)) as client:
            yield client


def test_state_endpoint(app_client):
    snap = app_client.get("/api/state").json()
    assert snap["sources"]["alerts"]["data"]["counts"]["high"] == 5
    assert snap["sources"]["attack_discovery"]["data"]["total"] == 1
    assert snap["sources"]["risk_scores"]["data"]["entities"][0]["name"] == "host-1"
    assert snap["meta"]["elastic_reachable"] is True


def test_health_endpoint(app_client):
    health = app_client.get("/api/health").json()
    assert health["status"] == "ok"
    assert health["sources"]["alerts"] == "ok"


def test_unavailable_source_hidden_status(config, alerts_response, attack_discovery_response):
    with respx.mock(assert_all_called=False) as mock:
        mock.post(ALERTS_SEARCH).respond(json=alerts_response)
        mock.get(AD_FIND).respond(json=attack_discovery_response)
        mock.post(RISK_SEARCH).respond(status_code=404, json={"error": "no index"})
        mock.post(ENTITY_SEARCH).respond(status_code=404, json={"error": "no index"})
        mock_observability_unavailable(mock)
        with TestClient(create_app(config)) as client:
            snap = client.get("/api/state").json()
    assert snap["sources"]["risk_scores"]["status"] == "unavailable"
    assert snap["sources"]["alerts"]["status"] == "ok"


async def test_event_bus_stream_sends_initial_state():
    bus = EventBus()
    stream = bus.stream(initial={"hello": 1})
    frame = await anext(stream)
    assert frame.startswith("event: state\n")
    assert json.loads(frame.split("data: ", 1)[1].strip()) == {"hello": 1}
    await stream.aclose()
    assert bus.subscriber_count == 0


async def test_event_bus_publish_reaches_subscriber():
    bus = EventBus()
    stream = bus.stream(initial={"n": 0})
    await anext(stream)  # initial
    bus.publish({"n": 1})
    frame = await anext(stream)
    assert '"n": 1' in frame
    await stream.aclose()
