"""FastAPI app factory.

The static dir (built frontend) is resolved from, in order:
  1. ESD_STATIC_DIR environment variable
  2. /opt/elastic-pi-display/static  (Pi install)
  3. ../../frontend/dist relative to the repo (development)
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api import router
from .config import Config, load_config
from .elastic.client import ElasticClient
from .elastic.sources import (
    AlertsSource,
    ApmServicesSource,
    AttackDiscoverySource,
    HostsSource,
    ObservabilityAlertsSource,
    RiskScoresSource,
    SloSource,
)
from .poller import Poller
from .sse import EventBus
from .state import DisplayState

logger = logging.getLogger(__name__)

OPT_STATIC_DIR = Path("/opt/elastic-pi-display/static")
REPO_STATIC_DIR = Path(__file__).resolve().parents[3] / "frontend" / "dist"


def build_sources(cfg: Config, client: ElasticClient) -> list:
    return [
        AlertsSource(
            client,
            cfg.poll.alerts_seconds,
            index=cfg.alerts_index,
            window=cfg.data.alerts_window,
        ),
        AttackDiscoverySource(
            client,
            cfg.poll.attack_discovery_seconds,
            window=cfg.data.attack_discovery_window,
        ),
        RiskScoresSource(
            client,
            cfg.poll.risk_scores_seconds,
            index=cfg.risk_index,
            entity_index=cfg.entity_store_index,
        ),
        ObservabilityAlertsSource(client, cfg.poll.observability_alerts_seconds),
        SloSource(client, cfg.poll.slos_seconds),
        HostsSource(client, cfg.poll.hosts_seconds),
        ApmServicesSource(client, cfg.poll.apm_services_seconds),
    ]


def static_dir() -> Path | None:
    env = os.environ.get("ESD_STATIC_DIR")
    for candidate in ([Path(env)] if env else []) + [OPT_STATIC_DIR, REPO_STATIC_DIR]:
        if candidate.is_dir():
            return candidate
    return None


def create_app(cfg: Config | None = None) -> FastAPI:
    cfg = cfg or load_config()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client = ElasticClient(cfg.elastic)
        poller = Poller(build_sources(cfg, client), app.state.display, app.state.bus)
        await poller.start()
        try:
            yield
        finally:
            await poller.stop()
            await client.aclose()

    app = FastAPI(title="elastic-pi-display", version=__version__, lifespan=lifespan)
    app.state.config = cfg
    app.state.display = DisplayState(
        meta={
            "space": cfg.elastic.space,
            "deployment_type": cfg.elastic.deployment_type,
            "version": __version__,
            "poll_intervals": cfg.poll.model_dump(),
        }
    )
    app.state.bus = EventBus()
    app.include_router(router)

    static = static_dir()
    if static:
        app.mount("/", StaticFiles(directory=static, html=True), name="static")
    else:
        logger.warning("no frontend static dir found: serving API only")
    return app


def app() -> FastAPI:
    """Uvicorn factory entrypoint: `uvicorn esd.main:app --factory`."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    return create_app()
