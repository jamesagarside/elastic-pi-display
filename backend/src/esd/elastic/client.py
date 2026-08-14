"""Thin httpx wrapper for Elasticsearch and Kibana REST calls.

Plain REST with `Authorization: ApiKey` is the one auth scheme that behaves
identically on Elastic Cloud hosted, self-managed, and serverless projects,
which is why this deliberately avoids the elasticsearch-py client.
"""

from __future__ import annotations

import ssl
from typing import Any

import httpx

from ..config import ElasticConfig

DEFAULT_TIMEOUT = httpx.Timeout(15.0, connect=10.0)


class ElasticError(Exception):
    """Non-2xx response from Elasticsearch or Kibana."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class ElasticClient:
    def __init__(self, cfg: ElasticConfig, client: httpx.AsyncClient | None = None):
        self._cfg = cfg
        if client is not None:
            self._client = client
        else:
            verify: ssl.SSLContext | bool = cfg.verify_tls
            if cfg.verify_tls and cfg.ca_cert:
                verify = ssl.create_default_context(cafile=cfg.ca_cert)
            self._client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, verify=verify)
        self._auth_header = {"Authorization": f"ApiKey {cfg.api_key}"}

    async def aclose(self) -> None:
        await self._client.aclose()

    async def es_request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        resp = await self._client.request(
            method,
            f"{self._cfg.es_url}{path}",
            json=json,
            headers=self._auth_header,
        )
        return self._handle(resp)

    async def kbn_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Space-aware Kibana routing: /s/<space>/api/... for non-default spaces.
        if self._cfg.space != "default":
            path = f"/s/{self._cfg.space}{path}"
        resp = await self._client.request(
            method,
            f"{self._cfg.kibana_url}{path}",
            params=params,
            json=json,
            headers={**self._auth_header, "kbn-xsrf": "true"},
        )
        return self._handle(resp)

    @staticmethod
    def _handle(resp: httpx.Response) -> dict[str, Any]:
        if resp.is_success:
            return resp.json()
        try:
            detail = resp.json()
            message = detail.get("message") or detail.get("error", resp.text)
        except Exception:
            message = resp.text
        raise ElasticError(resp.status_code, str(message)[:500])
