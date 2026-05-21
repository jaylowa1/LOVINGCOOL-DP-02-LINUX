# LOVINGCOOL-DP-02-LINUX
A native Linux app based on Python allowing LOVINGCOOL-DP-02 AIO's LCD display to be changed without requiring Windows.
## Information
This project was vibecoded using Codex on VSCodium. I manually reverse-engineered the LCD protocol using Wireshark + USBPCap.

This does NOT work with GIFs. If you upload a GIF, it will use the first frame of the GIF and display it.

Tested on:
  - Python 3.14.4
  - CachyOS (Arch-Based)
  - LOVINGCOOL DP-360-02
The 240mm variant may also work depending on if it uses the same protocol as the 360mm, but I don't own it to test it out.

Known Identifiers:
- VID:PID = 33c3:7788
- Device name: RT-Thread Team RTT Virtual Serial

## Quick Install
Run the following in a terminal.
```bash
git clone https://github.com/jaylowa1/LOVINGCOOL-DP-02-LINUX.git
cd lovingcool-linux-dp-360-02
./install.sh
```
After installation, reboot your computer and launch the application.



