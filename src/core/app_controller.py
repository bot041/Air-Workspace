import time

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtGui import QColor

from camera.webcam import Webcam
from core.state_machine import State, StateMachine
from drawing.smoother import Smoother
from drawing.stroke import Stroke
from eraser.eraser import Eraser
from objects.object_manager import ObjectManager
from objects.stroke_object import StrokeObject
from selection.selection_manager import SelectionManager
from tracking.gesture_detector import Gesture, GestureDetector
from tracking.hand_tracker import HandTracker
from ui.brush import BrushManager, BrushMode
from ui.palette import ColorPalette
from ui.theme import DELETE_GLOW


class AppController(QObject):
    """Owns the update loop and wires all subsystems together."""

    FINALIZE_DELAY = 1.0
    DELETE_HOLD_DELAY = 1.0

    def __init__(self, workspace_widget, parent=None):
        super().__init__(parent)
        self.workspace = workspace_widget

        self.webcam = Webcam()
        self.hand_tracker = HandTracker(max_hands=1)
        self.gesture_detector = GestureDetector()
        self.object_manager = ObjectManager()
        self.selection = SelectionManager()
        self.eraser = Eraser()
        self.state_machine = StateMachine()
        self.smoother = Smoother()
        self.palette = ColorPalette(default="white")
        self.brush = BrushManager()

        self.active_obj = None
        self.active_stroke = None
        self.last_draw_time = 0.0

        self._cursor = (0.0, 0.0)
        self._cursor_color = QColor(255, 255, 255)
        self._frame = None
        self._status = "AirScript Ready"

        self._fps = 0
        self._fps_count = 0
        self._fps_time = time.perf_counter()

        self.hover_obj = None
        self.hover_start = 0.0
        self.hover_orig_theme = None
        self._last_eraser_pos = None
        self._palette_hover_key = None
        self._palette_hover_start = 0.0
        self._brush_hover_name = None
        self._brush_hover_start = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

    # ------------------------------------------------------------------
    # Queries used by UI panels
    # ------------------------------------------------------------------
    def current_frame(self):
        return self._frame

    def cursor(self):
        return self._cursor

    def cursor_color(self):
        return self._cursor_color

    def workspace_objects(self):
        return sorted(self.object_manager.objects, key=lambda o: o.z_index)

    def active_object(self):
        return self.active_obj

    def selected_object(self):
        return self.selection.selected

    def current_state(self):
        return self.state_machine.state

    def current_gesture(self):
        return self.gesture_detector.current_gesture()

    def current_theme(self):
        return self.brush.theme(self.palette.color())

    def theme_for(self, obj):
        if obj.theme == "delete_glow":
            return DELETE_GLOW
        color = self.palette.color(obj.theme)
        mode = self.brush.mode_by_name(obj.brush)
        return mode.theme(color, obj.thickness_offset)

    def status_text(self):
        return self._status

    def fps_text(self):
        return f"{self._fps} FPS"

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def _tick(self):
        frame = self.webcam.read()
        self._frame = frame
        self._update_fps()

        if frame is None:
            self._status = "No camera"
            self._update()
            return

        landmarks = self.hand_tracker.process(frame)
        if landmarks:
            gesture, cursor_norm = self.gesture_detector.detect(landmarks, frame.shape)
            w = self.workspace.width()
            h = self.workspace.height()
            self._cursor = (cursor_norm[0] * w, cursor_norm[1] * h)
            self._handle_gesture(gesture)
        else:
            self._handle_no_hand()

        self._validate_selection()
        self._update()

    def _update_fps(self):
        now = time.perf_counter()
        self._fps_count += 1
        if now - self._fps_time >= 1.0:
            self._fps = self._fps_count
            self._fps_count = 0
            self._fps_time = now

    def _update(self):
        self.workspace.update()

    def _validate_selection(self):
        """Clear stale selection/hover if their objects no longer exist."""
        all_objects = self.object_manager.objects
        if self.selection.selected is not None and self.selection.selected not in all_objects:
            self.selection.clear()
        if self.hover_obj is not None and self.hover_obj not in all_objects:
            self.hover_obj = None
            self.hover_start = 0.0

    # ------------------------------------------------------------------
    # Gesture handling
    # ------------------------------------------------------------------
    def _handle_gesture(self, gesture):
        state = self.state_machine.state

        if gesture == Gesture.PINCH:
            self._clear_hover()
            self._last_eraser_pos = None
            self._palette_hover_key = None
            self._brush_hover_name = None
            self._set_cursor_color(QColor(255, 220, 0))

            if state in (State.IDLE, State.NAVIGATING, State.OBJECT_OPEN, State.ERASING):
                self._finalize_active()

                # First check if the user is pinching a color swatch.
                swatch = self.palette.hit_test(
                    self._cursor, self.workspace.width(), self.workspace.height()
                )
                if swatch:
                    self.palette.select(swatch)
                    self._status = f"Color: {swatch}"
                    self.state_machine.transition(State.IDLE)
                    return

                obj = self.object_manager.top_workspace_object_at(self._cursor)
                if obj:
                    self.selection.select(obj, self._cursor)
                    self.object_manager.bring_to_front(obj)
                    self.state_machine.transition(State.SELECTED)
                    self._status = f"Selected object {obj.object_id}"
                else:
                    self.state_machine.transition(State.IDLE)
                    self._status = "Pinch"

            elif state == State.SELECTED:
                self.state_machine.transition(State.DRAGGING)
                self._status = "Dragging"

            elif state == State.DRAGGING:
                self._drag_selected(self._cursor)
                self._status = "Dragging"

        elif gesture == Gesture.DRAW:
            self._clear_hover()
            self._last_eraser_pos = None
            raw = self.gesture_detector.current_raw_gesture()

            if state != State.DRAWING and raw in (Gesture.DRAW, Gesture.NAVIGATE):
                # Brush selector dwell (left side).
                brush_name = self.brush.hit_test(
                    self._cursor, self.workspace.width(), self.workspace.height()
                )
                if brush_name:
                    if self._brush_hover_name != brush_name:
                        self._brush_hover_name = brush_name
                        self._brush_hover_start = time.perf_counter()
                        self._palette_hover_key = None
                    elif time.perf_counter() - self._brush_hover_start >= 0.3:
                        if self.active_obj is not None:
                            self._finalize_active()
                        self.brush.select_by_name(brush_name)
                        self._brush_hover_name = None
                        self._status = f"Brush: {brush_name}"
                        self.state_machine.transition(State.IDLE)
                        self._update()
                        return
                    self._set_cursor_color(self.palette.color())
                    self._status = f"Brush hover: {brush_name}"
                    self.state_machine.transition(State.IDLE)
                    self._update()
                    return
                else:
                    self._brush_hover_name = None

                # Color palette dwell (right side).
                swatch = self.palette.hit_test(
                    self._cursor, self.workspace.width(), self.workspace.height()
                )
                if swatch:
                    if self._palette_hover_key != swatch:
                        self._palette_hover_key = swatch
                        self._palette_hover_start = time.perf_counter()
                        self._brush_hover_name = None
                    elif time.perf_counter() - self._palette_hover_start >= 0.3:
                        if self.active_obj is not None:
                            self._finalize_active()
                        self.palette.select(swatch)
                        self._palette_hover_key = None
                        self._status = f"Color: {swatch}"
                        self.state_machine.transition(State.IDLE)
                        self._update()
                        return
                    self._set_cursor_color(self.palette.color())
                    self._status = f"Hover: {swatch}"
                    self.state_machine.transition(State.IDLE)
                    self._update()
                    return
            self._palette_hover_key = None
            self._brush_hover_name = None

            self._set_cursor_color(QColor(0, 255, 100))

            if state == State.SELECTED:
                self.selection.clear()

            if self.active_obj is None:
                self.active_obj = StrokeObject(
                    theme=self.palette.selected,
                    brush=self.brush.selected.name,
                    thickness_offset=self.brush.thickness_offset,
                )
                self.active_stroke = None

            if self.active_stroke is None:
                self.active_stroke = Stroke()
                self.active_obj.add_stroke(self.active_stroke)

            pt = self.smoother.add(self._cursor)
            self.active_stroke.add_point(pt)
            self.active_obj._update_bbox()
            self.last_draw_time = time.perf_counter()
            self.state_machine.transition(State.DRAWING)
            self._status = "Drawing"

        elif gesture == Gesture.NAVIGATE:
            self._clear_hover()
            self._last_eraser_pos = None
            self._palette_hover_key = None
            self._brush_hover_name = None
            self._set_cursor_color(QColor(0, 150, 255))

            if state == State.DRAWING:
                self.active_stroke = None
                self.smoother.reset()
                self.last_draw_time = time.perf_counter()
                self.state_machine.transition(State.OBJECT_OPEN)
                self._status = "Stroke ended"

            elif state == State.SELECTED:
                self.selection.clear()
                self.state_machine.transition(State.IDLE)
                self._status = "Deselected"

            elif state == State.DRAGGING:
                self._drop_selected(self._cursor)

            elif state in (State.IDLE, State.NAVIGATING, State.OBJECT_OPEN, State.ERASING):
                self.state_machine.transition(State.NAVIGATING)
                self._status = "Navigate"

        elif gesture == Gesture.PALM:
            self._palette_hover_key = None
            self._brush_hover_name = None
            self._set_cursor_color(QColor(255, 50, 50))

            if state in (State.DRAWING, State.OBJECT_OPEN):
                self._finalize_active()

            self.state_machine.transition(State.ERASING)
            if self._last_eraser_pos is None:
                self._last_eraser_pos = self._cursor
            self.object_manager.objects = self.eraser.erase_at(
                self._cursor, self.object_manager.objects, prev=self._last_eraser_pos
            )
            self._last_eraser_pos = self._cursor
            self._status = "Erasing"

            obj = self.object_manager.top_workspace_object_at(self._cursor)
            if obj:
                if self.hover_obj != obj:
                    self._clear_hover()
                    self.hover_obj = obj
                    self.hover_start = time.perf_counter()
                    self.hover_orig_theme = obj.theme
                    obj.theme = "delete_glow"
                elif time.perf_counter() - self.hover_start >= self.DELETE_HOLD_DELAY:
                    self.object_manager.remove_object(obj)
                    self._clear_hover()
                    self._status = "Object deleted"
            else:
                self._clear_hover()

        else:  # IDLE / unrecognized
            self._clear_hover()
            self._last_eraser_pos = None
            self._palette_hover_key = None
            self._brush_hover_name = None
            self._set_cursor_color(QColor(255, 255, 255))

            if state == State.DRAWING:
                self.active_stroke = None
                self.smoother.reset()
                self.last_draw_time = time.perf_counter()
                self.state_machine.transition(State.OBJECT_OPEN)

            elif state in (State.SELECTED, State.DRAGGING):
                self.selection.clear()
                self.state_machine.transition(State.IDLE)

            elif state == State.ERASING:
                self.state_machine.transition(State.IDLE)

            self._status = "Idle"

        # Auto-finalize after inactivity.
        if self.active_obj and (time.perf_counter() - self.last_draw_time) > self.FINALIZE_DELAY:
            if state in (State.DRAWING, State.OBJECT_OPEN):
                self._finalize_active()
                self.state_machine.transition(State.IDLE)
                self._status = "Object finalized"

    def _handle_no_hand(self):
        self._clear_hover()
        self._last_eraser_pos = None
        self._palette_hover_key = None
        self._brush_hover_name = None
        self._set_cursor_color(QColor(255, 255, 255))

        if self.active_obj and (time.perf_counter() - self.last_draw_time) > self.FINALIZE_DELAY:
            self._finalize_active()
            self.state_machine.transition(State.IDLE)
            self._status = "Object finalized (no hand)"

        if self.state_machine.state in (State.SELECTED, State.DRAGGING):
            self._drop_selected(self._cursor)
            self.selection.clear()
            self.state_machine.transition(State.IDLE)

    # ------------------------------------------------------------------
    # Object / selection helpers
    # ------------------------------------------------------------------
    def _finalize_active(self):
        if self.active_obj is None:
            return
        if self.active_obj.strokes:
            self.active_obj.theme = self.palette.selected
            self.active_obj.brush = self.brush.selected.name
            self.active_obj.thickness_offset = self.brush.thickness_offset
            self.object_manager.add_workspace_object(self.active_obj)
        self.active_obj = None
        self.active_stroke = None
        self.smoother.reset()

    def _drag_selected(self, cursor):
        obj = self.selection.selected
        if obj is None:
            return
        dx = cursor[0] + self.selection.drag_offset[0] - obj.position[0]
        dy = cursor[1] + self.selection.drag_offset[1] - obj.position[1]
        obj.translate(dx, dy)

    def _drop_selected(self, cursor):
        obj = self.selection.selected
        if obj is None:
            self.state_machine.transition(State.IDLE)
            return

        self.selection.clear()
        self.state_machine.transition(State.IDLE)

    def _clear_hover(self):
        if self.hover_obj is not None and self.hover_obj.theme == "delete_glow":
            self.hover_obj.theme = self.hover_orig_theme if self.hover_orig_theme else self.palette.selected
        self.hover_obj = None
        self.hover_start = 0.0

    def _set_cursor_color(self, color):
        self._cursor_color = color

    def select_color(self, key):
        """Public API for keyboard/menu color selection."""
        if key in self.palette.COLORS:
            # Finalize any in-progress object first so it keeps its current
            # color instead of being retroactively changed.
            if self.active_obj is not None:
                self._finalize_active()
            self.palette.select(key)
            self._status = f"Color: {key}"
            self._update()

    def select_brush(self, name):
        """Public API for keyboard/menu brush selection."""
        if self.active_obj is not None:
            self._finalize_active()
        self.brush.select_by_name(name)
        self._status = f"Brush: {name}"
        self._update()

    def adjust_thickness(self, delta):
        """Public API to adjust stroke thickness."""
        if self.active_obj is not None:
            self._finalize_active()
        self.brush.adjust_thickness(delta)
        self._status = f"Thickness: {self.brush.selected.base_width + self.brush.thickness_offset}"
        self._update()

    def cleanup(self):
        self.timer.stop()
        self.webcam.release()
        self.hand_tracker.close()
