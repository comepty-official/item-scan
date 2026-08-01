"""Grid tile used by the folder screen to display one dataset image."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from kivy.metrics import dp
from kivy.uix.image import Image
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel


class ImageTile(MDCard):
    """Thumbnail + filename + move/delete/edit actions for a single image."""

    def __init__(
        self,
        image_path: Path,
        on_move: Callable[[Path], None],
        on_delete: Callable[[Path], None],
        on_edit: Callable[[Path], None],
        **kwargs,
    ):
        super().__init__(
            style="outlined",
            radius=dp(18),
            padding=dp(8),
            size_hint_y=None,
            height=dp(210),
            **kwargs,
        )
        self.image_path = image_path

        layout = MDBoxLayout(orientation="vertical", spacing=dp(6))
        layout.add_widget(Image(source=str(image_path), fit_mode="cover", size_hint_y=1))
        layout.add_widget(
            MDLabel(
                text=image_path.name,
                font_style="Label",
                role="small",
                halign="center",
                shorten=True,
                size_hint_y=None,
                height=dp(18),
                theme_text_color="Custom",
                text_color=self.theme_cls.onSurfaceVariantColor,
            )
        )

        actions = MDBoxLayout(size_hint_y=None, height=dp(40), spacing=dp(2))
        for icon, callback in (
            ("pencil-outline", on_edit),
            ("folder-move-outline", on_move),
            ("trash-can-outline", on_delete),
        ):
            btn = MDIconButton(icon=icon, style="standard")
            btn.bind(on_release=lambda _w, cb=callback: cb(self.image_path))
            actions.add_widget(btn)
        layout.add_widget(actions)

        self.add_widget(layout)
