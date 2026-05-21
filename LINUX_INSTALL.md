# LOVINGCOOL DP-360-02 Linux Install

This installer sets up the app as a normal desktop app. The GUI must run as a normal user, never with `sudo`.

## Quick Start

```bash
git clone <your-repo-url>
cd lovingcool-linux-dp-360-02
./install.sh
```

## What `install.sh` does

- Checks required commands (`python3`, `sudo`, `udevadm`, `sed`)
- Creates `venv/` if missing
- Installs Python dependencies from `requirements.txt`
- Installs udev rule to `/etc/udev/rules.d/99-lovingcool-dp36002.rules`
- Reloads udev rules and triggers devices
- Creates desktop launcher at `~/.local/share/applications/lovingcool-lcd.desktop`

## udev details

Rule matches:

- `VID:PID = 33c3:7788`
- `ttyACM*` nodes

Access model:

- Primary: `TAG+="uaccess"` (modern desktop sessions)
- Fallback: add your user to the actual device group shown by `ls -l /dev/ttyACM0` if ACL access is unavailable

## After install

- Unplug and replug the cooler
- If access still fails, log out/log in
- If still failing, check device group and add user:

```bash
ls -l /dev/ttyACM0
sudo usermod -aG uucp $USER      # Arch, if group is uucp
sudo usermod -aG dialout $USER   # Debian/Ubuntu, if group is dialout
```

Run app:

```bash
./venv/bin/python main.py
```

## Uninstall

```bash
./uninstall.sh
```

This removes:

- user desktop launcher
- system udev rule (with sudo)

Project files are kept.
