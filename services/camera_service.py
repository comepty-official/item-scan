"""
Camera helpers.

The Kivy :class:`~kivy.uix.camera.Camera` widget owns the hardware; this module
only deals with turning its texture into a straight, correctly-oriented JPEG on
disk (and with importing an existing file instead).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from utils.helpers import now_iso
from utils.paths import TEMP_DIR


def _rotate_with_pillow(path: Path, rotation: int) -> None:
    """Rotate a saved image in place. Silently skipped when Pillow is missing."""
    if rotation % 360 == 0:
        return
    try:
        from PIL import Image  # imported lazily: Pillow is optional
    except ImportError:
        return
    with Image.open(path) as image:
        # ``expand`` keeps the whole frame visible for 90/270 degree rotations.
        image.rotate(-rotation, expand=True).convert("RGB").save(path, quality=92)


class CameraService:
    """Saves camera frames into the temporary folder."""

    @staticmethod
    def temp_path() -> Path:
        """A unique scratch path for the next capture."""
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = now_iso().replace(":", "-")
        return TEMP_DIR / f"capture_{stamp}.jpg"

    @classmethod
    def capture(cls, texture, rotation: int = 0) -> Path:
        """Write *texture* to a JPEG and return its path.

        ``rotation`` compensates for devices whose sensor is mounted sideways so
        the stored photo is always the right way up.
        """
        if texture is None:
            raise RuntimeError("Camera is not ready yet.")
        path = cls.temp_path()
        # ``flipped=False`` keeps the image identical to the on-screen preview.
        texture.save(str(path), flipped=False)
        _rotate_with_pillow(path, rotation)
        return path

    @classmethod
    def import_file(cls, source: str | Path) -> Path:
        """Copy an existing picture into the scratch folder and return the copy."""
        source = Path(source)
        if not source.is_file():
            raise RuntimeError("Selected file does not exist.")
        target = cls.temp_path().with_suffix(source.suffix.lower() or ".jpg")
        shutil.copy2(source, target)
        return target
