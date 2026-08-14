import stat

from esd.config import load_config
from esd.wizard import derive_kibana_url, write_config


def test_derive_kibana_url():
    assert (
        derive_kibana_url("https://abc123.es.eu-west-1.aws.cloud.es.io")
        == "https://abc123.kb.eu-west-1.aws.cloud.es.io"
    )
    assert derive_kibana_url("https://kibana.internal.example.com") == ""


def test_write_config_round_trip_and_permissions(tmp_path, config):
    path = tmp_path / "config.toml"
    write_config(config, path)
    mode = stat.S_IMODE(path.stat().st_mode)
    assert mode == 0o600
    loaded = load_config(path)
    assert loaded.elastic.es_url == config.elastic.es_url
    assert loaded.elastic.api_key == config.elastic.api_key


def test_write_config_atomic_overwrite(tmp_path, config):
    path = tmp_path / "config.toml"
    write_config(config, path)
    updated = config.model_copy(deep=True)
    updated.elastic.space = "soc"
    write_config(updated, path)
    assert load_config(path).elastic.space == "soc"
    # no stray temp files left behind
    assert [p.name for p in tmp_path.iterdir()] == ["config.toml"]
