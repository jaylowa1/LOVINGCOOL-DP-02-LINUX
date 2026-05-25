#!/usr/bin/env bash
set -euo pipefail

RULE_TEMPLATE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/deploy/99-lovingcool-dp36002.rules"
RULE_DST="/etc/udev/rules.d/99-lovingcool-dp36002.rules"
SERIAL_GROUP=""

read_os_release() {
  local key="$1"
  awk -F= -v wanted="$key" '$1 == wanted {gsub(/"/, "", $2); print tolower($2)}' /etc/os-release 2>/dev/null || true
}

detect_serial_group() {
  local distro_id distro_like
  distro_id="$(read_os_release ID)"
  distro_like="$(read_os_release ID_LIKE)"

  if [[ "${distro_id}" =~ ^(arch|cachyos|endeavouros|manjaro)$ ]] || [[ "${distro_like}" == *arch* ]]; then
    SERIAL_GROUP="uucp"
  elif [[ "${distro_id}" =~ ^(debian|ubuntu|linuxmint|pop)$ ]] || [[ "${distro_like}" == *debian* ]] || [[ "${distro_like}" == *ubuntu* ]]; then
    SERIAL_GROUP="dialout"
  elif getent group uucp >/dev/null 2>&1; then
    SERIAL_GROUP="uucp"
  elif getent group dialout >/dev/null 2>&1; then
    SERIAL_GROUP="dialout"
  else
    echo "Could not determine serial access group for this distro." >&2
    exit 1
  fi
}

if [[ ! -f "${RULE_TEMPLATE}" ]]; then
  echo "Rule file not found: ${RULE_TEMPLATE}" >&2
  exit 1
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "This installer must run as root."
  echo "Run: sudo ./scripts/install_udev_rule.sh"
  exit 1
fi

detect_serial_group
sed "s|__SERIAL_GROUP__|${SERIAL_GROUP}|g" "${RULE_TEMPLATE}" > "${RULE_DST}"
chmod 0644 "${RULE_DST}"
udevadm control --reload-rules
udevadm trigger

echo "Installed: ${RULE_DST}"
echo "Using group fallback: ${SERIAL_GROUP}"
echo "udev rules reloaded and triggered."
echo "If device is already plugged in, unplug/replug it."
