"""Simple image-based prediction over the local dataset folders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image

from utils.helpers import display_name


@dataclass
class PredictionResult:
    """A friendly prediction result for the camera UI."""

    label: str | None
    confidence: float
    message: str


class FoodPredictionService:
    """Predict a label by matching a new image against saved dataset folders.

    This is intentionally lightweight and offline-first. It does not train a
    neural network; instead it compares the input image's average color against
    each existing label folder's representative color and proposes the closest
    match. That gives the app a practical "predict from DB" behavior based on
    the data already collected by the user.
    """

    def __init__(self, dataset_root: Path | None = None) -> None:
        self.dataset_root = Path(dataset_root or Path("FoodAI_Dataset")).resolve()

    def predict_label_from_image(self, image: Image.Image) -> str | None:
        """Return the best matching label for ``image`` or ``None`` if empty."""
        result = self.predict_from_image(image)
        return result.label

    def predict_from_image(self, image: Image.Image) -> PredictionResult:
        """Return a richer prediction result for the camera UI."""
        if not self.dataset_root.exists():
            return PredictionResult(None, 0.0, "I don't know this one yet.")

        image = image.convert("RGB")
        target_color = self._average_color(image)
        best_label: str | None = None
        best_distance: float | None = None

        for folder in sorted(self.dataset_root.iterdir(), key=lambda p: p.name.lower()):
            if not folder.is_dir():
                continue
            examples = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
            if not examples:
                continue
            representative = self._load_representative_color(examples)
            distance = self._color_distance(target_color, representative)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_label = display_name(folder.name)

        if best_label is None or best_distance is None:
            return PredictionResult(None, 0.0, "I don't know this one yet.")

        confidence = max(0.0, min(1.0, 1.0 - (best_distance / 500.0)))
        if confidence < 0.35 or best_distance > 160.0:
            return PredictionResult(None, confidence, "I don't know this one yet.")
        return PredictionResult(best_label, confidence, f"This looks familiar — I think it might be {best_label}.")

    def predict_from_path(self, image_path: Path) -> PredictionResult:
        """Load an image from disk and return a prediction."""
        with Image.open(image_path) as img:
            return self.predict_from_image(img)

    def _load_representative_color(self, images: Iterable[Path]) -> tuple[int, int, int]:
        colors = [self._average_color(self._load_image(path)) for path in images]
        if not colors:
            return (0, 0, 0)
        return self._average_color_from_pixels(colors)

    def _load_image(self, path: Path) -> Image.Image:
        with Image.open(path) as img:
            return img.convert("RGB")

    @staticmethod
    def _average_color(image: Image.Image) -> tuple[int, int, int]:
        image = image.resize((16, 16))
        pixels = list(image.getdata())
        if not pixels:
            return (0, 0, 0)
        red = sum(pixel[0] for pixel in pixels) // len(pixels)
        green = sum(pixel[1] for pixel in pixels) // len(pixels)
        blue = sum(pixel[2] for pixel in pixels) // len(pixels)
        return (red, green, blue)

    @staticmethod
    def _average_color_from_pixels(colors: Iterable[tuple[int, int, int]]) -> tuple[int, int, int]:
        pixels = list(colors)
        if not pixels:
            return (0, 0, 0)
        red = sum(color[0] for color in pixels) // len(pixels)
        green = sum(color[1] for color in pixels) // len(pixels)
        blue = sum(color[2] for color in pixels) // len(pixels)
        return (red, green, blue)

    @staticmethod
    def _color_distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> float:
        return ((left[0] - right[0]) ** 2 + (left[1] - right[1]) ** 2 + (left[2] - right[2]) ** 2) ** 0.5
