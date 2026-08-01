"""Folder screen - manage the images of a single food class."""

from __future__ import annotations

from pathlib import Path

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

from screens.base import BaseScreen
from utils.helpers import display_name
from widgets.common import confirm_dialog, prompt_dialog, toast, top_bar
from widgets.image_tile import ImageTile


class FolderScreen(BaseScreen):
    """Grid of images with rename / move / delete / edit-description actions."""

    def build_ui(self) -> None:
        self.folder = ""

        root = MDBoxLayout(orientation="vertical")
        self.bar_holder = MDBoxLayout(adaptive_height=True)
        root.add_widget(self.bar_holder)

        self.subtitle = MDLabel(
            text="",
            font_style="Body",
            role="small",
            adaptive_height=True,
            theme_text_color="Custom",
            text_color=self.theme_cls.onSurfaceVariantColor,
        )
        root.add_widget(MDBoxLayout(self.subtitle, adaptive_height=True, padding=(dp(16), dp(4))))

        scroll = MDScrollView(do_scroll_x=False)
        self.grid = MDGridLayout(
            cols=2, spacing=dp(10), adaptive_height=True, padding=(dp(16), 0, dp(16), dp(24))
        )
        scroll.add_widget(self.grid)
        root.add_widget(scroll)
        self.add_widget(root)

    # --------------------------------------------------------------- loading
    def load(self, folder: str) -> None:
        """Remember which folder to display."""
        self.folder = folder

    def on_pre_enter(self, *args) -> None:
        """Rebuild the app bar (title changes) and the image grid."""
        self.bar_holder.clear_widgets()
        self.bar_holder.add_widget(
            top_bar(
                display_name(self.folder),
                on_back=lambda: self.app.switch("library"),
                actions=[
                    ("form-textbox", self.rename_folder),
                    ("delete-outline", self.delete_folder),
                ],
            )
        )
        self.refresh()

    def refresh(self) -> None:
        """Reload the images from disk."""
        self.grid.clear_widgets()
        images = self.app.storage.images(self.folder)
        self.subtitle.text = f"{len(images)} image{'s' if len(images) != 1 else ''} in this class"

        if not images:
            self.grid.add_widget(
                MDLabel(
                    text="This folder is empty.",
                    font_style="Body",
                    role="medium",
                    adaptive_height=True,
                )
            )
            return

        for image in images:
            self.grid.add_widget(
                ImageTile(
                    image,
                    on_move=self.move_image,
                    on_delete=self.delete_image,
                    on_edit=self.edit_description,
                )
            )

    # ------------------------------------------------------- folder actions
    def rename_folder(self) -> None:
        """Rename the food class (folder + filenames + database records)."""

        def _submit(new_label: str) -> None:
            if not new_label:
                toast("Name cannot be empty.")
                return
            try:
                new_folder = self.app.storage.rename_folder(self.folder, new_label)
            except RuntimeError as error:
                toast("Rename failed", str(error))
                return
            self.app.db.rename_folder(self.folder, new_folder, new_label)
            self.folder = new_folder
            toast(f"Renamed to {display_name(new_folder)}")
            self.on_pre_enter()

        prompt_dialog("Rename food", "New food name", _submit, initial=display_name(self.folder))

    def delete_folder(self) -> None:
        """Delete the whole class after confirmation."""

        def _confirm() -> None:
            self.app.storage.delete_folder(self.folder)
            self.app.db.delete_where_folder(self.folder)
            toast(f"Deleted {display_name(self.folder)}")
            self.app.switch("library")

        confirm_dialog(
            "Delete folder?",
            f"'{display_name(self.folder)}' and all of its images will be removed permanently.",
            _confirm,
        )

    # -------------------------------------------------------- image actions
    def move_image(self, image: Path) -> None:
        """Move one image into a different (possibly new) food class."""

        def _submit(new_label: str) -> None:
            if not new_label:
                toast("Name cannot be empty.")
                return
            old_relative = self.app.db.relative(image)
            try:
                target = self.app.storage.move_image(image, new_label)
            except OSError as error:
                toast("Move failed", str(error))
                return
            from utils.helpers import folder_name

            self.app.db.move_image(
                old_relative, self.app.db.relative(target), folder_name(new_label), new_label
            )
            toast(f"Moved to {new_label}")
            self.refresh()

        prompt_dialog("Move image", "Target food name", _submit, submit_text="Move")

    def delete_image(self, image: Path) -> None:
        """Delete one image (file + record)."""

        def _confirm() -> None:
            relative = self.app.db.relative(image)
            self.app.storage.delete_image(image)
            record = self.app.db.by_image(relative)
            if record is not None:
                self.app.db.delete(record["id"])
            toast("Image deleted")
            self.refresh()

        confirm_dialog("Delete image?", image.name, _confirm)

    def edit_description(self, image: Path) -> None:
        """Edit the description stored in ``food_db.json`` for one image."""
        relative = self.app.db.relative(image)
        record = self.app.db.by_image(relative)
        if record is None:
            # The image exists on disk but has no record yet (e.g. copied in
            # manually) - create one so the description can be stored.
            record = self.app.db.insert(
                name=display_name(self.folder),
                folder=self.folder,
                image=relative,
                description="",
                status="saved",
            )

        def _submit(text: str) -> None:
            self.app.db.update(record["id"], description=text)
            toast("Description updated")

        prompt_dialog(
            "Edit description",
            "Description",
            _submit,
            initial=record.get("description", ""),
            multiline=True,
        )
