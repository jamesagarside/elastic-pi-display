#!/usr/bin/env bash
# Launch Chromium in kiosk mode pointing at the local display backend.
# Works on Wayland (labwc, Pi OS Bookworm/Trixie default) and falls back to
# X11 for older installs. Tuned for low-RAM Pis (cache in tmpfs, no background
# services).
set -euo pipefail

URL="http://127.0.0.1:8080"

# Wait for the backend to come up before launching the browser, so the first
# thing on screen is the dashboard rather than a connection error.
for _ in $(seq 1 60); do
  if curl -fsS --max-time 2 "${URL}/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

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
