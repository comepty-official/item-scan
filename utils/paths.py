"""
Central place for every filesystem path used by the application.

Keeping paths in one module means the whole app can be relocated by editing a
single file, and unit tests can monkey-patch :data:`BASE_DIR` if required.
"""

from pathlib import Path

#: Project root (the folder that contains ``main.py``).
BASE_DIR: Path = Path(__file__).resolve().parent.parent

#: Root of the generated dataset (one sub-folder per food label).
DATASET_DIR: Path = BASE_DIR / "FoodAI_Dataset"

#: JSON "database" holding one record per saved image.
DB_PATH: Path = BASE_DIR / "food_db.json"

#: Queue of records that could not be written to the dataset.
PENDING_PATH: Path = BASE_DIR / "pending_db.json"

#: Persisted user settings.
CONFIG_PATH: Path = BASE_DIR / "config.json"

#: Scratch folder for freshly captured (not yet confirmed) photos.
TEMP_DIR: Path = BASE_DIR / ".temp"

#: Bundled images / icons.
ASSETS_DIR: Path = BASE_DIR / "assets"


def ensure_directories() -> None:
    """Create every directory the app expects to exist. Safe to call repeatedly."""
    for directory in (DATASET_DIR, TEMP_DIR, ASSETS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
