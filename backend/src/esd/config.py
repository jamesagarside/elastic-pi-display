"""Configuration loading and validation.

Resolution order for the config file path:
  1. ESD_CONFIG environment variable
  2. /etc/elastic-pi-display/config.toml   (service install)
  3. ~/.config/elastic-pi-display/config.toml  (development)
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

SYSTEM_CONFIG_PATH = Path("/etc/elastic-pi-display/config.toml")
USER_CONFIG_PATH = Path.home() / ".config" / "elastic-pi-display" / "config.toml"

DEPLOYMENT_TYPES = ("cloud", "self-managed", "serverless")


class ElasticConfig(BaseModel):
    deployment_type: str = "cloud"
    es_url: str
    kibana_url: str
    api_key: str
    space: str = "default"
    verify_tls: bool = True
    ca_cert: str = ""

    @field_validator("deployment_type")
    @classmethod
    def _valid_deployment_type(cls, v: str) -> str:
        if v not in DEPLOYMENT_TYPES:
            raise ValueError(f"deployment_type must be one of {DEPLOYMENT_TYPES}")
        return v

    @field_validator("es_url", "kibana_url")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class PollConfig(BaseModel):
    alerts_seconds: int = Field(default=30, ge=5)
    attack_discovery_seconds: int = Field(default=300, ge=30)
    risk_scores_seconds: int = Field(default=300, ge=30)
    observability_alerts_seconds: int = Field(default=60, ge=5)
    slos_seconds: int = Field(default=300, ge=30)
    hosts_seconds: int = Field(default=60, ge=15)
    apm_services_seconds: int = Field(default=120, ge=30)


class DataConfig(BaseModel):
    alerts_window: str = "now-24h"
    attack_discovery_window: str = "now-7d"
    # Dev/testing hook: the real alerts alias is system-managed, so tests and
    # local demos can point at a plain index of simulated alert documents.
    alerts_index_override: str = ""


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8080


class Config(BaseModel):
    elastic: ElasticConfig
    poll: PollConfig = PollConfig()
    data: DataConfig = DataConfig()
    server: ServerConfig = ServerConfig()

    @property
    def alerts_index(self) -> str:
        return self.data.alerts_index_override or f".alerts-security.alerts-{self.elastic.space}"

    @property
    def risk_index(self) -> str:
        return f"risk-score.risk-score-latest-{self.elastic.space}"

    @property
    def entity_store_index(self) -> str:
        # Entity Store V2 latest index (replaces the legacy risk engine
        # storage on newer stacks); the numeric suffix varies.
        return f".entities.v2.latest.security_{self.elastic.space}-*"


def config_path() -> Path:
    env = os.environ.get("ESD_CONFIG")
    if env:
        return Path(env)
    if SYSTEM_CONFIG_PATH.exists():
        return SYSTEM_CONFIG_PATH
    return USER_CONFIG_PATH


def load_config(path: Path | None = None) -> Config:
    path = path or config_path()
    if not path.exists():
        raise FileNotFoundError(
            f"No config found at {path}. Run `elastic-display setup` to create one."
        )
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return Config.model_validate(raw)
