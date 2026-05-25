from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "LOVINGCOOL LCD Startup"
AUTOSTART_DIR = Path.home() / ".config" / "autostart"
AUTOSTART_PATH = AUTOSTART_DIR / "lovingcool-lcd.desktop"


class AutostartManager:
    def __init__(self) -> None:
        self.project_dir = Path(__file__).resolve().parent.parent
        self.main_script = self.project_dir / "main.py"

    def is_enabled(self) -> bool:
        return AUTOSTART_PATH.exists()

    def ensure_current(self) -> None:
        if self.is_enabled():
            self._write_entry()

    def set_enabled(self, enabled: bool) -> None:
        if enabled:
            self._write_entry()
            return

        AUTOSTART_PATH.unlink(missing_ok=True)

    def _write_entry(self) -> None:
        AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
        AUTOSTART_PATH.write_text(self._desktop_entry(), encoding="utf-8")

    def _desktop_entry(self) -> str:
        exec_path = self._python_executable()
        icon_path = self.project_dir / "assets" / "icon.png"
        icon_value = str(icon_path) if icon_path.exists() else "utilities-terminal"

        return "\n".join(
            [
                "[Desktop Entry]",
                "Type=Application",
                "Version=1.0",
                f"Name={APP_NAME}",
                "Comment=Run the last LOVINGCOOL LCD media item at login",
                f"Exec={exec_path} {self.main_script} --run-last",
                f"Path={self.project_dir}",
                f"Icon={icon_value}",
                "Terminal=false",
                "Categories=Utility;System;",
                "StartupNotify=true",
                "X-GNOME-Autostart-enabled=true",
                "",
            ]
        )

    def _python_executable(self) -> Path:
        venv_python = self.project_dir / "venv" / "bin" / "python"
        if venv_python.exists():
            return venv_python
        return Path(sys.executable).resolve()
