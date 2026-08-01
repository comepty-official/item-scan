"""Camera screen - live preview, capture, retake and confirm."""

from __future__ import annotations

from pathlib import Path

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.relativelayout import MDRelativeLayout

from screens.base import BaseScreen
from services.camera_service import CameraService
from widgets.common import button, toast, top_bar
from widgets.file_picker import open_file_picker


class CameraScreen(BaseScreen):
    """Shows the hardware camera, then a still preview with Retake / Use Photo."""

    def build_ui(self) -> None:
        self.camera = None            # kivy.uix.camera.Camera, created lazily
        self.captured: Path | None = None
        self.prediction_card = None

        root = MDBoxLayout(orientation="vertical")
        root.add_widget(
            top_bar(
                "Capture Food",
                on_back=lambda: self.app.switch("home"),
                actions=[
                    ("rotate-right", self.rotate_preview),
                    ("folder-image", self.import_photo),
                ],
            )
        )

        # Stage: holds either the live camera or the captured still image.
        # All floating chrome (hint pill + action buttons) lives inside the
        # stage itself now, overlaid on top of the preview.
        self.stage = MDCard(
            style="filled",
            radius=dp(20),
            padding=dp(4),
            size_hint=(1, 1),
        )
        self.viewport = MDRelativeLayout()
        self.stage.add_widget(self.viewport)

        self.recognition_panel = MDCard(
            style="elevated",
            radius=dp(24),
            padding=dp(12),
            size_hint=(0.95, None),
            height=dp(0),
            pos_hint={"center_x": 0.5, "top": 0.84},
            opacity=0,
        )
        self.viewport.add_widget(self.recognition_panel)

        self.hint_card = MDCard(
            style="filled",
            radius=dp(24),
            padding=(dp(10), dp(10), dp(10), dp(10)),
            size_hint=(0.95, None),
            height=dp(60),
            pos_hint={"center_x": 0.5, "top": 0.96},
        )
        hint_box = MDBoxLayout(orientation="horizontal", adaptive_height=True)
        self.hint = MDLabel(
            text="Hold the phone steady and fill the frame with the food.",
            font_style="Body",
            role="small",
            halign="center",
            adaptive_height=True,
            theme_text_color="Custom",
            text_color=self.theme_cls.onSurfaceVariantColor,
        )
        hint_box.add_widget(self.hint)
        self.hint_card.add_widget(hint_box)
        self.viewport.add_widget(self.hint_card)

        self.actions_panel = MDCard(
            style="elevated",
            radius=dp(24),
            padding=dp(10),
            size_hint=(0.96, None),
            height=dp(84),
            pos_hint={"center_x": 0.5, "y": 0.03},
        )
        self.actions = MDBoxLayout(size_hint=(1, 1), spacing=dp(10))
        self.actions_panel.add_widget(self.actions)
        self.viewport.add_widget(self.actions_panel)

        stage_wrapper = MDBoxLayout(padding=(dp(16), dp(8), dp(16), dp(16)))
        stage_wrapper.add_widget(self.stage)
        root.add_widget(stage_wrapper)

        self.add_widget(root)

    # --------------------------------------------------------------- helpers
    def on_pre_enter(self, *args) -> None:
        """Start the camera and show the capture button."""
        self.captured = None
        self.show_live()

    def on_leave(self, *args) -> None:
        """Always release the camera so other apps (and other screens) can use it."""
        self.stop_camera()

    def stop_camera(self) -> None:
        """Stop the camera and drop the widget."""
        if self.camera is not None:
            self.camera.play = False
            self.camera = None
        self._clear_prediction_card()
        # Only clear the live preview widget itself; the hint and actions
        # overlays are re-added by show_live()/show_still() as needed, so we
        # remove everything except those two persistent overlay widgets.
        for child in list(self.viewport.children):
            if child not in (self.hint_card, self.actions_panel, self.recognition_panel):
                self.viewport.remove_widget(child)

    # ------------------------------------------------------------ live state
    def show_live(self) -> None:
        """Create (or re-create) the live camera preview."""
        self.stop_camera()
        self.prediction_card = None
        self.actions.clear_widgets()
        self.hint.text = "Hold the phone steady and fill the frame with the food."
        self.recognition_panel.height = dp(0)
        self.recognition_panel.opacity = 0

        try:
            from kivy.uix.camera import Camera  # imported lazily: needs a provider

            self.camera = Camera(
                index=int(self.app.config_store.get("camera_index", 0)),
                resolution=(640, 480),
                play=True,
                allow_stretch=True,
                keep_ratio=True,
            )
        except Exception as error:  # no camera / no provider installed
            self.camera = None
            self.hint.text = "No camera available on this machine."
            fallback = MDLabel(
                text="Use the folder icon above to import a photo instead.\n\n"
                f"({error})",
                halign="center",
                font_style="Body",
                role="medium",
                pos_hint={"center_x": 0.5, "center_y": 0.5},
                size_hint=(0.9, None),
            )
            self.viewport.add_widget(fallback)
            self.actions.add_widget(
                button("Import photo", self.import_photo, icon="folder-image", style="filled")
            )
            return

        # A Scatter is used purely to rotate the preview so the picture is
        # always "straight", regardless of how the sensor is mounted.
        self.holder = Scatter(
            do_rotation=False,
            do_scale=False,
            do_translation=False,
            size_hint=(None, None),
            auto_bring_to_front=False,
        )
        self.holder.add_widget(self.camera)
        # Insert the camera behind the hint/actions overlays so they float
        # visibly on top of the live preview.
        self.viewport.add_widget(self.holder, index=len(self.viewport.children))
        self.viewport.bind(size=lambda *_: self._layout_preview())
        Clock.schedule_once(lambda *_: self._layout_preview(), 0)

        # Capture is a single centered circular-style button floating over
        # the bottom of the preview, instead of a full-width bar button.
        self.actions.add_widget(MDBoxLayout())
        self.actions.add_widget(
            button("Capture", self.capture, icon="camera-iris", style="filled", size_hint_x=None, width=dp(160))
        )
        self.actions.add_widget(MDBoxLayout())

    def _layout_preview(self) -> None:
        """Keep the rotated preview centred and fitted inside the viewport."""
        if self.camera is None:
            return
        rotation = int(self.app.config_store.get("preview_rotation", 0)) % 360
        width, height = self.viewport.size
        if width <= 1 or height <= 1:
            return
        # For 90/270 degrees the camera's own width/height must be swapped.
        swapped = rotation in (90, 270)
        box_w, box_h = (height, width) if swapped else (width, height)
        self.camera.size_hint = (None, None)
        self.camera.size = (box_w, box_h)
        self.holder.size = (box_w, box_h)
        self.holder.rotation = rotation
        self.holder.center = self.viewport.center

    def rotate_preview(self) -> None:
        """Cycle the preview rotation by 90 degrees and remember the choice."""
        rotation = (int(self.app.config_store.get("preview_rotation", 0)) + 90) % 360
        self.app.config_store.set("preview_rotation", rotation)
        self._layout_preview()
        toast(f"Preview rotated to {rotation} degrees")

    # --------------------------------------------------------- capture state
    def capture(self) -> None:
        """Grab the current frame and switch to the still preview."""
        if self.camera is None:
            toast("Camera is not running.")
            return
        try:
            path = CameraService.capture(
                self.camera.texture,
                rotation=int(self.app.config_store.get("preview_rotation", 0)),
            )
        except Exception as error:
            toast("Capture failed", str(error))
            return
        self.stop_camera()
        self.show_still(path)

    def import_photo(self) -> None:
        """Import an existing image file instead of taking a picture."""

        def _selected(file_path: str) -> None:
            try:
                path = CameraService.import_file(file_path)
            except Exception as error:
                toast("Import failed", str(error))
                return
            self.stop_camera()
            self.show_still(path)

        open_file_picker(_selected)

    def show_still(self, path: Path) -> None:
        """Display the captured photo with Retake / Use Photo buttons."""
        self.captured = path
        self.stop_camera()
        image = Image(source=str(path), fit_mode="contain")
        self.viewport.add_widget(image, index=len(self.viewport.children))
        self.hint.text = "Happy with the shot? Continue to add the food details."

        self._suggest_prediction(path)

        self.actions.clear_widgets()
        self.actions.add_widget(
            button("Retake", self.show_live, icon="camera-retake-outline", style="outlined", size_hint_x=0.5)
        )
        self.actions.add_widget(
            button("Use Photo", self.use_photo, icon="check", style="filled", size_hint_x=0.5)
        )

    def _clear_prediction_card(self) -> None:
        """Hide the animated prediction card from the viewport."""
        if self.prediction_card is not None:
            self.prediction_card.opacity = 0
            self.prediction_card.size_hint_y = None
            self.prediction_card.height = dp(0)
            self.prediction_card = None

    def _suggest_prediction(self, path: Path) -> None:
        """Show a friendly recognition card if the image looks familiar."""
        self._clear_prediction_card()
        try:
            prediction = self.app.predictor.predict_from_path(path)
        except Exception:  # pragma: no cover - best effort UI hint
            return

        self.recognition_panel.clear_widgets()
        content = MDBoxLayout(orientation="vertical", spacing=dp(6), adaptive_height=True)
        title = MDLabel(
            text="🍔 Predicted Food" if prediction.label else "🤔 Not sure yet",
            font_style="Label",
            role="large",
            adaptive_height=True,
        )
        name = MDLabel(
            text=prediction.label or "Unknown",
            font_style="Title",
            role="large",
            adaptive_height=True,
        )
        confidence = MDLabel(
            text=f"Confidence: {int(prediction.confidence * 100)}%",
            font_style="Body",
            role="small",
            adaptive_height=True,
            theme_text_color="Custom",
            text_color=self.theme_cls.onSurfaceVariantColor,
        )
        detail = MDLabel(
            text=prediction.message,
            font_style="Body",
            role="small",
            adaptive_height=True,
            theme_text_color="Custom",
            text_color=self.theme_cls.onSurfaceVariantColor,
        )
        actions = MDBoxLayout(adaptive_height=True, spacing=dp(8))
        actions.add_widget(button("Accept", lambda: self._accept_prediction(prediction.label), icon="check", style="filled", size_hint_x=0.5))
        actions.add_widget(button("Edit Name", self._edit_name, icon="pencil-outline", style="outlined", size_hint_x=0.5))
        content.add_widget(title)
        content.add_widget(name)
        content.add_widget(confidence)
        content.add_widget(detail)
        content.add_widget(actions)
        self.recognition_panel.add_widget(content)
        self.prediction_card = self.recognition_panel

        if prediction.label:
            self.hint.text = f"Looks familiar — {prediction.label}"
        else:
            self.hint.text = "I don't know this one yet — let's add the details manually."

        self.recognition_panel.opacity = 1
        self.recognition_panel.height = dp(220)
        Animation(opacity=1, duration=0.25).start(self.recognition_panel)

    def _accept_prediction(self, label: str | None) -> None:
        """Use a recognized label and carry the user to the details editor."""
        if self.captured is None:
            return
        self.app.open_details(self.captured, suggested_label=label)

    def _edit_name(self) -> None:
        """Go to the details screen without preloading a prediction."""
        if self.captured is None:
            return
        self.app.open_details(self.captured, suggested_label=None)

    def use_photo(self) -> None:
        """Hand the captured photo over to the details screen."""
        if self.captured is None:
            toast("Take a photo first.")
            return
        self.app.open_details(self.captured)