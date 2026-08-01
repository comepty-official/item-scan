"""Common base class for every screen."""

from __future__ import annotations

from kivy.app import App
from kivymd.uix.screen import MDScreen


class BaseScreen(MDScreen):
    """Adds convenience access to the running app and its services."""

    @property
    def app(self):
        """The running :class:`~main.FoodAIApp` instance."""
        return App.get_running_app()

    def build_ui(self) -> None:
        """Create the (static) widget tree. Called once from ``__init__``."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
