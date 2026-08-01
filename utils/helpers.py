"""Small, dependency-free helper functions shared across the app."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

#: Characters that are illegal (or simply inconvenient) inside folder names.
_ILLEGAL = re.compile(r"[^A-Za-z0-9]+")


def folder_name(label: str) -> str:
    """Convert a human food name into a safe folder name.

    ``"ice cream!"`` -> ``"Ice_Cream"``
    """
    words = [w for w in _ILLEGAL.split(label.strip()) if w]
    if not words:
        return "Unlabeled"
    return "_".join(word.capitalize() for word in words)


def file_stem(label: str) -> str:
    """Return the lowercase file prefix used for images (``"ice_cream"``)."""
    return folder_name(label).lower()


def display_name(folder: str) -> str:
    """Turn a folder name back into a readable label (``"Ice_Cream"`` -> ``"Ice Cream"``)."""
    return folder.replace("_", " ").strip() or "Unlabeled"


def next_image_path(folder: Path, label: str, extension: str = ".jpg") -> Path:
    """Return the next free ``<stem>_NNN<ext>`` path inside *folder*.

    The counter is derived from the files already present, so deleting an image
    never causes a filename collision.
    """
    stem = file_stem(label)
    pattern = re.compile(rf"^{re.escape(stem)}_(\d+)$", re.IGNORECASE)
    highest = 0
    if folder.exists():
        for existing in folder.iterdir():
            match = pattern.match(existing.stem)
            if match:
                highest = max(highest, int(match.group(1)))
    return folder / f"{stem}_{highest + 1:03d}{extension}"


def now_iso() -> str:
    """Current local time as an ISO-8601 string (stored in the database)."""
    return datetime.now().isoformat(timespec="seconds")


def pretty_date(value: str) -> str:
    """Format an ISO timestamp for display; fall back to the raw value."""
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y, %H:%M")
    except (TypeError, ValueError):
        return value or "-"
