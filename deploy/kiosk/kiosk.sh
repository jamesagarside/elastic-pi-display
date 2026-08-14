#!/usr/bin/env bash
# Launch Chromium in kiosk mode pointing at the local display backend.
# Works on Wayland (labwc, Pi OS Bookworm/Trixie default) and falls back to
# X11 for older installs. Tuned for low-RAM Pis (cache in tmpfs, no background
# services).
set -euo pipefail

URL="http://127.0.0.1:8080"

# Wait for the backend to come up before launching the browser, so the first
# thing on screen is the dashboard rather than a connection error. If it never
# comes up (e.g. not configured yet), exit and let systemd retry us.
HEALTHY=0
for _ in $(seq 1 60); do
  if curl -fsS --max-time 2 "${URL}/api/health" >/dev/null 2>&1; then
    HEALTHY=1
    break
  fi
  sleep 2
done
if [ "${HEALTHY}" -ne 1 ]; then
  echo "backend not healthy at ${URL}: giving up for now" >&2
  exit 1
fi

# Optional overrides, e.g. panels whose EDID prefers a mode the physical
# resolution can't match: set KIOSK_OUTPUT and KIOSK_MODE here. Lives in
# /opt (not /etc/elastic-pi-display) because the kiosk user has no access to
# the config dir, which holds the API key.
#   echo 'KIOSK_OUTPUT=HDMI-A-1'  >  /opt/elastic-pi-display/kiosk.env
#   echo 'KIOSK_MODE=800x480'     >> /opt/elastic-pi-display/kiosk.env
if [ -f /opt/elastic-pi-display/kiosk.env ]; then
  # shellcheck disable=SC1091
  . /opt/elastic-pi-display/kiosk.env
fi

# One-shot mode sets get reverted whenever the compositor reconfigures, so a
# kanshi daemon continuously enforces the requested mode instead. It lives in
# this unit's cgroup and dies with it.
if [ -n "${KIOSK_MODE:-}" ] && command -v kanshi >/dev/null 2>&1; then
  KANSHI_CONF="$(mktemp)"
  printf 'profile {\n  output "%s" mode %s\n}\n' \
    "${KIOSK_OUTPUT:-HDMI-A-1}" "${KIOSK_MODE}" > "${KANSHI_CONF}"
  kanshi -c "${KANSHI_CONF}" &
fi
# Pi OS ships the browser as either `chromium-browser` or `chromium`.
CHROMIUM="$(command -v chromium-browser || command -v chromium)"

FLAGS=(
  --kiosk "${URL}"
  --noerrdialogs
  --disable-infobars
  --no-first-run
  --password-store=basic
  --disable-pinch
  --overscroll-history-navigation=0
  --disable-extensions
  --disable-component-update
  --disable-background-networking
  --disable-features=Translate
  --check-for-update-interval=31536000
  --disk-cache-dir=/dev/shm/chromium-cache
  --disk-cache-size=33554432
)

if [ -n "${WAYLAND_DISPLAY:-}" ]; then
  FLAGS+=(--ozone-platform=wayland)
fi

exec "${CHROMIUM}" "${FLAGS[@]}"
