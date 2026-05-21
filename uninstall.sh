#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="${HOME}/.local/share/applications/lovingcool-lcd.desktop"
AUTOSTART_FILE="${HOME}/.config/autostart/lovingcool-lcd.desktop"
RULE_DST="/etc/udev/rules.d/99-lovingcool-dp36002.rules"

remove_desktop_file() {
  if [[ -f "${DESKTOP_FILE}" ]]; then
    rm -f "${DESKTOP_FILE}"
    update-desktop-database "${HOME}/.local/share/applications" >/dev/null 2>&1 || true
    echo "Removed desktop launcher: ${DESKTOP_FILE}"
  else
    echo "Desktop launcher not found: ${DESKTOP_FILE}"
  fi
}

remove_autostart_file() {
  if [[ -f "${AUTOSTART_FILE}" ]]; then
    rm -f "${AUTOSTART_FILE}"
    echo "Removed autostart entry: ${AUTOSTART_FILE}"
  else
    echo "Autostart entry not found: ${AUTOSTART_FILE}"
  fi
}

remove_udev_rule() {
  if sudo test -f "${RULE_DST}"; then
    sudo rm -f "${RULE_DST}"
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo "Removed udev rule: ${RULE_DST}"
    echo "Replug the cooler to refresh device node permissions."
  else
    echo "udev rule not found: ${RULE_DST}"
  fi
}

main() {
  remove_autostart_file
  remove_desktop_file
  remove_udev_rule
  cat <<MSG

Uninstall complete.

Notes:
- Project files and virtualenv were not deleted.
- If you also want to remove the virtualenv:
    rm -rf ${PROJECT_DIR}/venv
MSG
}

main "$@"
