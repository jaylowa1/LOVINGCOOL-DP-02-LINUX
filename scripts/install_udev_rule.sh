#!/usr/bin/env bash
set -euo pipefail

RULE_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/deploy/99-lovingcool-dp36002.rules"
RULE_DST="/etc/udev/rules.d/99-lovingcool-dp36002.rules"

if [[ ! -f "${RULE_SRC}" ]]; then
  echo "Rule file not found: ${RULE_SRC}" >&2
  exit 1
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "This installer must run as root."
  echo "Run: sudo ./scripts/install_udev_rule.sh"
  exit 1
fi

install -m 0644 "${RULE_SRC}" "${RULE_DST}"
udevadm control --reload-rules
udevadm trigger

echo "Installed: ${RULE_DST}"
echo "udev rules reloaded and triggered."
echo "If device is already plugged in, unplug/replug it."
echo "Verify with: ls -l /dev/ttyACM*"
