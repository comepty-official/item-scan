"""
``food_db.json`` access layer.

The database is a plain JSON document so that it can be inspected, diffed and
shipped to the training pipeline without any extra tooling::

    {
      "next_id": 4,
      "records": [
        {
          "id": 1,
          "name": "Burger",
          "folder": "Burger",
          "image": "FoodAI_Dataset/Burger/burger_001.jpg",
          "description": "Beef burger, street food",
          "status": "saved",
          "date": "2026-08-01T10:12:00"
        }
      ]
    }
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any

from utils.helpers import now_iso
from utils.paths import BASE_DIR, DB_PATH, PENDING_PATH


class JsonStore:
    """Thread-safe JSON document with an auto-incrementing ``id`` column."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()
        self._data: dict[str, Any] = {"next_id": 1, "records": []}
        self.load()

    # ------------------------------------------------------------------ io
    def load(self) -> None:
        """Load the document from disk, recovering gracefully from corruption."""
        with self._lock:
            if self.path.exists():
                try:
                    stored = json.loads(self.path.read_text(encoding="utf-8"))
                    if isinstance(stored, dict) and isinstance(stored.get("records"), list):
                        self._data = stored
                        self._data.setdefault("next_id", len(stored["records"]) + 1)
                        return
                except (OSError, json.JSONDecodeError):
                    pass
            self.save()

    def save(self) -> None:
        """Persist the document (written atomically via a temporary file)."""
        with self._lock:
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
            tmp.replace(self.path)

    # ------------------------------------------------------------- queries
    @property
    def records(self) -> list[dict[str, Any]]:
        """Every record, newest last."""
        return list(self._data["records"])

    def get(self, record_id: int) -> dict[str, Any] | None:
        """Return a single record by id, or ``None``."""
        return next((r for r in self._data["records"] if r["id"] == record_id), None)

    def by_folder(self, folder: str) -> list[dict[str, Any]]:
        """Every record belonging to one dataset folder."""
        return [r for r in self._data["records"] if r.get("folder") == folder]

    def by_image(self, relative_path: str) -> dict[str, Any] | None:
        """Look a record up by its stored (relative) image path."""
        return next(
            (r for r in self._data["records"] if r.get("image") == relative_path), None
        )

    # -------------------------------------------------------------- writes
    def insert(self, **fields: Any) -> dict[str, Any]:
        """Insert a record, filling in ``id``/``date`` when missing."""
        with self._lock:
            record: dict[str, Any] = {
                "id": self._data["next_id"],
                "date": now_iso(),
                "status": "saved",
            }
            record.update(fields)
            record["id"] = self._data["next_id"]
            self._data["next_id"] += 1
            self._data["records"].append(record)
            self.save()
            return record

    def update(self, record_id: int, **fields: Any) -> dict[str, Any] | None:
        """Patch a record and return it."""
        with self._lock:
            record = self.get(record_id)
            if record is None:
                return None
            record.update(fields)
            self.save()
            return record

    def delete(self, record_id: int) -> bool:
        """Remove a record; returns ``True`` when something was deleted."""
        with self._lock:
            before = len(self._data["records"])
            self._data["records"] = [
                r for r in self._data["records"] if r["id"] != record_id
            ]
            changed = len(self._data["records"]) != before
            if changed:
                self.save()
            return changed

    def delete_where_folder(self, folder: str) -> int:
        """Delete every record of a folder; returns how many were removed."""
        with self._lock:
            keep = [r for r in self._data["records"] if r.get("folder") != folder]
            removed = len(self._data["records"]) - len(keep)
            self._data["records"] = keep
            if removed:
                self.save()
            return removed


class FoodDatabase(JsonStore):
    """The main dataset database (``food_db.json``)."""

    def __init__(self) -> None:
        super().__init__(DB_PATH)

    def rename_folder(self, old_folder: str, new_folder: str, new_name: str) -> None:
        """Re-point every record of *old_folder* at the renamed folder."""
        with self._lock:
            for record in self._data["records"]:
                if record.get("folder") == old_folder:
                    record["folder"] = new_folder
                    record["name"] = new_name
                    record["image"] = record["image"].replace(
                        f"FoodAI_Dataset/{old_folder}/", f"FoodAI_Dataset/{new_folder}/", 1
                    )
            self.save()

    def move_image(self, old_relative: str, new_relative: str, folder: str, name: str) -> None:
        """Update a record after its image was moved to another folder."""
        with self._lock:
            record = self.by_image(old_relative)
            if record is not None:
                record.update(image=new_relative, folder=folder, name=name)
                self.save()

    def relative(self, absolute: Path) -> str:
        """Convert an absolute image path into the project-relative form we store."""
        try:
            return absolute.relative_to(BASE_DIR).as_posix()
        except ValueError:
            return absolute.as_posix()


class PendingDatabase(JsonStore):
    """Queue of records whose image could not be written to the dataset."""

    def __init__(self) -> None:
        super().__init__(PENDING_PATH)
