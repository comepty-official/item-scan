"""
Dataset filesystem manager.

Owns everything under ``FoodAI_Dataset/``: creating label folders, generating
sequential filenames, moving / deleting images and renaming whole folders.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from utils.helpers import display_name, folder_name, next_image_path
from utils.paths import DATASET_DIR

#: Image types shown in the library.
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


class DatasetStorage:
    """High-level API over the dataset directory tree."""

    def __init__(self, root: Path = DATASET_DIR) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------- reading
    def folders(self) -> list[tuple[str, int]]:
        """Return ``[(folder_name, image_count), ...]`` sorted alphabetically."""
        result: list[tuple[str, int]] = []
        for entry in sorted(self.root.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_dir():
                result.append((entry.name, len(self.images(entry.name))))
        return result

    def images(self, folder: str) -> list[Path]:
        """Every image inside one label folder, sorted by filename."""
        directory = self.root / folder
        if not directory.is_dir():
            return []
        return sorted(
            (p for p in directory.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES),
            key=lambda p: p.name.lower(),
        )

    def total_images(self) -> int:
        """Number of images in the whole dataset."""
        return sum(count for _, count in self.folders())

    # ------------------------------------------------------------- writing
    def save_image(self, source: Path, label: str) -> Path:
        """Copy *source* into ``FoodAI_Dataset/<Label>/<label>_NNN.jpg``.

        The label folder is created when it does not exist yet.
        """
        source = Path(source)
        if not source.is_file():
            raise RuntimeError("Captured image is missing from disk.")
        directory = self.root / folder_name(label)
        directory.mkdir(parents=True, exist_ok=True)
        target = next_image_path(directory, label, source.suffix.lower() or ".jpg")
        shutil.copy2(source, target)
        return target

    def rename_folder(self, folder: str, new_label: str) -> str:
        """Rename a label folder and every image inside it. Returns the new name."""
        new_folder = folder_name(new_label)
        source = self.root / folder
        target = self.root / new_folder
        if new_folder == folder:
            return folder
        if target.exists():
            raise RuntimeError(f"'{display_name(new_folder)}' already exists.")
        source.rename(target)
        # Keep filenames aligned with the new label (burger_001 -> pizza_001).
        for index, image in enumerate(self.images(new_folder), start=1):
            desired = target / f"{new_folder.lower()}_{index:03d}{image.suffix.lower()}"
            if image != desired and not desired.exists():
                image.rename(desired)
        return new_folder

    def move_image(self, image: Path, new_label: str) -> Path:
        """Move one image into another label folder (folder created if needed)."""
        directory = self.root / folder_name(new_label)
        directory.mkdir(parents=True, exist_ok=True)
        target = next_image_path(directory, new_label, image.suffix.lower())
        shutil.move(str(image), str(target))
        return target

    def delete_image(self, image: Path) -> None:
        """Delete a single image file."""
        Path(image).unlink(missing_ok=True)

    def delete_folder(self, folder: str) -> None:
        """Delete a label folder and everything inside it."""
        shutil.rmtree(self.root / folder, ignore_errors=True)
