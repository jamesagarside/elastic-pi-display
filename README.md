# elastic-pi-display

A Raspberry Pi desk display for Elastic Security. It sits on your desk and
shows, at a glance, how your security posture looks right now:

- **Open alerts by severity** — critical / high / medium / low counts, big
  enough to read from across the room
- **Attack Discovery** — the latest AI-generated attack discoveries
- **Entity risk scores** — the riskiest hosts and users (where the risk engine
  is enabled)

Built with Elastic's real [EUI](https://eui.elastic.co) component library
(Borealis theme) so it looks and feels like an extension of Elastic Security,
with full light and dark mode. Inspired by Simon's CLAUDE Inc display — this
one shows the state of your SIEM instead.

![Severity view on a 5-inch screen, dark mode](docs/screenshots/small-dark-severity.png)

| 5" screen, light mode, Attack Discovery view | Large screen, everything at once |
| --- | --- |
| ![](docs/screenshots/small-light-attack.png) | ![](docs/screenshots/large-dark-all.png) |

## How it works

```
┌───────────────────────────── Raspberry Pi ─────────────────────────────┐
│                                                                        │
│  Chromium (kiosk, systemd user unit)                                   │
│      │  SSE                                                            │
│  FastAPI backend (systemd service, 127.0.0.1:8080)                     │
│      │  polls with ApiKey auth                                         │
└──────┼─────────────────────────────────────────────────────────────────┘
       ▼
  Elasticsearch  ← alert counts, risk scores
  Kibana         ← Attack Discovery
```

A small Python service polls your deployment, caches the state, and pushes
updates to a prebuilt EUI web app over server-sent events. Chromium shows it
full screen. If Elastic becomes unreachable the display keeps the last known
data and says so.

## Works with any Elastic deployment

Elastic Cloud hosted, self-managed, and serverless security projects are all
supported — authentication is a single API key
([minimal privileges guide](docs/api-key-privileges.md)).

## Works on any Raspberry Pi and screen

Tested baseline is a Pi 3B with a 5-inch 800×480 touchscreen. The layout
adapts: small screens show one view at a time (tap to cycle), bigger screens
show more side by side. Touch is optional — without it the display just shows
the severity view.

- **Tap** — cycle views
- **Tap top-right corner** — toggle light/dark mode (persists)

## Install

On the Pi (Raspberry Pi OS with desktop), over SSH:

```bash
sudo bash install.sh                       # fetches the latest release
sudo bash install.sh --from-file <tarball> # air-gapped install
```

The installer sets up the service user, systemd units, kiosk autostart, and
runs an interactive setup wizard that live-tests your connection before
writing any config. Full walkthrough: [docs/setup.md](docs/setup.md).

Administration is all over SSH:

```bash
elastic-display setup   # (re)configure — deployment type, URLs, API key, space
elastic-display test    # probe each data source, show what's available
journalctl -u elastic-pi-display -f
```

## Creating the API key

An index-only read key covers the severity and risk tiles, but **Attack
Discovery is a Kibana API**, so the key also needs Kibana feature privileges.
Run this in **Kibana → Dev Tools** (change `default` in both places if your
alerts live in another space), then paste the `encoded` value into
`elastic-display setup`:

```json
POST /_security/api_key
{
  "name": "elastic-pi-display",
  "role_descriptors": {
    "elastic_pi_display_read": {
      "indices": [
        {
          "names": [
            ".alerts-security.alerts-default",
            "risk-score.risk-score-latest-default"
          ],
          "privileges": ["read", "view_index_metadata"]
        }
      ],
      "applications": [
        {
          "application": "kibana-.kibana",
          "privileges": [
            "feature_siemV3.read",
            "feature_securitySolutionAttackDiscovery.read",
            "feature_securitySolutionAssistant.read"
          ],
          "resources": ["space:default"]
        }
      ]
    }
  }
}
```

> **Using the API keys UI instead?** The form posts to a different (Kibana)
> endpoint with its own shape, so the full request above will be rejected with
> a `role_descriptors.indices: expected a plain object` validation error. In
> **Stack Management → API keys → Control security privileges**, paste only
> the inner object — everything from `"elastic_pi_display_read": { … }` —
> and set the name in the form field.

The Security feature IDs have changed across stack versions (`feature_siem` →
`feature_siemV2` → `feature_siemV3`). If `elastic-display test` reports Attack
Discovery as unavailable with a 403, list your version's IDs with
`GET kbn:/api/security/privileges` in Dev Tools and adjust — details and a
simpler UI-based alternative in
[docs/api-key-privileges.md](docs/api-key-privileges.md).

## Development

```bash
# backend
python3 -m venv .venv && .venv/bin/pip install -e "backend[dev]"
cd backend && ../.venv/bin/python -m pytest

# run backend against your deployment (config in ~/.config/elastic-pi-display/)
.venv/bin/elastic-display setup
.venv/bin/elastic-display run

# frontend, with /api proxied to the backend
cd frontend && npm install && npm run dev
```

Releases are built by GitHub Actions on version tags (`v*`): frontend bundle +
backend wheel + deploy scripts in one tarball, so the Pi never needs Node.js.

## Repository layout

| Path | What |
| --- | --- |
| `backend/` | FastAPI service, Elastic data sources, setup wizard CLI |
| `frontend/` | Vite + React + EUI (Borealis) kiosk app |
| `deploy/` | `install.sh`, systemd units, Chromium kiosk launcher |
| `docs/` | Setup guide, API key privilege guide |

## License

MIT
