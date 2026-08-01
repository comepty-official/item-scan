import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from services.prediction_service import FoodPredictionService


class PredictionServiceTests(unittest.TestCase):
    def test_predicts_label_from_existing_dataset_images(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dataset_dir = root / "FoodAI_Dataset"
            apple_dir = dataset_dir / "Apple"
            apple_dir.mkdir(parents=True)
            apple_image = apple_dir / "apple_001.jpg"
            Image.new("RGB", (64, 64), (255, 0, 0)).save(apple_image)

            banana_dir = dataset_dir / "Banana"
            banana_dir.mkdir(parents=True)
            banana_image = banana_dir / "banana_001.jpg"
            Image.new("RGB", (64, 64), (0, 255, 0)).save(banana_image)

            service = FoodPredictionService(dataset_root=dataset_dir)
            prediction = service.predict_label_from_image(
                Image.new("RGB", (64, 64), (255, 0, 0))
            )

            self.assertEqual(prediction, "Apple")


if __name__ == "__main__":
    unittest.main()
