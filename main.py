"""
FoodAI Dataset Builder - application entry point.

An offline-first **admin tool** used to build an image dataset for a future food
recognition model. Built with:

* Python 3.13
* Kivy 2.3.1
* KivyMD 2.0.1.dev0 (Material 3 API only - no deprecated widgets anywhere)

Run with ``python main.py``.
"""

from __future__ import annotations

from pathlib import Path

from kivy.core.window import Window
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

from database.db import FoodDatabase, PendingDatabase
from screens.camera_screen import CameraScreen
from screens.details import DetailsScreen
from screens.folder import FolderScreen
from screens.home import HomeScreen
from screens.library import LibraryScreen
from screens.pending import PendingScreen
from screens.settings import SettingsScreen
from services.prediction_service import FoodPredictionService
from services.usda_service import USDAService
from storage.file_manager import DatasetStorage
from utils.config import AppConfig
from utils.helpers import folder_name, now_iso
from utils.paths import ensure_directories
from widgets.common import toast


class FoodAIApp(MDApp):
    """The single application object; also acts as the service container."""

    # ------------------------------------------------------------------ setup
    def build(self):
        """Create the services, theme and screen manager."""
        ensure_directories()

        # --- services -------------------------------------------------------
        self.config_store = AppConfig()
        self.db = FoodDatabase()
        self.pending = PendingDatabase()
        self.storage = DatasetStorage()
        self.usda = USDAService(self.config_store.get("usda_api_key"))
        self.predictor = FoodPredictionService(self.storage.root)

        # --- Material 3 theme ----------------------------------------------
        self.title = "FoodAI Dataset Builder"
        self.icon = str(Path(__file__).parent / "assets" / "icons" / "icon.png")
        Window.set_icon(self.icon)
        self.theme_cls.theme_style = self.config_store.get("theme_style")
        self.theme_cls.primary_palette = self.config_store.get("primary_palette")
        self.theme_cls.dynamic_scheme_name = "TONAL_SPOT"

        # A phone-like window makes the layout easy to review on desktop.
        Window.minimum_width, Window.minimum_height = dp(360), dp(600)

        # --- screens --------------------------------------------------------
        self.manager = MDScreenManager()
        self.screens = {
            "home": HomeScreen(name="home"),
            "camera": CameraScreen(name="camera"),
            "details": DetailsScreen(name="details"),
            "library": LibraryScreen(name="library"),
            "folder": FolderScreen(name="folder"),
            "pending": PendingScreen(name="pending"),
            "settings": SettingsScreen(name="settings"),
        }
        for screen in self.screens.values():
            self.manager.add_widget(screen)
        self._apply_glass_theme()
        self.manager.current = "home"
        return self.manager

    # ------------------------------------------------------------ navigation
    def switch(self, name: str, direction: str = "left") -> None:
        """Show another screen with a slide transition."""
        self.manager.transition.direction = direction
        self.manager.current = name

    def open_camera(self) -> None:
        """Go to the capture screen."""
        self.switch("camera")

    def open_details(self, image_path: Path, suggested_label: str | None = None) -> None:
        """Go to the details form for a freshly captured photo."""
        self.screens["details"].load(image_path, suggested_label=suggested_label)
        self.switch("details")

    def open_folder(self, folder: str) -> None:
        """Open one dataset folder."""
        self.screens["folder"].load(folder)
        self.switch("folder")

    # ----------------------------------------------------------------- theme
    def set_theme(self, dark: bool) -> None:
        """Switch between the light and dark Material 3 scheme."""
        style = "Dark" if dark else "Light"
        self.theme_cls.theme_style = style
        self.config_store.set("theme_style", style)
        self._apply_glass_theme()

    def _apply_glass_theme(self) -> None:
        """No-op kept for compatibility after removing the glass toggle."""
        return

    def set_palette(self, palette: str) -> None:
        """Change the seed colour of the Material 3 scheme."""
        self.theme_cls.primary_palette = palette
        self.config_store.set("primary_palette", palette)

    # ------------------------------------------------------------ dataset io
    def save_capture(self, image_path: Path, name: str, description: str) -> None:
        """Copy the capture into the dataset and insert a database record.

        Any failure (permissions, missing file, full disk) is queued in
        *Pending* instead of being lost, so the admin can retry later.
        """
        label = name.strip() or "Unlabeled"
        try:
            target = self.storage.save_image(Path(image_path), label)
        except Exception as error:  # noqa: BLE001 - anything must land in Pending
            self.pending.insert(
                name=label,
                folder=folder_name(label),
                source=str(image_path),
                description=description,
                status="pending",
                error=str(error),
                date=now_iso(),
            )
            toast("Save failed - queued in Pending", str(error))
            self.switch("pending")
            return

        record = self.db.insert(
            name=label,
            folder=folder_name(label),
            image=self.db.relative(target),
            description=description,
            status="saved",
        )
        # The scratch capture is no longer needed once it is in the dataset.
        Path(image_path).unlink(missing_ok=True)
        toast(f"Saved as {target.name}", f"Record #{record['id']} in {folder_name(label)}")
        self.open_camera()

    def retry_pending(self, record: dict) -> bool:
        """Try to move one pending item into the dataset. Returns success."""
        source = Path(record.get("source", ""))
        label = record.get("name") or "Unlabeled"
        if not source.is_file():
            self.pending.update(record["id"], error="Source image no longer exists")
            return False
        try:
            target = self.storage.save_image(source, label)
        except Exception as error:  # noqa: BLE001
            self.pending.update(record["id"], error=str(error))
            return False

        self.db.insert(
            name=label,
            folder=folder_name(label),
            image=self.db.relative(target),
            description=record.get("description", ""),
            status="saved",
        )
        source.unlink(missing_ok=True)
        self.pending.delete(record["id"])
        return True


if __name__ == "__main__":
    FoodAIApp().run()
