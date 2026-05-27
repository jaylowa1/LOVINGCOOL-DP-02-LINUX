import argparse
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from lcd_app.gif_process import GifProcessManager
from lcd_app.main_window import MainWindow
from lcd_app.protocol import LcdProtocol
from lcd_app.settings import AppSettings


def run_last_media() -> int:
    settings = AppSettings().load()
    media_path = settings.get("last_media", settings.get("last_image", ""))
    port = settings.get("last_port", "")

    if not media_path or not port:
        return 0

    protocol = LcdProtocol()
    available_ports = protocol.list_ports()
    if port not in available_ports:
        return 0

    media_file = Path(media_path)
    if not media_file.is_file():
        return 0

    stretch = bool(settings.get("display_stretch", False))

    if media_file.suffix.lower() == ".gif":
        gif_process = GifProcessManager()
        if not gif_process.is_running():
            gif_process.start(media_file, port, stretch=stretch)
        return 0

    protocol.send_image_file(media_file, port, stretch=stretch)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--run-last", action="store_true")
    args, _ = parser.parse_known_args(argv)

    if args.run_last:
        return run_last_media()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
