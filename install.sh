#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/venv"
REQ_FILE="${PROJECT_DIR}/requirements.txt"
RULE_TEMPLATE="${PROJECT_DIR}/deploy/99-lovingcool-dp36002.rules"
RULE_DST="/etc/udev/rules.d/99-lovingcool-dp36002.rules"
DESKTOP_TEMPLATE="${PROJECT_DIR}/deploy/lovingcool-lcd.desktop.template"
DESKTOP_DIR="${HOME}/.local/share/applications"
DESKTOP_FILE="${DESKTOP_DIR}/lovingcool-lcd.desktop"
AUTOSTART_DIR="${HOME}/.config/autostart"
AUTOSTART_FILE="${AUTOSTART_DIR}/lovingcool-lcd.desktop"
ICON_PATH="${PROJECT_DIR}/assets/icon.png"
PY_BIN=""
ENABLE_AUTOSTART=0
SERIAL_GROUP=""
GROUP_CHANGED=0

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

ensure_user_group() {
  if id -nG "$USER" | tr ' ' '\n' | grep -qx "${SERIAL_GROUP}"; then
    return
  fi

  echo "Adding ${USER} to group ${SERIAL_GROUP} (requires sudo)"
  sudo usermod -aG "${SERIAL_GROUP}" "$USER"
  GROUP_CHANGED=1
}

install_udev_rule() {
  echo "Installing udev rule for group ${SERIAL_GROUP} (requires sudo)"
  sed "s|__SERIAL_GROUP__|${SERIAL_GROUP}|g" "${RULE_TEMPLATE}" | sudo tee "${RULE_DST}" >/dev/null
  sudo chmod 0644 "${RULE_DST}"
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

  chmod 0644 "${AUTOSTART_FILE}"
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
  local startup_send_status="disabled"
  if [[ "${ENABLE_AUTOSTART}" -eq 1 ]]; then
    startup_send_status="enabled"
  fi

  cat <<MSG

Install complete.

Serial access:
- Using group fallback: ${SERIAL_GROUP}
- udev rule installed to: ${RULE_DST}
- Replug the cooler so the new rule applies.
MSG

  if [[ "${GROUP_CHANGED}" -eq 1 ]]; then
    cat <<MSG
- Your user was added to ${SERIAL_GROUP}.
- Log out and log back in, or reboot, before testing.
MSG
  else
    cat <<MSG
- Your user is already in ${SERIAL_GROUP}.
MSG
  fi

  cat <<MSG

Important:
- Do NOT run the GUI with sudo.

Run app:
  ${VENV_DIR}/bin/python ${PROJECT_DIR}/main.py

Desktop launcher installed:
  ${DESKTOP_FILE}

Startup send:
  ${startup_send_status}
  Toggle later inside the app with "Send last image on login".
MSG
}

main() {
  parse_args "$@"
  need_cmd awk
  need_cmd getent
  need_cmd sed
  need_cmd sudo
  need_cmd udevadm
  choose_python
  detect_serial_group

  if ! "${PY_BIN}" -m venv -h >/dev/null 2>&1; then
    echo "Python venv module is unavailable. Install python3-venv (Debian/Ubuntu) or ensure venv support (Arch)." >&2
    exit 1
  fi

  if [[ ! -f "${REQ_FILE}" ]]; then
    echo "Missing requirements file: ${REQ_FILE}" >&2
    exit 1
  fi

  if [[ ! -f "${RULE_TEMPLATE}" ]]; then
    echo "Missing udev rule file: ${RULE_TEMPLATE}" >&2
    exit 1
  fi

  if [[ ! -f "${DESKTOP_TEMPLATE}" ]]; then
    echo "Missing desktop template: ${DESKTOP_TEMPLATE}" >&2
    exit 1
  fi

  setup_venv
  install_deps
  ensure_user_group
  install_udev_rule
  install_desktop_file
  if [[ "${ENABLE_AUTOSTART}" -eq 1 ]]; then
    install_autostart_file
  fi
  print_post_install
}

main "$@"
