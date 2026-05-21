from __future__ import annotations

import glob
import io
import time
from pathlib import Path

import serial
from PIL import Image, ImageSequence

COMMAND_BYTES = bytes.fromhex("55 aa 07 00 11 17 01")
CHUNK_SIZE = 4096
HANDSHAKE_DELAY = 0.5
CHUNK_DELAY = 0.01


class LcdProtocol:
    def __init__(self, baudrate: int = 115200, timeout: float = 1.0) -> None:
        self.baudrate = baudrate
        self.timeout = timeout

    def list_ports(self) -> list[str]:
        return sorted(glob.glob("/dev/ttyACM*"))

    def send_image_file(self, image_path: str | Path, port: str) -> None:
        jpeg_data = self._to_jpeg_bytes(image_path)
        self.send_jpeg_bytes(jpeg_data, port)

    def send_jpeg_bytes(self, jpeg_data: bytes, port: str) -> None:
        if not jpeg_data:
            raise ValueError("JPEG data is empty")

        with serial.Serial(port, self.baudrate, timeout=self.timeout) as ser:
            ser.write(COMMAND_BYTES)
            ser.flush()
            time.sleep(HANDSHAKE_DELAY)

            for start in range(0, len(jpeg_data), CHUNK_SIZE):
                chunk = jpeg_data[start : start + CHUNK_SIZE]
                ser.write(chunk)
                ser.flush()
                time.sleep(CHUNK_DELAY)

    @staticmethod
    def _to_jpeg_bytes(image_path: str | Path, quality: int = 95) -> bytes:
        with Image.open(image_path) as image:
            if getattr(image, "is_animated", False):
                image = ImageSequence.Iterator(image)[0]
            rgb_image = image.convert("RGB")
            buf = io.BytesIO()
            rgb_image.save(buf, format="JPEG", quality=quality, optimize=True)
            return buf.getvalue()
