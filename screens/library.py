"""Food Library - every dataset folder with its image count."""

from __future__ import annotations

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import (
    MDListItem,
    MDListItemHeadlineText,
    MDListItemLeadingIcon,
    MDListItemSupportingText,
    MDListItemTrailingSupportingText,
)
from kivymd.uix.scrollview import MDScrollView

from screens.base import BaseScreen
from utils.helpers import display_name
from widgets.common import top_bar


class LibraryScreen(BaseScreen):
    """Lists ``FoodAI_Dataset/*`` folders; tapping one opens the folder screen."""

    def build_ui(self) -> None:
        root = MDBoxLayout(orientation="vertical")
        root.add_widget(
            top_bar(
                "Food Library",
                on_back=lambda: self.app.switch("home"),
                actions=[("refresh", self.refresh)],
            )
        )

        self.summary = MDLabel(
            text="",
            font_style="Body",
            role="small",
            adaptive_height=True,
            theme_text_color="Custom",
            text_color=self.theme_cls.onSurfaceVariantColor,
        )
        root.add_widget(MDBoxLayout(self.summary, adaptive_height=True, padding=(dp(16), dp(4))))

        scroll = MDScrollView(do_scroll_x=False)
        self.list_box = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            padding=(dp(8), 0, dp(8), dp(24)),
        )
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *args) -> None:
        """Always rebuild the list - folders can change while the app runs."""
        self.refresh()

    def refresh(self) -> None:
        """Re-read the dataset directory and rebuild the list."""
        self.list_box.clear_widgets()
        folders = self.app.storage.folders()
        self.summary.text = (
            f"{len(folders)} food classes - {self.app.storage.total_images()} images total"
        )

        if not folders:
            self.list_box.add_widget(
                MDLabel(
                    text="No food saved yet.\nUse 'Capture Food' on the home screen to start.",
                    halign="center",
                    font_style="Body",
                    role="medium",
                    adaptive_height=True,
                    padding=(0, dp(40)),
                )
            )
            return

        for folder, count in folders:
            item = MDListItem(
                MDListItemLeadingIcon(icon="folder-image"),
                MDListItemHeadlineText(text=display_name(folder)),
                MDListItemSupportingText(text=f"{count} image{'s' if count != 1 else ''}"),
                MDListItemTrailingSupportingText(text=str(count)),
            )
            item.bind(on_release=lambda _w, value=folder: self.app.open_folder(value))
            self.list_box.add_widget(item)
