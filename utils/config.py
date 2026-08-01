"""Persisted application settings (theme, camera, USDA key)."""

from __future__ import annotations

import json
from typing import Any

from utils.paths import CONFIG_PATH

#: Defaults used the first time the app starts.
DEFAULTS: dict[str, Any] = {
    "theme_style": "Light",      # "Light" or "Dark"
    "primary_palette": "Green",  # KivyMD Material 3 palette name
    "camera_index": 0,           # which physical camera to open
    "preview_rotation": 0,       # 0 / 90 / 180 / 270 - keeps the camera "straight"
    "usda_api_key": "nI2FcdapypzLIALjr1Tkl5XzuGzWT1O8G6cdhyRL",  # FoodData Central key (DEMO_KEY works for testing)
}


class AppConfig:
    """Tiny JSON-backed settings store with attribute-style access helpers."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = dict(DEFAULTS)
        self.load()

    # ------------------------------------------------------------------ io
    def load(self) -> None:
        """Read settings from disk, ignoring corrupt or partial files."""
        if CONFIG_PATH.exists():
            try:
                stored = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                if isinstance(stored, dict):
                    self._data.update({k: v for k, v in stored.items() if k in DEFAULTS})
            except (OSError, json.JSONDecodeError):
                pass  # keep defaults - a broken config must never crash the app

    def save(self) -> None:
        """Write the current settings back to ``config.json``."""
        CONFIG_PATH.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    # --------------------------------------------------------------- access
    def get(self, key: str, default: Any = None) -> Any:
        """Return a setting value."""
        return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        """Update a setting and persist it immediately."""
        self._data[key] = value
        self.save()

    def as_dict(self) -> dict[str, Any]:
        """Return a copy of every setting."""
        return dict(self._data)
