#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/venv"
REQ_FILE="${PROJECT_DIR}/requirements.txt"
RULE_SRC="${PROJECT_DIR}/deploy/99-lovingcool-dp36002.rules"
RULE_DST="/etc/udev/rules.d/99-lovingcool-dp36002.rules"
DESKTOP_TEMPLATE="${PROJECT_DIR}/deploy/lovingcool-lcd.desktop.template"
DESKTOP_DIR="${HOME}/.local/share/applications"
DESKTOP_FILE="${DESKTOP_DIR}/lovingcool-lcd.desktop"
AUTOSTART_DIR="${HOME}/.config/autostart"
AUTOSTART_FILE="${AUTOSTART_DIR}/lovingcool-lcd.desktop"
ICON_PATH="${PROJECT_DIR}/assets/icon.png"
PY_BIN=""
ENABLE_AUTOSTART=0

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

choose_python() {
  if command -v python3 >/dev/null 2>&1; then
    PY_BIN="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    PY_BIN="$(command -v python)"
  else
    echo "Python 3 not found." >&2
    exit 1
  fi
}

setup_venv() {
  if [[ -d "${VENV_DIR}" ]]; then
    return
  fi
  echo "Creating virtualenv at ${VENV_DIR}"
  "${PY_BIN}" -m venv "${VENV_DIR}"
}

install_deps() {
  echo "Installing Python dependencies"
  "${VENV_DIR}/bin/python" -m pip install --upgrade pip
  "${VENV_DIR}/bin/pip" install -r "${REQ_FILE}"
}

install_udev_rule() {
  echo "Installing udev rule (requires sudo)"
  sudo install -m 0644 "${RULE_SRC}" "${RULE_DST}"
  sudo udevadm control --reload-rules
  sudo udevadm trigger
}

install_desktop_file() {
  mkdir -p "${DESKTOP_DIR}"

  local app_exec="${VENV_DIR}/bin/python ${PROJECT_DIR}/main.py"
  local icon_value="utilities-terminal"
  if [[ -f "${ICON_PATH}" ]]; then
    icon_value="${ICON_PATH}"
  fi

  sed \
    -e "s|__APP_EXEC__|${app_exec}|g" \
    -e "s|__APP_PATH__|${PROJECT_DIR}|g" \
    -e "s|__APP_ICON__|${icon_value}|g" \
    "${DESKTOP_TEMPLATE}" > "${DESKTOP_FILE}"

  chmod 0644 "${DESKTOP_FILE}"
  update-desktop-database "${DESKTOP_DIR}" >/dev/null 2>&1 || true
}

install_autostart_file() {
  mkdir -p "${AUTOSTART_DIR}"

  local app_exec="${VENV_DIR}/bin/python ${PROJECT_DIR}/main.py --send-last"
  local icon_value="utilities-terminal"
  if [[ -f "${ICON_PATH}" ]]; then
    icon_value="${ICON_PATH}"
  fi

  sed \
    -e "s|__APP_EXEC__|${app_exec}|g" \
    -e "s|__APP_PATH__|${PROJECT_DIR}|g" \
    -e "s|__APP_ICON__|${icon_value}|g" \
    "${DESKTOP_TEMPLATE}" > "${AUTOSTART_FILE}"
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --enable-autostart)
        ENABLE_AUTOSTART=1
        shift
        ;;
      *)
        echo "Unknown option: $1" >&2
        echo "Usage: ./install.sh [--enable-autostart]" >&2
        exit 1
        ;;
    esac
  done
}

print_post_install() {
  local autostart_status="disabled"
  if [[ "${ENABLE_AUTOSTART}" -eq 1 ]]; then
    autostart_status="enabled"
  fi

  cat <<MSG

Install complete.

Important:
- Do NOT run the GUI with sudo.
- Replug the cooler (unplug/replug USB) so new udev permissions apply.
- If serial access still fails, log out and log back in.

Run app:
  ${VENV_DIR}/bin/python ${PROJECT_DIR}/main.py

Desktop launcher installed:
  ${DESKTOP_FILE}

Startup send:
  ${autostart_status}
  Toggle later inside the app with "Send last image on login".
MSG
}

main() {
  parse_args "$@"
  need_cmd sed
  need_cmd sudo
  need_cmd udevadm
  choose_python

  if ! "${PY_BIN}" -m venv -h >/dev/null 2>&1; then
    echo "Python venv module is unavailable. Install python3-venv (Debian/Ubuntu) or ensure venv support (Arch)." >&2
    exit 1
  fi

  if [[ ! -f "${REQ_FILE}" ]]; then
    echo "Missing requirements file: ${REQ_FILE}" >&2
    exit 1
  fi

  if [[ ! -f "${RULE_SRC}" ]]; then
    echo "Missing udev rule file: ${RULE_SRC}" >&2
    exit 1
  fi

  if [[ ! -f "${DESKTOP_TEMPLATE}" ]]; then
    echo "Missing desktop template: ${DESKTOP_TEMPLATE}" >&2
    exit 1
  fi

  setup_venv
  install_deps
  install_udev_rule
  install_desktop_file
  if [[ "${ENABLE_AUTOSTART}" -eq 1 ]]; then
    install_autostart_file
  fi
  print_post_install
}

main "$@"
