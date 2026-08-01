"""Pending screen - records whose image could not be written to the dataset."""

from __future__ import annotations

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

from screens.base import BaseScreen
from utils.helpers import pretty_date
from widgets.common import button, confirm_dialog, toast, top_bar


class PendingScreen(BaseScreen):
    """Lists queued items and lets the admin retry or drop them."""

    def build_ui(self) -> None:
        root = MDBoxLayout(orientation="vertical")
        root.add_widget(
            top_bar(
                "Pending",
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
            spacing=dp(10),
            padding=(dp(16), 0, dp(16), dp(16)),
        )
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)

        self.retry_all_row = MDBoxLayout(adaptive_height=True, padding=(dp(16), 0, dp(16), dp(16)))
        root.add_widget(self.retry_all_row)
        self.add_widget(root)

    def on_pre_enter(self, *args) -> None:
        """Rebuild the queue view."""
        self.refresh()

    def refresh(self) -> None:
        """Re-read ``pending_db.json`` and rebuild the cards."""
        self.list_box.clear_widgets()
        self.retry_all_row.clear_widgets()
        records = self.app.pending.records
        self.summary.text = f"{len(records)} item{'s' if len(records) != 1 else ''} waiting"

        if not records:
            self.list_box.add_widget(
                MDLabel(
                    text="Nothing pending. Every capture was saved successfully.",
                    halign="center",
                    font_style="Body",
                    role="medium",
                    adaptive_height=True,
                    padding=(0, dp(40)),
                )
            )
            return

        for record in records:
            self.list_box.add_widget(self._card(record))

        self.retry_all_row.add_widget(
            button("Retry all", self.retry_all, icon="refresh", style="filled", size_hint_x=1)
        )

    def _card(self, record: dict) -> MDCard:
        """Build one pending card with retry / delete buttons."""
        card = MDCard(style="outlined", radius=dp(18), padding=dp(12), size_hint_y=None, height=dp(132))
        layout = MDBoxLayout(orientation="vertical", spacing=dp(2))
        layout.add_widget(
            MDLabel(text=record.get("name") or "Unlabeled", font_style="Title", role="small", adaptive_height=True)
        )
        layout.add_widget(
            MDLabel(
                text=f"Reason: {record.get('error', 'unknown')}",
                font_style="Body",
                role="small",
                adaptive_height=True,
                shorten=True,
                theme_text_color="Custom",
                text_color=self.theme_cls.errorColor,
            )
        )
        layout.add_widget(
            MDLabel(
                text=f"Queued {pretty_date(record.get('date', ''))}",
                font_style="Label",
                role="small",
                adaptive_height=True,
                theme_text_color="Custom",
                text_color=self.theme_cls.onSurfaceVariantColor,
            )
        )

        actions = MDBoxLayout(adaptive_height=True, spacing=dp(4))
        retry = MDIconButton(icon="refresh", style="tonal")
        retry.bind(on_release=lambda *_: self.retry(record))
        remove = MDIconButton(icon="trash-can-outline", style="standard")
        remove.bind(on_release=lambda *_: self.remove(record))
        actions.add_widget(retry)
        actions.add_widget(remove)
        layout.add_widget(actions)

        card.add_widget(layout)
        return card

    # ---------------------------------------------------------------- actions
    def retry(self, record: dict) -> None:
        """Attempt to move a queued item into the dataset again."""
        if self.app.retry_pending(record):
            toast("Saved successfully")
        else:
            toast("Still failing - the source image may be gone.")
        self.refresh()

    def retry_all(self) -> None:
        """Retry every queued item, reporting how many succeeded."""
        saved = sum(1 for record in self.app.pending.records if self.app.retry_pending(record))
        toast(f"{saved} item(s) saved")
        self.refresh()

    def remove(self, record: dict) -> None:
        """Drop an item from the queue."""

        def _confirm() -> None:
            self.app.pending.delete(record["id"])
            toast("Removed from pending")
            self.refresh()

        confirm_dialog("Remove item?", "This queued capture will be discarded.", _confirm)
