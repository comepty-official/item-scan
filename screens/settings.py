"""Settings screen - theme, camera, rotation, USDA key and dataset info."""

from __future__ import annotations

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.divider import MDDivider
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.textfield import MDTextField, MDTextFieldHelperText, MDTextFieldHintText

from screens.base import BaseScreen
from services.network import has_internet
from utils.paths import DATASET_DIR, DB_PATH
from widgets.common import button, toast, top_bar

#: Palettes offered to the admin (all valid KivyMD 2.0 Material 3 palettes).
PALETTES = ["Green", "Teal", "Blue", "Orange", "Red", "Brown"]


class SettingsScreen(BaseScreen):
    """Edits :class:`~utils.config.AppConfig` values and applies them live."""

    def build_ui(self) -> None:
        root = MDBoxLayout(orientation="vertical")
        root.add_widget(top_bar("Settings", on_back=lambda: self.app.switch("home")))

        scroll = MDScrollView(do_scroll_x=False)
        body = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            padding=(dp(16), dp(8), dp(16), dp(24)),
            spacing=dp(14),
        )

        # --- theme ----------------------------------------------------------
        body.add_widget(self._section("Appearance"))
        theme_row = MDBoxLayout(adaptive_height=True, spacing=dp(12))
        theme_row.add_widget(
            MDLabel(text="Dark theme", font_style="Body", role="large", adaptive_height=True)
        )
        self.theme_switch = MDSwitch(pos_hint={"center_y": 0.5})
        self.theme_switch.bind(active=lambda _w, value: self.app.set_theme(value))
        theme_row.add_widget(self.theme_switch)
        body.add_widget(theme_row)

        self.palette_box = MDBoxLayout(adaptive_height=True, spacing=dp(8))
        palette_scroll = MDScrollView(do_scroll_y=False, size_hint_y=None, height=dp(48))
        palette_scroll.add_widget(self.palette_box)
        body.add_widget(palette_scroll)

        body.add_widget(MDDivider())

        # --- camera ---------------------------------------------------------
        body.add_widget(self._section("Camera"))
        self.camera_field = MDTextField(
            MDTextFieldHintText(text="Camera index"),
            MDTextFieldHelperText(text="0 is the default device camera", mode="persistent"),
            mode="outlined",
            input_filter="int",
            size_hint_x=1,
        )
        body.add_widget(self.camera_field)

        self.rotation_label = MDLabel(text="", font_style="Body", role="medium", adaptive_height=True)
        body.add_widget(self.rotation_label)
        rotation_row = MDBoxLayout(adaptive_height=True, spacing=dp(8))
        for degrees in (0, 90, 180, 270):
            rotation_row.add_widget(
                button(f"{degrees}", lambda d=degrees: self.set_rotation(d), style="outlined")
            )
        body.add_widget(rotation_row)

        body.add_widget(MDDivider())

        # --- USDA -----------------------------------------------------------
        body.add_widget(self._section("USDA FoodData Central"))
        self.usda_field = MDTextField(
            MDTextFieldHintText(text="USDA API key"),
            MDTextFieldHelperText(text="DEMO_KEY works for light testing", mode="persistent"),
            mode="outlined",
            size_hint_x=1,
        )
        body.add_widget(self.usda_field)
        self.network_label = MDLabel(text="", font_style="Label", role="large", adaptive_height=True)
        body.add_widget(self.network_label)

        body.add_widget(button("Save settings", self.save, icon="content-save-outline", style="filled", size_hint_x=1))

        body.add_widget(MDDivider())

        # --- storage info ---------------------------------------------------
        body.add_widget(self._section("Storage"))
        info = MDCard(style="filled", radius=dp(18), padding=dp(14), adaptive_height=True)
        info_box = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(4))
        info_box.add_widget(
            MDLabel(text=f"Dataset: {DATASET_DIR}", font_style="Body", role="small", adaptive_height=True)
        )
        info_box.add_widget(
            MDLabel(text=f"Database: {DB_PATH}", font_style="Body", role="small", adaptive_height=True)
        )
        info_box.add_widget(
            MDLabel(
                text="Everything is stored locally - no cloud, no account needed.",
                font_style="Label",
                role="small",
                adaptive_height=True,
                theme_text_color="Custom",
                text_color=self.theme_cls.onSurfaceVariantColor,
            )
        )
        info.add_widget(info_box)
        body.add_widget(info)

        scroll.add_widget(body)
        root.add_widget(scroll)
        self.add_widget(root)

    def _section(self, title: str) -> MDLabel:
        """Section heading label."""
        return MDLabel(
            text=title,
            font_style="Title",
            role="medium",
            adaptive_height=True,
            theme_text_color="Custom",
            text_color=self.theme_cls.primaryColor,
        )

    # ---------------------------------------------------------------- loading
    def on_pre_enter(self, *args) -> None:
        """Fill the form with the current configuration."""
        config = self.app.config_store
        self.theme_switch.active = config.get("theme_style") == "Dark"
        self.camera_field.text = str(config.get("camera_index", 0))
        self.usda_field.text = str(config.get("usda_api_key", "DEMO_KEY"))
        self.rotation_label.text = f"Preview rotation: {config.get('preview_rotation', 0)} degrees"
        self.network_label.text = "Online" if has_internet() else "Offline (manual tags only)"

        self.palette_box.clear_widgets()
        active = config.get("primary_palette")
        for palette in PALETTES:
            chip = MDChip(MDChipText(text=palette), type="filter", active=palette == active)
            chip.bind(on_release=lambda _w, value=palette: self.set_palette(value))
            self.palette_box.add_widget(chip)

    # ---------------------------------------------------------------- actions
    def set_palette(self, palette: str) -> None:
        """Apply and persist a new Material 3 palette."""
        self.app.set_palette(palette)
        toast(f"{palette} palette applied")
        self.on_pre_enter()

    def set_rotation(self, degrees: int) -> None:
        """Persist the camera preview rotation."""
        self.app.config_store.set("preview_rotation", degrees)
        self.rotation_label.text = f"Preview rotation: {degrees} degrees"
        toast(f"Camera rotation set to {degrees} degrees")

    def save(self) -> None:
        """Store the camera index and USDA key."""
        config = self.app.config_store
        config.set("camera_index", int(self.camera_field.text or 0))
        config.set("usda_api_key", self.usda_field.text.strip() or "DEMO_KEY")
        self.app.usda.api_key = config.get("usda_api_key")
        toast("Settings saved")
