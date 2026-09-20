"""Resume storage abstraction and local filesystem implementation."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Protocol
from uuid import uuid4

from app.core.config import get_settings


class StorageService(Protocol):
    """Persistence interface for resume files."""

    def save(
        self,
        file_bytes: bytes,
        original_filename: str,
        mime_type: str | None,
    ) -> tuple[str, str]:
        """Persist a file and return the storage key and stored filename."""

    def get(self, storage_key: str) -> bytes:
        """Read a stored file back as bytes."""

    def delete(self, storage_key: str) -> None:
        """Delete a stored file."""


class LocalStorageService:
    """Small local storage layer suitable for development and tests."""

    def __init__(self, root_path: str | Path | None = None) -> None:
        configured = root_path or get_settings().resume_storage_path
        root = Path(configured)
        if not root.is_absolute():
            root = Path(__file__).resolve().parents[3] / root
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_storage_key(self, original_filename: str) -> str:
        candidate = PurePosixPath(original_filename.replace("\\", "/")).name
        if candidate in {"", ".", ".."}:
            raise ValueError("Invalid resume filename")
        name = Path(candidate).stem
        suffix = Path(candidate).suffix.lower()
        if not name or not suffix:
            raise ValueError("Resume file must include a valid filename and extension")
        safe_suffix = suffix if suffix in {".pdf", ".docx"} else ".bin"
        return f"{uuid4().hex}{safe_suffix}"

    def save(
        self, file_bytes: bytes, original_filename: str, mime_type: str | None
    ) -> tuple[str, str]:
        storage_key = self._safe_storage_key(original_filename)
        target = (self.root / storage_key).resolve()
        if not str(target).startswith(str(self.root.resolve())):
            raise ValueError("Resume storage path is invalid")
        target.write_bytes(file_bytes)
        return storage_key, storage_key

    def get(self, storage_key: str) -> bytes:
        safe_name = PurePosixPath(storage_key).name
        if safe_name in {"", ".", ".."} or "/" in safe_name or "\\" in safe_name:
            raise ValueError("Unsafe resume storage key")
        target = (self.root / safe_name).resolve()
        if not str(target).startswith(str(self.root.resolve())):
            raise ValueError("Resume storage key escapes the configured directory")
        return target.read_bytes()

    def delete(self, storage_key: str) -> None:
        safe_name = PurePosixPath(storage_key).name
        if safe_name in {"", ".", ".."} or "/" in safe_name or "\\" in safe_name:
            raise ValueError("Unsafe resume storage key")
        target = (self.root / safe_name).resolve()
        if not str(target).startswith(str(self.root.resolve())):
            raise ValueError("Resume storage key escapes the configured directory")
        if target.exists():
            target.unlink()
