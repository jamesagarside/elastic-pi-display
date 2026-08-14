"""Interactive setup wizard and connection tester, run over SSH.

`elastic-display setup` walks through deployment type, URLs, API key and
space, live-tests each data source, then writes the config atomically with
0600 permissions (it contains the API key).
"""

from __future__ import annotations

import asyncio
import getpass
import os
import shutil
import sys
import tempfile
from pathlib import Path

import tomli_w

from .config import (
    SYSTEM_CONFIG_PATH,
    USER_CONFIG_PATH,
    Config,
    DataConfig,
    ElasticConfig,
    PollConfig,
    ServerConfig,
)
from .elastic.client import ElasticClient
from .main import build_sources

DEPLOYMENT_CHOICES = {
    "1": ("cloud", "Elastic Cloud hosted deployment"),
    "2": ("self-managed", "Self-managed deployment"),
    "3": ("serverless", "Serverless security project"),
}


def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"  {label}{suffix}: ").strip()
    return value or default


def _prompt_required(label: str, default: str = "") -> str:
    while True:
        value = _prompt(label, default)
        if value:
            return value
        print("    A value is required.")


def derive_kibana_url(es_url: str) -> str:
    """Elastic Cloud endpoints pair `<id>.es.<region>...` with `<id>.kb.<region>...`."""
    if ".es." in es_url:
        return es_url.replace(".es.", ".kb.", 1)
    return ""


def run_setup() -> int:
    print("\nelastic-pi-display setup")
    print("=" * 40)

    print("\nDeployment type:")
    for key, (_, label) in DEPLOYMENT_CHOICES.items():
        print(f"  {key}) {label}")
    while True:
        choice = _prompt("Choose 1-3", "1")
        if choice in DEPLOYMENT_CHOICES:
            deployment_type = DEPLOYMENT_CHOICES[choice][0]
            break
        print("    Enter 1, 2 or 3.")

    print("\nEndpoints (find these in your deployment / project settings):")
    es_url = _prompt_required("Elasticsearch URL")
    kb_default = derive_kibana_url(es_url) if deployment_type == "cloud" else ""
    kibana_url = _prompt_required("Kibana URL", kb_default)

    print("\nAPI key (base64 'id:key' form, shown once when created in Kibana):")
    api_key = ""
    while not api_key:
        api_key = getpass.getpass("  API key: ").strip()

    space = _prompt("Kibana space", "default")

    verify_tls = True
    ca_cert = ""
    if deployment_type == "self-managed":
        verify_tls = _prompt("Verify TLS certificates? (y/n)", "y").lower() != "n"
        if verify_tls:
            ca_cert = _prompt("Path to custom CA certificate (blank for system CAs)")

    alerts_seconds = int(_prompt("Alert poll interval in seconds", "30"))

    cfg = Config(
        elastic=ElasticConfig(
            deployment_type=deployment_type,
            es_url=es_url,
            kibana_url=kibana_url,
            api_key=api_key,
            space=space,
            verify_tls=verify_tls,
            ca_cert=ca_cert,
        ),
        poll=PollConfig(alerts_seconds=alerts_seconds),
        data=DataConfig(),
        server=ServerConfig(),
    )

    print("\nTesting connection...")
    results = asyncio.run(probe_sources(cfg))
    print_capability_table(results)

    if not results.get("alerts", (False, ""))[0]:
        answer = _prompt("\nAlerts are unavailable: save this config anyway? (y/n)", "n")
        if answer.lower() != "y":
            print("Aborted; nothing written.")
            return 1

    path = write_config(cfg)
    print(f"\nConfig written to {path} (mode 0600).")
    print("Start or restart the service with:")
    print("  sudo systemctl restart elastic-pi-display")
    return 0


def run_test() -> int:
    from .config import load_config

    cfg = load_config()
    print("Testing connection...")
    results = asyncio.run(probe_sources(cfg))
    print_capability_table(results)
    return 0 if results.get("alerts", (False, ""))[0] else 1


async def probe_sources(cfg: Config) -> dict[str, tuple[bool, str]]:
    """Probe every source; returns {name: (available, detail)}."""
    client = ElasticClient(cfg.elastic)
    results: dict[str, tuple[bool, str]] = {}
    try:
        for source in build_sources(cfg, client):
            probe = await source.probe()
            transient = probe.detail.startswith("transient:")
            results[source.name] = (probe.available and not transient, probe.detail)
    finally:
        await client.aclose()
    return results


SOURCE_LABELS = {
    "alerts": "Security alerts",
    "attack_discovery": "Attack Discovery",
    "risk_scores": "Entity risk scores",
}


def print_capability_table(results: dict[str, tuple[bool, str]]) -> None:
    print()
    for name, (ok, detail) in results.items():
        label = SOURCE_LABELS.get(name, name)
        if ok:
            print(f"  OK {label:<20} available")
        else:
            reason = detail.splitlines()[0][:80] if detail else "no detail"
            print(f"   X {label:<20} unavailable ({reason})")
            if name != "alerts":
                print(f"     (the {label} tile will be hidden on the display)")


def default_config_path() -> Path:
    env = os.environ.get("ESD_CONFIG")
    if env:
        return Path(env)
    # Root (the installer) writes the system path; anyone else gets a user config.
    if os.geteuid() == 0 or os.access(SYSTEM_CONFIG_PATH.parent, os.W_OK):
        return SYSTEM_CONFIG_PATH
    return USER_CONFIG_PATH


SERVICE_USER = "elastic-display"


def write_config(cfg: Config, path: Path | None = None) -> Path:
    path = path or default_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = cfg.model_dump()
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".config-", suffix=".toml")
    try:
        with os.fdopen(fd, "wb") as f:
            tomli_w.dump(payload, f)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    # Written via sudo the file is root-owned, which the systemd service
    # (User=elastic-display) cannot read: hand it over when possible.
    if os.geteuid() == 0:
        try:
            shutil.chown(path, user=SERVICE_USER, group=SERVICE_USER)
        except (LookupError, OSError):
            pass  # dev machine without the service user
    return path


if __name__ == "__main__":
    sys.exit(run_setup())
