from __future__ import annotations

import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path

MEDIA_DIR = Path(__file__).resolve().parent.parent / "media_library"
CHUNK_SIZE = 1024 * 1024


class MediaStore:
    def __init__(self, root: Path = MEDIA_DIR) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def import_file(self, source_path: str | Path) -> Path:
        source = Path(source_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Media not found: {source}")

        duplicate = self._find_duplicate(source)
        if duplicate is not None:
            return duplicate

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_stem = re.sub(r"[^a-zA-Z0-9._-]+", "_", source.stem).strip("_") or "media"
        destination = self.root / f"{stamp}-{safe_stem}{source.suffix.lower()}"
        shutil.copy2(source, destination)
        return destination

    def _find_duplicate(self, source: Path) -> Path | None:
        source_hash = self._sha256(source)
        for candidate in self.root.iterdir():
            if not candidate.is_file() or candidate.suffix.lower() != source.suffix.lower():
                continue
            if self._sha256(candidate) == source_hash:
                return candidate
        return None

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(CHUNK_SIZE):
                digest.update(chunk)
        return digest.hexdigest()
