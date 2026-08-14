# Setup guide

This walks through getting the display running on a Raspberry Pi, from a blank
Raspberry Pi OS image to a live dashboard. Everything is done over SSH.

## What you need

- Any Raspberry Pi (a Pi 3B with 1GB RAM is the tested baseline) running
  Raspberry Pi OS **with desktop** (Bookworm or later), with a screen attached.
- SSH access to the Pi.
- An Elastic deployment with Elastic Security in use — any of:
  - Elastic Cloud hosted deployment
  - Self-managed deployment
  - Serverless security project
- An API key for that deployment (see
  [api-key-privileges.md](api-key-privileges.md)).

## 1. Gather your connection details

The display talks to two endpoints, both with the same API key:

| Deployment type | Elasticsearch URL | Kibana URL |
|---|---|---|
| Elastic Cloud hosted | `https://<id>.es.<region>.<csp>.cloud.es.io` | Same host with `.kb.` — the wizard derives it for you |
| Self-managed | Wherever Elasticsearch listens (e.g. `https://es.internal:9200`) | Wherever Kibana listens (e.g. `https://kibana.internal:5601`) |
| Serverless project | Copy both from the project's **Connection details** panel | |

If your alerts live in a non-default Kibana space, note the space ID too.

## 2. Install on the Pi

```bash
ssh pi@<your-pi>
curl -fsSLO https://github.com/jamesagarside/elastic-security-display/releases/latest/download/install.sh \
  || curl -fsSL https://raw.githubusercontent.com/jamesagarside/elastic-security-display/main/deploy/install.sh -o install.sh
sudo bash install.sh
```

If the Pi has no internet access to GitHub, build or download the release
tarball elsewhere, `scp` it over, and run:

```bash
sudo bash install.sh --from-file elastic-security-display-<version>.tar.gz
```

The installer:

1. Creates a locked-down `elastic-display` system user.
2. Installs the backend into a venv at `/opt/elastic-security-display`.
3. Installs the prebuilt frontend (no Node.js needed on the Pi).
4. Installs two systemd units — the backend service and the Chromium kiosk.
5. Enables desktop autologin and disables screen blanking.
6. Runs the setup wizard (below) if there's no config yet.

## 3. The setup wizard

```bash
elastic-display setup
```

The wizard asks for deployment type, the two URLs, the API key, the space, and
the poll interval, then live-tests each data source:

```
  ✔ Security alerts       OK
  ✔ Attack Discovery      OK
  ✘ Entity risk scores    unavailable — index_not_found_exception
    (the Entity risk scores tile will be hidden on the display)
```

Sources that aren't available in your deployment (wrong tier, feature not
enabled, older stack version) are simply hidden on the display — alerts are the
only required source.

Re-test connectivity any time with `elastic-display test`, and re-run
`elastic-display setup` to change settings, then
`sudo systemctl restart elastic-security-display`.

## 4. Reboot

```bash
sudo reboot
```

The Pi boots to the desktop, the kiosk service waits for the backend's health
check, and Chromium opens the dashboard full screen.

## Using the display

- **Tap** the screen to cycle between views (severity → Attack Discovery →
  risk scores) on small screens. Larger screens show views side by side.
- **Tap the top-right corner** to toggle light/dark mode. The choice persists
  across reboots.
- The status bar shows a **Live / Elastic unreachable / Display offline** pill,
  the Kibana space, and when data was last updated. If Elastic becomes
  unreachable the display keeps showing the last known data, marked as such.

## Administration over SSH

```bash
elastic-display test                                 # re-probe all data sources
journalctl -u elastic-security-display -f            # backend logs
systemctl --user status elastic-display-kiosk        # kiosk status (as the desktop user)
curl -s localhost:8080/api/health | python3 -m json.tool
```

## Updating

Re-run the installer — it replaces `/opt` but never touches your config:

```bash
sudo bash install.sh
```

## Screen size behaviour

The layout adapts to the screen resolution automatically:

| Screen | Behaviour |
|---|---|
| < 1024 px wide (5" 800×480 panels) | One view at a time, tap to cycle |
| 1024–1599 px (~10" screens) | Severity tiles pinned, second panel cycles |
| ≥ 1600 px (monitors/TVs) | Everything at once |

## Troubleshooting

- **Blank screen after boot** — check the kiosk unit as the desktop user:
  `systemctl --user status elastic-display-kiosk`. It only starts inside a
  graphical session; make sure desktop autologin is on
  (`sudo raspi-config nonint do_boot_behaviour B4`).
- **"Display offline" pill** — the browser lost the backend:
  `systemctl status elastic-security-display`.
- **"Elastic unreachable" pill** — the backend can't reach your deployment:
  `elastic-display test` and check network/API key.
- **Attack Discovery tile missing** — the `_find` API needs a recent stack
  version and an API key with security read privileges; on older stacks the
  tile hides itself by design.
- **Sluggish on a Pi 3** — enable zram swap: `sudo apt install zram-tools`.
