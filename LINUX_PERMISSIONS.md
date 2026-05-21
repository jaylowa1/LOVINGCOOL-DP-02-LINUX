# Linux Device Permissions (No sudo GUI)

This app should run as a normal user. Do **not** run the GUI with `sudo`.

## What this config does

- Installs a `udev` rule for LOVINGCOOL DP-360-02 (`VID:PID = 33c3:7788`)
- Grants access to `/dev/ttyACM*` for active local users (`TAG+="uaccess"`)
- Adds `dialout` group fallback permissions (`MODE="0660"`)

Rule installed to:

- `/etc/udev/rules.d/99-lovingcool-dp36002.rules`

## 1) Install the rule (one-time, admin)

From project root:

```bash
sudo ./scripts/install_udev_rule.sh
```

The script will:

- copy the rule into `/etc/udev/rules.d/`
- reload udev rules (`udevadm control --reload-rules`)
- trigger udev (`udevadm trigger`)

Then unplug/replug the cooler.

## 2) Ensure your user has serial group fallback

Debian/Ubuntu and Arch both commonly use `dialout` for tty devices.

```bash
sudo usermod -aG dialout $USER
```

Log out and log back in after this.

## 3) Verify access

```bash
ls -l /dev/ttyACM*
groups
```

You should be able to run:

```bash
./venv/bin/python main.py
```

without sudo.

## Troubleshooting

- Confirm device IDs:

```bash
udevadm info -a -n /dev/ttyACM0 | rg 'idVendor|idProduct'
```

Expected:

- `idVendor` = `33c3`
- `idProduct` = `7788`

- If permissions still fail, re-run:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

and unplug/replug the device.
