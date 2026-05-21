import argparse
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from lcd_app.main_window import MainWindow
from lcd_app.protocol import LcdProtocol
from lcd_app.settings import AppSettings


def send_last_image() -> int:
    settings = AppSettings().load()
    image_path = settings.get("last_image", "")
    port = settings.get("last_port", "")

    if not image_path or not port:
        return 0

    protocol = LcdProtocol()
    available_ports = protocol.list_ports()
    if port not in available_ports:
        return 0

    if not Path(image_path).is_file():
        return 0

    protocol.send_image_file(image_path, port)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--send-last", action="store_true")
    args, _ = parser.parse_known_args(argv)

    if args.send_last:
        return send_last_image()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
