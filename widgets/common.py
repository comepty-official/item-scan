"""
Reusable Material 3 building blocks.

Every widget here uses the **KivyMD 2.0** API exclusively (``MDButton`` with
``MDButtonText``/``MDButtonIcon``, ``MDTopAppBar`` from ``kivymd.uix.appbar``,
``MDDialog`` with its typed containers, ...). No deprecated widget is imported.
"""

from __future__ import annotations

from collections.abc import Callable

from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivymd.uix.appbar import (
    MDActionTopAppBarButton,
    MDTopAppBar,
    MDTopAppBarLeadingButtonContainer,
    MDTopAppBarTitle,
    MDTopAppBarTrailingButtonContainer,
)
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonIcon, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogHeadlineText,
    MDDialogSupportingText,
)
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarSupportingText, MDSnackbarText
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText


# --------------------------------------------------------------------- buttons
def button(
    text: str,
    on_release: Callable | None = None,
    icon: str | None = None,
    style: str = "filled",
    **kwargs,
) -> MDButton:
    """Create an M3 button.

    :param style: ``"filled"``, ``"tonal"``, ``"outlined"``, ``"elevated"`` or ``"text"``.
    """
    children: list[Widget] = []
    if icon:
        children.append(MDButtonIcon(icon=icon))
    children.append(MDButtonText(text=text))
    widget = MDButton(*children, style=style, **kwargs)
    if on_release is not None:
        widget.bind(on_release=lambda *_: on_release())
    return widget


# --------------------------------------------------------------------- app bar
def top_bar(
    title: str,
    on_back: Callable | None = None,
    actions: list[tuple[str, Callable]] | None = None,
) -> MDTopAppBar:
    """Build a small top app bar with an optional back arrow and action icons."""
    bar = MDTopAppBar(type="small", size_hint_x=1)
    if on_back is not None:
        back = MDActionTopAppBarButton(icon="arrow-left")
        back.bind(on_release=lambda *_: on_back())
        bar.add_widget(MDTopAppBarLeadingButtonContainer(back))
    bar.add_widget(MDTopAppBarTitle(text=title, pos_hint={"center_y": 0.5}))
    if actions:
        container = MDTopAppBarTrailingButtonContainer()
        for icon, callback in actions:
            action = MDActionTopAppBarButton(icon=icon)
            action.bind(on_release=lambda _w, cb=callback: cb())
            container.add_widget(action)
        bar.add_widget(container)
    return bar


# ------------------------------------------------------------------- feedback
def toast(message: str, supporting: str | None = None) -> MDSnackbar:
    """Show a Material 3 snackbar at the bottom of the screen."""
    bar = MDSnackbar(
        MDSnackbarText(text=message),
        y=dp(16),
        orientation="horizontal" if supporting is None else "vertical",
        pos_hint={"center_x": 0.5},
        size_hint_x=0.9,
    )
    if supporting:
        bar.add_widget(MDSnackbarSupportingText(text=supporting))
    bar.open()
    return bar


# -------------------------------------------------------------------- dialogs
def confirm_dialog(
    title: str,
    message: str,
    on_confirm: Callable,
    confirm_text: str = "Delete",
) -> MDDialog:
    """Ask the admin to confirm a destructive action."""
    dialog = MDDialog(
        MDDialogHeadlineText(text=title),
        MDDialogSupportingText(text=message),
    )
    buttons = MDDialogButtonContainer(spacing=dp(8))
    buttons.add_widget(Widget())
    buttons.add_widget(button("Cancel", dialog.dismiss, style="text"))

    def _confirm() -> None:
        dialog.dismiss()
        on_confirm()

    buttons.add_widget(button(confirm_text, _confirm, style="filled"))
    dialog.add_widget(buttons)
    dialog.open()
    return dialog


def prompt_dialog(
    title: str,
    hint: str,
    on_submit: Callable[[str], None],
    initial: str = "",
    submit_text: str = "Save",
    multiline: bool = False,
) -> MDDialog:
    """Single-field text dialog used for renaming / moving / editing descriptions."""
    field = MDTextField(
        MDTextFieldHintText(text=hint),
        mode="outlined",
        text=initial,
        multiline=multiline,
        size_hint_x=1,
    )
    dialog = MDDialog(
        MDDialogHeadlineText(text=title),
        MDDialogContentContainer(field, orientation="vertical", padding=(0, dp(8), 0, 0)),
    )
    buttons = MDDialogButtonContainer(spacing=dp(8))
    buttons.add_widget(Widget())
    buttons.add_widget(button("Cancel", dialog.dismiss, style="text"))

    def _submit() -> None:
        value = field.text.strip()
        dialog.dismiss()
        on_submit(value)

    buttons.add_widget(button(submit_text, _submit, style="filled"))
    dialog.add_widget(buttons)
    dialog.open()
    return dialog


# ----------------------------------------------------------------------- cards
class ActionCard(MDCard):
    """Big tappable home-screen card with an icon, a title and a subtitle."""

    def __init__(self, icon: str, title: str, subtitle: str, on_press_callback: Callable, **kwargs):
        size_hint_y = kwargs.pop("size_hint_y", None)
        height = kwargs.pop("height", dp(148))
        super().__init__(
            style="filled",
            ripple_behavior=True,
            padding=dp(16),
            radius=dp(20),
            size_hint_y=size_hint_y,
            height=height,
            **kwargs,
        )
        self._callback = on_press_callback

        layout = MDBoxLayout(orientation="vertical", spacing=dp(4), adaptive_height=False)
        layout.add_widget(
            MDLabel(
                text=icon_glyph(icon),
                font_name=md_icon_font(),
                font_size=dp(34),
                theme_text_color="Custom",
                text_color=self.theme_cls.primaryColor,
                size_hint_y=None,
                height=dp(42),
            )
        )
        layout.add_widget(MDLabel(text=title, font_style="Title", role="medium", size_hint_y=None, height=dp(26)))
        layout.add_widget(
            MDLabel(
                text=subtitle,
                font_style="Body",
                role="small",
                theme_text_color="Custom",
                text_color=self.theme_cls.onSurfaceVariantColor,
            )
        )
        self.add_widget(layout)

    def on_release(self) -> None:
        """Forward the tap to the callback given by the screen."""
        self._callback()


class StatCard(MDCard):
    """Small outlined card that shows one dataset statistic."""

    def __init__(self, value: str, caption: str, **kwargs):
        super().__init__(
            style="outlined", padding=dp(14), radius=dp(18), size_hint_y=None, height=dp(84), **kwargs
        )
        box = MDBoxLayout(orientation="vertical", spacing=dp(2))
        box.add_widget(
            MDLabel(
                text=value,
                font_style="Headline",
                role="small",
                theme_text_color="Custom",
                text_color=self.theme_cls.primaryColor,
            )
        )
        box.add_widget(
            MDLabel(
                text=caption,
                font_style="Label",
                role="medium",
                theme_text_color="Custom",
                text_color=self.theme_cls.onSurfaceVariantColor,
            )
        )
        self.add_widget(box)


# --------------------------------------------------------------- icon helpers
def md_icon_font() -> str:
    """Name of the Material Design icon font registered by KivyMD."""
    return "Icons"


def icon_glyph(name: str) -> str:
    """Return the icon-font glyph for a Material Design icon name.

    Falls back to an empty string when the icon does not exist so a typo can
    never crash the UI.
    """
    from kivymd.icon_definitions import md_icons

    return md_icons.get(name, "")
