"""Food details screen - label, description and (optional) USDA suggestion."""

from __future__ import annotations

from pathlib import Path
from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.image import Image
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.divider import MDDivider
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemLeadingIcon
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField, MDTextFieldHelperText, MDTextFieldHintText

from screens.base import BaseScreen
from services.network import has_internet
from utils.helpers import display_name
from widgets.common import button, toast, top_bar


class DetailsScreen(BaseScreen):
    """Collects the food label + description before the image is saved."""

    def build_ui(self) -> None:
        self.image_path: Path | None = None
        self.online = False

        root = MDBoxLayout(orientation="vertical")
        root.add_widget(top_bar("Food Details", on_back=lambda: self.app.switch("camera")))

        scroll = MDScrollView(do_scroll_x=False)
        body = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            padding=(dp(16), dp(8), dp(16), dp(24)),
            spacing=dp(14),
        )

        # --- captured photo -------------------------------------------------
        preview_card = MDCard(style="outlined", radius=dp(20), padding=dp(6), size_hint_y=None, height=dp(220))
        self.preview = Image(fit_mode="contain")
        preview_card.add_widget(self.preview)
        body.add_widget(preview_card)

        # --- free-form label ------------------------------------------------
        self.name_field = MDTextField(
            MDTextFieldHintText(text="Food name (optional - any tag)"),
            MDTextFieldHelperText(text="Examples: Burger, Fried Rice, Jollof Rice, Ice Cream", mode="persistent"),
            mode="outlined",
            size_hint_x=1,
        )
        body.add_widget(self.name_field)

        # --- quick labels from folders that already exist -------------------
        body.add_widget(
            MDLabel(
                text="Existing labels",
                font_style="Label",
                role="large",
                adaptive_height=True,
                theme_text_color="Custom",
                text_color=self.theme_cls.onSurfaceVariantColor,
            )
        )
        self.chip_box = MDBoxLayout(adaptive_height=True, spacing=dp(8), padding=(0, 0, 0, dp(4)))
        chip_scroll = MDScrollView(do_scroll_y=False, size_hint_y=None, height=dp(48))
        chip_scroll.add_widget(self.chip_box)
        body.add_widget(chip_scroll)

        # --- description ----------------------------------------------------
        self.description_field = MDTextField(
            MDTextFieldHintText(text="Description"),
            mode="outlined",
            multiline=True,
            size_hint_x=1,
        )
        body.add_widget(self.description_field)

        body.add_widget(MDDivider())

        # --- USDA lookup ----------------------------------------------------
        self.usda_button = button(
            "Search USDA FoodData Central",
            self.search_usda,
            icon="cloud-search-outline",
            style="tonal",
            size_hint_x=1,
        )
        body.add_widget(self.usda_button)

        self.usda_status = MDLabel(
            text="",
            font_style="Body",
            role="small",
            adaptive_height=True,
            theme_text_color="Custom",
            text_color=self.theme_cls.onSurfaceVariantColor,
        )
        body.add_widget(self.usda_status)

        self.suggestions = MDBoxLayout(orientation="vertical", adaptive_height=True)
        body.add_widget(self.suggestions)

        # --- save -----------------------------------------------------------
        row = MDBoxLayout(adaptive_height=True, spacing=dp(10))
        row.add_widget(button("Discard", self.discard, icon="close", style="outlined", size_hint_x=0.4))
        row.add_widget(button("Save to dataset", self.save, icon="content-save-outline", style="filled", size_hint_x=0.6))
        body.add_widget(row)

        scroll.add_widget(body)
        root.add_widget(scroll)
        self.add_widget(root)

    # --------------------------------------------------------------- loading
    def load(self, image_path: Path, suggested_label: str | None = None) -> None:
        """Show a freshly captured photo and reset the form."""
        self.image_path = image_path
        self.preview.source = str(image_path)
        self.preview.reload()
        self.name_field.text = ""
        self.description_field.text = ""
        self.suggestions.clear_widgets()

        if suggested_label:
            self.name_field.text = suggested_label
            self.usda_status.text = f"Looks like {suggested_label}. Checking USDA hints..."
            self._load_usda_suggestions(suggested_label)
            return

        try:
            prediction = self.app.predictor.predict_from_path(image_path)
        except Exception:
            prediction = None
        if prediction and prediction.label:
            self.name_field.text = prediction.label
            self.usda_status.text = f"Looks like {prediction.label}. Checking USDA hints..."
            self._load_usda_suggestions(prediction.label)
        else:
            self.usda_status.text = "I don't know this one yet — add the name manually or search USDA."

    def on_pre_enter(self, *args) -> None:
        """Refresh quick labels and check connectivity for the USDA button."""
        self.chip_box.clear_widgets()
        for folder, count in self.app.storage.folders():
            label = display_name(folder)
            chip = MDChip(MDChipText(text=f"{label} ({count})"), type="suggestion")
            chip.bind(on_release=lambda _w, value=label: self.set_name(value))
            self.chip_box.add_widget(chip)

        self.online = has_internet()
        self.usda_button.disabled = not self.online
        self.usda_status.text = (
            "Online - USDA suggestions available."
            if self.online
            else "Offline - type the food name manually (any tag is allowed)."
        )

    def set_name(self, value: str) -> None:
        """Fill the name field from a chip or a USDA suggestion."""
        self.name_field.text = value

    def _load_usda_suggestions(self, label: str) -> None:
        """Query USDA in the background and reuse the first result as a hint."""

        def worker() -> None:
            try:
                results = self.app.usda.search(label)
            except RuntimeError as error:
                Clock.schedule_once(lambda *_: self.usda_failed(str(error)), 0)
                return
            Clock.schedule_once(lambda *_: self._show_usda_hint(results, label), 0)

        Thread(target=worker, daemon=True).start()

    def _show_usda_hint(self, results: list[str], label: str) -> None:
        """Apply the first USDA description as a helpful detail hint."""
        self.suggestions.clear_widgets()
        if not results:
            self.usda_status.text = f"USDA didn't have a strong match for {label}; you can enter it manually."
            return
        top_result = results[0]
        self.usda_status.text = f"USDA hint: {top_result}"
        if not self.description_field.text.strip():
            self.description_field.text = f"Likely {label}. {top_result}"
        for description in results[:3]:
            item = MDListItem(
                MDListItemLeadingIcon(icon="food-apple-outline"),
                MDListItemHeadlineText(text=description),
            )
            item.bind(on_release=lambda _w, value=description: self.set_name(value))
            self.suggestions.add_widget(item)

    # ------------------------------------------------------------ USDA search
    def search_usda(self) -> None:
        """Query USDA in a background thread so the UI never freezes."""
        query = self.name_field.text.strip()
        if not query:
            toast("Type something to search for first.")
            return
        self.usda_status.text = "Searching USDA..."
        self.suggestions.clear_widgets()

        def worker() -> None:
            try:
                results = self.app.usda.search(query)
                Clock.schedule_once(lambda *_: self.show_suggestions(results), 0)
            except RuntimeError as error:
                message = str(error)
                Clock.schedule_once(lambda *_: self.usda_failed(message), 0)

        Thread(target=worker, daemon=True).start()

    def show_suggestions(self, results: list[str]) -> None:
        """Render USDA results as a tappable list."""
        self.suggestions.clear_widgets()
        if not results:
            self.usda_status.text = "No USDA match - keep your manual tag."
            return
        self.usda_status.text = "Tap a suggestion to use it as the food name."
        for description in results:
            item = MDListItem(
                MDListItemLeadingIcon(icon="food-apple-outline"),
                MDListItemHeadlineText(text=description),
            )
            item.bind(on_release=lambda _w, value=description: self.set_name(value))
            self.suggestions.add_widget(item)

    def usda_failed(self, message: str) -> None:
        """Show a friendly message when the lookup could not complete."""
        self.usda_status.text = "USDA unavailable - continue offline."
        toast("USDA lookup failed", message)

    # ----------------------------------------------------------------- saving
    def save(self) -> None:
        """Persist the image + record through the app-level save routine."""
        if self.image_path is None:
            toast("Nothing to save.")
            return
        self.app.save_capture(
            image_path=self.image_path,
            name=self.name_field.text.strip(),
            description=self.description_field.text.strip(),
        )

    def discard(self) -> None:
        """Throw the capture away and go back to the camera."""
        if self.image_path is not None:
            Path(self.image_path).unlink(missing_ok=True)
            self.image_path = None
        toast("Capture discarded.")
        self.app.open_camera()
