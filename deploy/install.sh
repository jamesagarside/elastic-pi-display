#!/usr/bin/env bash
# Install or update elastic-pi-display on a Raspberry Pi.
#
# Usage (as root on the Pi):
#   sudo bash install.sh                     # fetch + install the latest release
#   sudo bash install.sh --from-file X.tar.gz  # install an scp'd release tarball
#
# Re-running is safe: it updates /opt and the units but never touches an
# existing /etc/elastic-pi-display/config.toml.
set -euo pipefail

REPO="jamesagarside/elastic-pi-display"
INSTALL_DIR="/opt/elastic-pi-display"
CONFIG_DIR="/etc/elastic-pi-display"
SERVICE_USER="elastic-display"
# The desktop-session user that runs the Chromium kiosk.
KIOSK_USER="${KIOSK_USER:-${SUDO_USER:-pi}}"

log() { echo -e "\033[1;36m==>\033[0m $*"; }
die() { echo "error: $*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "run as root: sudo bash install.sh"

# --- 1. Locate release artifacts ---------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR=""
cleanup() { [ -n "${WORK_DIR}" ] && rm -rf "${WORK_DIR}"; }
trap cleanup EXIT

resolve_artifacts() {
  if [ "${1:-}" = "--from-file" ]; then
    [ -f "${2:-}" ] || die "--from-file: tarball not found: ${2:-}"
    WORK_DIR="$(mktemp -d)"
    tar -xzf "$2" -C "${WORK_DIR}" --strip-components=1
    ARTIFACT_DIR="${WORK_DIR}"
  elif [ -d "${SCRIPT_DIR}/../wheel" ] && [ -d "${SCRIPT_DIR}/../static" ]; then
    # Running from inside an extracted release tarball.
    ARTIFACT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
  else
    log "Downloading latest release of ${REPO}"
    WORK_DIR="$(mktemp -d)"
    local url
    url="$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" \
      | grep -o '"browser_download_url": *"[^"]*\.tar\.gz"' \
      | head -1 | cut -d'"' -f4)"
    [ -n "${url}" ] || die "no release tarball found — build one or use --from-file"
    curl -fsSL "${url}" -o "${WORK_DIR}/release.tar.gz"
    tar -xzf "${WORK_DIR}/release.tar.gz" -C "${WORK_DIR}" --strip-components=1
    ARTIFACT_DIR="${WORK_DIR}"
  fi
  [ -d "${ARTIFACT_DIR}/wheel" ] || die "release is missing wheel/"
  [ -d "${ARTIFACT_DIR}/static" ] || die "release is missing static/"
}
resolve_artifacts "$@"

# --- 2. System user and directories ------------------------------------------
if ! id "${SERVICE_USER}" >/dev/null 2>&1; then
  log "Creating system user ${SERVICE_USER}"
  useradd --system --home-dir "${INSTALL_DIR}" --shell /usr/sbin/nologin "${SERVICE_USER}"
fi
mkdir -p "${INSTALL_DIR}" "${CONFIG_DIR}"
chmod 0750 "${CONFIG_DIR}"
chown root:"${SERVICE_USER}" "${CONFIG_DIR}"

# --- 3. Python backend --------------------------------------------------------
log "Installing backend into ${INSTALL_DIR}/venv"
[ -d "${INSTALL_DIR}/venv" ] || python3 -m venv "${INSTALL_DIR}/venv"
"${INSTALL_DIR}/venv/bin/pip" install --quiet --upgrade "${ARTIFACT_DIR}"/wheel/*.whl
ln -sf "${INSTALL_DIR}/venv/bin/elastic-display" /usr/local/bin/elastic-display

# --- 4. Frontend + kiosk script ----------------------------------------------
log "Installing frontend bundle"
rm -rf "${INSTALL_DIR}/static"
cp -r "${ARTIFACT_DIR}/static" "${INSTALL_DIR}/static"
install -m 0755 "${ARTIFACT_DIR}/deploy/kiosk/kiosk.sh" "${INSTALL_DIR}/kiosk.sh"
chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}"

# --- 5. systemd units ---------------------------------------------------------
log "Installing systemd units"
install -m 0644 "${ARTIFACT_DIR}/deploy/systemd/elastic-pi-display.service" \
  /etc/systemd/system/elastic-pi-display.service

KIOSK_HOME="$(getent passwd "${KIOSK_USER}" | cut -d: -f6)"
[ -n "${KIOSK_HOME}" ] || die "kiosk user ${KIOSK_USER} does not exist (set KIOSK_USER=...)"
KIOSK_UNIT_DIR="${KIOSK_HOME}/.config/systemd/user"
mkdir -p "${KIOSK_UNIT_DIR}"
install -m 0644 "${ARTIFACT_DIR}/deploy/systemd/elastic-display-kiosk.service" \
  "${KIOSK_UNIT_DIR}/elastic-display-kiosk.service"
chown -R "${KIOSK_USER}:" "${KIOSK_HOME}/.config"
loginctl enable-linger "${KIOSK_USER}"

systemctl daemon-reload

# --- 6. Raspberry Pi display settings ----------------------------------------
if command -v raspi-config >/dev/null 2>&1; then
  log "Configuring desktop autologin and disabling screen blanking"
  raspi-config nonint do_boot_behaviour B4 || true
  raspi-config nonint do_blanking 1 || true
fi
for cmdline in /boot/firmware/cmdline.txt /boot/cmdline.txt; do
  if [ -f "${cmdline}" ] && ! grep -q "consoleblank=0" "${cmdline}"; then
    sed -i '1 s/$/ consoleblank=0/' "${cmdline}"
    break
  fi
done

# --- 7. Configuration ---------------------------------------------------------
if [ ! -f "${CONFIG_DIR}/config.toml" ]; then
  log "No config yet — running the setup wizard"
  ESD_CONFIG="${CONFIG_DIR}/config.toml" elastic-display setup
fi
if [ -f "${CONFIG_DIR}/config.toml" ]; then
  chown "${SERVICE_USER}:${SERVICE_USER}" "${CONFIG_DIR}/config.toml"
  chmod 0600 "${CONFIG_DIR}/config.toml"
fi

# --- 8. Start services --------------------------------------------------------
log "Enabling services"
systemctl enable --now elastic-pi-display.service
KIOSK_UID="$(id -u "${KIOSK_USER}")"
sudo -u "${KIOSK_USER}" XDG_RUNTIME_DIR="/run/user/${KIOSK_UID}" \
  systemctl --user enable elastic-display-kiosk.service 2>/dev/null \
  || log "Kiosk unit installed; it will start with the next graphical login"

log "Done. The display starts on the next boot of the desktop session."
log "Admin commands: elastic-display setup | elastic-display test"
log "Service logs:   journalctl -u elastic-pi-display -f"
