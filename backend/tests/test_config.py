import pytest

from esd.config import Config, load_config


def make_toml(tmp_path, body: str):
    path = tmp_path / "config.toml"
    path.write_text(body)
    return path


VALID = """
[elastic]
deployment_type = "serverless"
es_url = "https://proj.es.eu-west-1.aws.elastic.cloud/"
kibana_url = "https://proj.kb.eu-west-1.aws.elastic.cloud"
api_key = "secret"
space = "default"
"""


def test_load_valid_config(tmp_path):
    cfg = load_config(make_toml(tmp_path, VALID))
    assert cfg.elastic.deployment_type == "serverless"
    # trailing slash stripped
    assert cfg.elastic.es_url.endswith("elastic.cloud")
    assert cfg.poll.alerts_seconds == 30
    assert cfg.alerts_index == ".alerts-security.alerts-default"
    assert cfg.risk_index == "risk-score.risk-score-latest-default"


def test_missing_config_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="elastic-display setup"):
        load_config(tmp_path / "nope.toml")


def test_invalid_deployment_type(tmp_path):
    bad = VALID.replace("serverless", "on-prem")
    with pytest.raises(ValueError):
        load_config(make_toml(tmp_path, bad))


def test_invalid_url_rejected(tmp_path):
    bad = VALID.replace("https://proj.es.eu-west-1.aws.elastic.cloud/", "proj.example.com")
    with pytest.raises(ValueError):
        load_config(make_toml(tmp_path, bad))


def test_alerts_index_override(tmp_path):
    cfg = load_config(make_toml(tmp_path, VALID + '\n[data]\nalerts_index_override = "sim-alerts"\n'))
    assert cfg.alerts_index == "sim-alerts"


def test_space_in_index_names(config):
    cfg = Config(elastic=config.elastic.model_copy(update={"space": "soc"}))
    assert cfg.alerts_index == ".alerts-security.alerts-soc"
    assert cfg.risk_index == "risk-score.risk-score-latest-soc"
