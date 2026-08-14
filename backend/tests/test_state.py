from esd.state import DisplayState, SourceState, SourceStatus


def test_success_resets_failures():
    s = SourceState()
    s.record_failure("x")
    s.record_success({"n": 1})
    assert s.status == SourceStatus.OK
    assert s.consecutive_failures == 0
    assert s.data == {"n": 1}


def test_stale_after_three_failures_keeps_data():
    s = SourceState()
    s.record_success({"n": 1})
    for _ in range(2):
        s.record_failure("boom")
    assert s.status == SourceStatus.OK
    s.record_failure("boom")
    assert s.status == SourceStatus.STALE
    assert s.data == {"n": 1}


def test_pending_stays_pending_on_failure():
    s = SourceState()
    for _ in range(5):
        s.record_failure("boom")
    assert s.status == SourceStatus.PENDING


def test_unavailable():
    s = SourceState()
    s.mark_unavailable("404")
    assert s.status == SourceStatus.UNAVAILABLE
    assert s.snapshot()["error"] == "404"


def test_elastic_reachable():
    d = DisplayState()
    d.source("alerts").record_success({})
    d.source("risk").mark_unavailable("404")
    assert d.elastic_reachable is True
    d.source("alerts").record_failure("net down")
    assert d.elastic_reachable is False


def test_snapshot_shape():
    d = DisplayState(meta={"space": "default"})
    d.source("alerts").record_success({"counts": {}})
    snap = d.snapshot()
    assert snap["sources"]["alerts"]["status"] == "ok"
    assert snap["meta"]["space"] == "default"
    assert "elastic_reachable" in snap["meta"]
    assert "generated_at" in snap
