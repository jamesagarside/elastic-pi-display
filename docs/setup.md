# Setup guide

This walks through getting the display running on a Raspberry Pi, from a
blank Raspberry Pi OS image to a live dashboard. Everything is done over SSH.

## What you need

- Any Raspberry Pi (a Pi 3B is the tested baseline) running Raspberry Pi OS
  Lite or Desktop, with a screen attached.
- SSH access to the Pi.
- An Elastic deployment with Elastic Security in use. Any of:
  - Elastic Cloud hosted deployment
  - Self-managed deployment
  - Serverless security project
- An API key for that deployment (see
  [api-key-privileges.md](api-key-privileges.md)).

## 1. Gather your connection details

The display talks to two endpoints, both with the same API key:

| Deployment type | Elasticsearch URL | Kibana URL |
| --- | --- | --- |
| Elastic Cloud hosted | `https://<id>.es.<region>.<csp>.cloud.es.io` | Same host with `.kb.`; the wizard derives it for you |
| Self-managed | Wherever Elasticsearch listens (e.g. `https://es.internal:9200`) | Wherever Kibana listens (e.g. `https://kibana.internal:5601`) |
| Serverless project | Copy both from the project's Connection details panel | |

If your alerts live in a non-default Kibana space, note the space ID too.

## 2. Know your screen

How the display is driven depends on the panel type. Check before installing:

| Panel type | How to tell | What to do |
| --- | --- | --- |
| HDMI or official DSI touch display | HDMI cable or ribbon into the DISPLAY port | Nothing, works out of the box. See notes below if the panel stays blank. |
| DPI (parallel RGB over the GPIO pins) | Sits on the whole GPIO header, no HDMI in play | Add your vendor's DPI overlay to `/boot/firmware/config.txt` |
| SPI TFT (e.g. 3.5 inch ILI9486 resistive kits) | Sits on the GPIO header; the screen glows solid white until a driver loads | Add the panel overlay, then install with `--spi-panel` (details below) |

Notes for HDMI panels that stay blank: some panels never assert HDMI hotplug,
so the Pi does not drive them. Force the output by appending
`video=HDMI-A-1:<W>x<H>M@60D` to `/boot/firmware/cmdline.txt`. If the panel's
EDID advertises a preferred mode larger than its physical resolution, set
`KIOSK_MODE=<W>x<H>` in `/opt/elastic-pi-display/kiosk.env`; the kiosk then
runs a kanshi daemon to hold that mode.

Notes for SPI TFT panels: add the overlay for your panel to
`/boot/firmware/config.txt`, for example:

```
dtoverlay=piscreen,speed=18000000,rotate=270
```

Try `rotate=90` if the image comes up upside down. The `--spi-panel` install
flag switches the kiosk from Wayland to a minimal X11 server, because these
panels expose only a legacy framebuffer that Wayland compositors cannot draw
to. The panel's framebuffer device is detected automatically at each start.

## 3. Install on the Pi

```bash
ssh pi@<your-pi>
curl -fsSL https://raw.githubusercontent.com/jamesagarside/elastic-pi-display/main/deploy/install.sh -o install.sh
sudo bash install.sh              # add --spi-panel for SPI TFT screens
```

If the Pi has no internet access to GitHub, build or download the release
tarball elsewhere, copy it over with `scp`, and run:

```bash
sudo bash install.sh --from-file elastic-pi-display-<version>.tar.gz
```

The installer:

1. Creates a locked-down `elastic-display` system user.
2. Installs the backend into a virtualenv at `/opt/elastic-pi-display`.
3. Installs the prebuilt frontend (no Node.js needed on the Pi).
4. Installs two systemd units: the backend service and the Chromium kiosk.
5. Disables screen blanking, and on Desktop images enables autologin.
6. Runs the setup wizard if there is no config yet.

## 4. The setup wizard

```bash
sudo elastic-display setup
```

The wizard asks for deployment type, the two URLs, the API key, the space,
and the poll interval, then tests each data source live:

```
  OK Security alerts
  OK Attack Discovery
   X Entity risk scores    unavailable (index_not_found_exception)
     (the Entity risk scores tile will be hidden on the display)
```

Sources that are not available in your deployment (wrong licence tier,
feature not enabled, older stack version) are hidden on the display. Alerts
are the only required source.

Re-test connectivity any time with `elastic-display test`. To change
settings, re-run `sudo elastic-display setup`, then
`sudo systemctl restart elastic-pi-display`.

## 5. Reboot

```bash
sudo reboot
```

The Pi boots straight into the kiosk. The kiosk waits for the backend's
health check before starting Chromium, so the first thing on screen is the
dashboard.

## Using the display

- Tap the screen to cycle between views (severity, Attack Discovery, risk
  scores) on small screens. Larger screens show views side by side.
- Tap the top-right corner to toggle light and dark mode. The choice
  persists across reboots.
- The status bar shows a Live / Elastic unreachable / Display offline pill,
  the Kibana space, and when data was last updated. If Elastic becomes
  unreachable the display keeps showing the last known data, marked as such.

## Administration over SSH

```bash
elastic-display test                              # re-probe all data sources
journalctl -u elastic-pi-display -f               # backend logs
systemctl status elastic-pi-display-kiosk         # kiosk status
curl -s localhost:8080/api/health | python3 -m json.tool
```

## Updating

Re-run the installer. It replaces `/opt` but never touches your config:

```bash
sudo bash install.sh
```

## Screen size behaviour

The layout adapts to the screen resolution automatically:

| Screen | Behaviour |
| --- | --- |
| Under 1024 px wide (small panels) | One view at a time, tap to cycle |
| 1024 to 1599 px (around 10 inches) | Severity tiles pinned, second panel cycles |
| 1600 px and up (monitors, TVs) | Everything at once |

## Network requirements

The Pi needs outbound access to:

- Your Elasticsearch and Kibana URLs on port 443 (or your self-managed
  ports). This is the display's only permanent dependency.
- An NTP server on UDP 123, so the clock stays correct for TLS. Without it
  the clock drifts and connections to Elastic eventually fail.
- The apt mirrors and GitHub during installation only.

Everything else can be blocked. The display serves its own fonts, icons, and
UI from the Pi, so it needs no other outbound access at runtime.

## Troubleshooting

- **Blank or white screen after boot**: check the kiosk unit with
  `systemctl status elastic-pi-display-kiosk` and review the "Know your
  screen" section above. A solid white screen on a GPIO-mounted panel means
  the SPI panel driver is not loaded.
- **Display upside down**: change the `rotate` value in your panel's overlay
  line in `/boot/firmware/config.txt` and reboot.
- **"Display offline" pill**: the browser lost the backend. Check
  `systemctl status elastic-pi-display`.
- **"Elastic unreachable" pill**: the backend cannot reach your deployment.
  Run `elastic-display test` and check the network and API key. Also check
  the Pi's clock with `timedatectl`; a wrong clock breaks TLS.
- **Attack Discovery tile missing**: the find API needs a recent stack
  version and an API key with the Kibana privileges described in
  [api-key-privileges.md](api-key-privileges.md). On older stacks the tile
  hides itself by design.
- **Sluggish on a Pi 3**: enable zram swap with `sudo apt install zram-tools`,
  and use a proper 2.5 A power supply. Undervoltage (see `dmesg`) throttles
  the CPU and can destabilise WiFi.
