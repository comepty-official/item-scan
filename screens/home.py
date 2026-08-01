"""Home screen - entry point with the four main actions."""

from __future__ import annotations

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard

from screens.base import BaseScreen
from widgets.common import StatCard, icon_glyph, top_bar


class HomeScreen(BaseScreen):
    """Material 3 dashboard with dataset statistics and navigation cards."""

    def build_ui(self) -> None:
        root = MDBoxLayout(orientation="vertical")
        root.add_widget(top_bar("FoodAI Dataset Builder"))

        scroll = MDScrollView(do_scroll_x=False)
        body = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            padding=(dp(16), dp(8), dp(16), dp(24)),
            spacing=dp(14),
        )

        hero = MDCard(
            style="elevated",
            radius=dp(24),
            padding=dp(16),
            size_hint_y=None,
            height=dp(150),
        )
        hero_content = MDBoxLayout(orientation="vertical", spacing=dp(6), adaptive_height=True)
        hero_content.add_widget(
            MDLabel(
                text="Quick start",
                font_style="Label",
                role="medium",
                adaptive_height=True,
                theme_text_color="Custom",
                text_color=self.theme_cls.primaryColor,
            )
        )
        hero_content.add_widget(
            MDLabel(
                text="Capture Food",
                font_style="Title",
                role="large",
                adaptive_height=True,
            )
        )
        hero_content.add_widget(
            MDLabel(
                text="Capture food photos, build your local dataset and keep everything tidy offline.",
                font_style="Body",
                role="medium",
                adaptive_height=True,
                theme_text_color="Custom",
                text_color=self.theme_cls.onSurfaceVariantColor,
            )
        )
        hero.add_widget(hero_content)
        body.add_widget(hero)

        body.add_widget(
            MDLabel(
                text="Start here",
                font_style="Label",
                role="medium",
                adaptive_height=True,
                theme_text_color="Custom",
                text_color=self.theme_cls.onSurfaceVariantColor,
            )
        )

        # --- quick launcher ----------------------------------------------
        launcher = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(12))
        launcher.add_widget(
            self._launcher_card("camera", "Capture Food", "Take a fresh photo", lambda: self.app.open_camera())
        )
        launcher.add_widget(
            self._launcher_card("image-multiple", "Food Library", "Browse saved folders", lambda: self.app.switch("library"))
        )
        launcher.add_widget(
            self._launcher_card("cog", "Settings", "Theme, camera and USDA", lambda: self.app.switch("settings"))
        )
        body.add_widget(launcher)

        body.add_widget(
            MDLabel(
                text="Dataset overview",
                font_style="Label",
                role="medium",
                adaptive_height=True,
                theme_text_color="Custom",
                text_color=self.theme_cls.onSurfaceVariantColor,
            )
        )

        # --- statistics -----------------------------------------------------
        self.stats = MDGridLayout(cols=2, spacing=dp(10), adaptive_height=True)
        body.add_widget(self.stats)

        scroll.add_widget(body)
        root.add_widget(scroll)
        self.add_widget(root)

    def _launcher_card(self, icon: str, title: str, subtitle: str, callback) -> MDCard:
        """Create a polished launcher card with an icon and short description."""
        card = MDCard(
            style="filled",
            ripple_behavior=True,
            padding=dp(16),
            radius=dp(22),
            size_hint_y=None,
            height=dp(118),
        )
        card.bind(on_release=lambda *_: callback())
        box = MDBoxLayout(orientation="horizontal", spacing=dp(14), adaptive_height=True)
        icon_label = MDLabel(
            text=icon_glyph(icon),
            font_name="Icons",
            font_size=dp(26),
            theme_text_color="Custom",
            text_color=self.theme_cls.primaryColor,
            size_hint_x=None,
            width=dp(42),
        )
        text_box = MDBoxLayout(orientation="vertical", spacing=dp(2), adaptive_height=True)
        text_box.add_widget(MDLabel(text=title, font_style="Title", role="medium", adaptive_height=True))
        text_box.add_widget(MDLabel(text=subtitle, font_style="Body", role="small", adaptive_height=True, theme_text_color="Custom", text_color=self.theme_cls.onSurfaceVariantColor))
        box.add_widget(icon_label)
        box.add_widget(text_box)
        box.add_widget(MDLabel(text="›", font_name="Icons", font_size=dp(24), theme_text_color="Custom", text_color=self.theme_cls.onSurfaceVariantColor, size_hint_x=None, width=dp(20)))
        card.add_widget(box)
        return card

    def on_pre_enter(self, *args) -> None:
        """Refresh the statistic cards every time the screen is shown."""
        self.stats.clear_widgets()
        folders = self.app.storage.folders()
        self.stats.add_widget(StatCard(str(len(folders)), "Food classes"))
        self.stats.add_widget(StatCard(str(self.app.storage.total_images()), "Images"))
        self.stats.add_widget(StatCard(str(len(self.app.pending.records)), "Pending"))
