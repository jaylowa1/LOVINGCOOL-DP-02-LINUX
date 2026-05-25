from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any

STATE_PATH = Path.home() / ".config" / "lovingcool-lcd" / "gif_player.json"


class GifProcessManager:
    def __init__(self) -> None:
        self.project_dir = Path(__file__).resolve().parent.parent
        self.player_script = self.project_dir / "gif_player.py"
        self.python_executable = self._python_executable()

    def is_running(self) -> bool:
        state = self._load_state()
        pid = int(state.get("pid", 0) or 0)
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except OSError:
            self._clear_state()
            return False
        return True

    def start(self, gif_path: str | Path, port: str) -> None:
        gif_path = str(Path(gif_path).resolve())
        if self.is_running():
            raise RuntimeError("GIF playback is already running")

        process = subprocess.Popen(
            [
                str(self.python_executable),
                str(self.player_script),
                gif_path,
                "--port",
                port,
            ],
            cwd=self.project_dir,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._save_state({"pid": process.pid, "gif_path": gif_path, "port": port})

    def stop(self) -> None:
        state = self._load_state()
        pid = int(state.get("pid", 0) or 0)
        if pid <= 0:
            self._clear_state()
            return

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        self._clear_state()

    def current_state(self) -> dict[str, Any]:
        if not self.is_running():
            return {}
        return self._load_state()

    @staticmethod
    def _python_executable() -> Path:
        project_dir = Path(__file__).resolve().parent.parent
        venv_python = project_dir / "venv" / "bin" / "python"
        if venv_python.exists():
            return venv_python
        return Path(sys.executable).resolve()

    def _load_state(self) -> dict[str, Any]:
        if not STATE_PATH.exists():
            return {}
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_state(self, data: dict[str, Any]) -> None:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _clear_state(self) -> None:
        STATE_PATH.unlink(missing_ok=True)
