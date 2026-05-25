from __future__ import annotations

import argparse
import io
import signal
import sys
import time
from pathlib import Path

import serial
from PIL import Image, ImageSequence

from lcd_app.protocol import CHUNK_DELAY, CHUNK_SIZE, COMMAND_BYTES, HANDSHAKE_DELAY, LcdProtocol

MAX_FPS = 30
MIN_FRAME_DELAY = 1.0 / MAX_FPS
RECONNECT_DELAY = 1.0
DEFAULT_GIF_DELAY_MS = 100
SHOULD_RUN = True


class GifPlayer:
    def __init__(self, gif_path: str | Path, port: str, quality: int = 90) -> None:
        self.gif_path = Path(gif_path)
        self.port = port
        self.quality = quality
        self.protocol = LcdProtocol()
        self.frames = self._load_frames()

    def play_forever(self) -> int:
        while SHOULD_RUN:
            try:
                with serial.Serial(self.port, self.protocol.baudrate, timeout=self.protocol.timeout) as ser:
                    self._start_stream(ser)
                    self._play_once(ser)
            except (serial.SerialException, OSError) as exc:
                print(f"GIF playback disconnected: {exc}", file=sys.stderr)
                time.sleep(RECONNECT_DELAY)
        return 0

    def _play_once(self, ser: serial.Serial) -> None:
        while SHOULD_RUN:
            for jpeg_data, frame_delay in self.frames:
                if not SHOULD_RUN:
                    return
                frame_start = time.monotonic()
                self._send_frame(ser, jpeg_data)
                remaining_delay = frame_delay - (time.monotonic() - frame_start)
                if remaining_delay <= 0:
                    continue
                deadline = time.monotonic() + remaining_delay
                while SHOULD_RUN and time.monotonic() < deadline:
                    time.sleep(min(0.01, deadline - time.monotonic()))

    @staticmethod
    def _start_stream(ser: serial.Serial) -> None:
        ser.write(COMMAND_BYTES)
        ser.flush()
        time.sleep(HANDSHAKE_DELAY)

    @staticmethod
    def _send_frame(ser: serial.Serial, jpeg_data: bytes) -> None:
        for start in range(0, len(jpeg_data), CHUNK_SIZE):
            chunk = jpeg_data[start : start + CHUNK_SIZE]
            ser.write(chunk)
            ser.flush()
            time.sleep(CHUNK_DELAY)

    def _load_frames(self) -> list[tuple[bytes, float]]:
        if not self.gif_path.is_file():
            raise FileNotFoundError(f"GIF not found: {self.gif_path}")

        frames: list[tuple[bytes, float]] = []
        with Image.open(self.gif_path) as gif:
            for frame in ImageSequence.Iterator(gif):
                rgb_frame = frame.convert("RGB")
                fitted_frame = self.protocol._fit_to_lcd(rgb_frame)
                jpeg_data = self._encode_jpeg(fitted_frame)
                frame_delay = self._frame_delay_seconds(frame)
                frames.append((jpeg_data, frame_delay))

        if not frames:
            raise ValueError("GIF has no frames")
        return frames

    def _encode_jpeg(self, image: Image.Image) -> bytes:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=self.quality, optimize=True)
        return buffer.getvalue()

    @staticmethod
    def _frame_delay_seconds(frame: Image.Image) -> float:
        duration_ms = int(frame.info.get("duration", DEFAULT_GIF_DELAY_MS))
        if duration_ms <= 0:
            duration_ms = DEFAULT_GIF_DELAY_MS
        return max(duration_ms / 1000.0, MIN_FRAME_DELAY)


def _handle_signal(_signum: int, _frame: object) -> None:
    global SHOULD_RUN
    SHOULD_RUN = False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Loop a GIF on the LOVINGCOOL LCD")
    parser.add_argument("gif_path", help="Path to the GIF file")
    parser.add_argument("--port", required=True, help="Serial device path, e.g. /dev/ttyACM0")
    parser.add_argument("--quality", type=int, default=90, help="JPEG quality for streamed frames")
    args = parser.parse_args(argv)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    player = GifPlayer(args.gif_path, args.port, quality=args.quality)
    return player.play_forever()


if __name__ == "__main__":
    raise SystemExit(main())
