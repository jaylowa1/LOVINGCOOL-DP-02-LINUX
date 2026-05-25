# LOVINGCOOL-DP-02-LINUX
A native Linux app based on Python allowing LOVINGCOOL-DP-02 AIO's LCD display to be changed without requiring Windows.

## Information
This project was vibecoded using Codex on VSCodium. I manually reverse-engineered the LCD protocol using Wireshark + USBPCap.

Now works with GIFs!

Tested on:
- Python 3.14.4
- CachyOS (Arch-based)
- LOVINGCOOL DP-360-02

The 240mm variant may also work depending on if it uses the same protocol as the 360mm, but I don't own it to test it out.

Known identifiers:
- VID:PID = `33c3:7788`
- Device name: `RT-Thread Team RTT Virtual Serial`
- Device path: `/dev/ttyACM*`

## Quick Install
Run the following in a terminal:

```bash
git clone https://github.com/jaylowa1/LOVINGCOOL-DP-02-LINUX.git
cd LOVINGCOOL-DP-02-LINUX
./install.sh
```
Then reboot your computer. DO NOT SKIP THIS STEP.

## Linux permissions
The installer uses a hybrid `udev` setup for reliable non-root access:
- `TAG+="uaccess"` for desktop-session ACLs
- `GROUP="uucp"` on Arch-based distros
- `GROUP="dialout"` on Debian/Ubuntu-based distros
- `MODE="0660"` to avoid world-writable device access

`install.sh` will:
- detect the correct serial group for your distro
- install `/etc/udev/rules.d/99-lovingcool-dp36002.rules`
- add your user to the correct group if needed
- reload `udev` rules

## Media library
Imported media is copied into the app's local `media_library/` folder so it keeps working even if you delete the original source file.

Behavior:
- importing the same file again reuses the existing stored copy instead of duplicating it
- the history strip shows one-click thumbnails for saved media
- right-click a thumbnail to remove that item from the library
- `Run on startup` replays the last saved media item, including GIF playback
