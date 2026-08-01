"""Simple offline file picker dialog (used to import an existing photo)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from kivy.metrics import dp
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.widget import Widget
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogHeadlineText,
)

from widgets.common import button, toast


def open_file_picker(on_select: Callable[[str], None], start_path: str | None = None) -> MDDialog:
    """Show a dialog with a Kivy file chooser filtered to image files."""
    chooser = FileChooserIconView(
        path=start_path or str(Path.home()),
        filters=["*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"],
        size_hint_y=None,
        height=dp(320),
    )
    dialog = MDDialog(
        MDDialogHeadlineText(text="Import a photo"),
        MDDialogContentContainer(chooser, orientation="vertical"),
        size_hint_x=0.95,
    )
    buttons = MDDialogButtonContainer(spacing=dp(8))
    buttons.add_widget(Widget())
    buttons.add_widget(button("Cancel", dialog.dismiss, style="text"))

    def _use() -> None:
        if not chooser.selection:
            toast("Select an image first.")
            return
        dialog.dismiss()
        on_select(chooser.selection[0])

    buttons.add_widget(button("Use file", _use, style="filled"))
    dialog.add_widget(buttons)
    dialog.open()
    return dialog
