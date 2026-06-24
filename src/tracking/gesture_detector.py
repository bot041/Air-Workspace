import math
from collections import deque


class Gesture:
    DRAW = "DRAW"
    NAVIGATE = "NAVIGATE"
    PINCH = "PINCH"
    PALM = "PALM"
    IDLE = "IDLE"


class GestureSmoother:
    """Hysteresis smoother that only switches gestures after several
    consecutive frames agree. This removes single-frame flicker between
    similar poses (e.g. DRAW <-> NAVIGATE).
    """

    def __init__(self, window=5, min_stable=3):
        self.window = window
        self.min_stable = min_stable
        self._history = deque(maxlen=window)
        self._stable = Gesture.IDLE

    def update(self, gesture):
        self._history.append(gesture)
        if gesture == self._stable:
            return self._stable
        if self._history.count(gesture) >= self.min_stable:
            self._stable = gesture
        return self._stable

    @property
    def stable(self):
        return self._stable


class GestureDetector:
    """Classifies hand gestures from MediaPipe landmarks.

    Thresholds are expressed as fractions of the hand size (wrist to
    middle-finger MCP) so they adapt automatically to hand distance from
    the camera.
    """

    def __init__(
        self,
        pinch_factor=0.22,
        extension_factor=0.06,
        smoother_window=5,
        smoother_min_stable=2,
    ):
        self.pinch_factor = pinch_factor
        self.extension_factor = extension_factor
        self.smoother = GestureSmoother(
            window=smoother_window, min_stable=smoother_min_stable
        )
        self._last_raw = Gesture.IDLE

    @staticmethod
    def _dist(a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    def _hand_scale(self, landmarks):
        """Use wrist -> middle finger MCP as a proxy for hand size."""
        scale = self._dist(landmarks[0], landmarks[9])
        return scale if scale > 0 else 0.1

    def _extended(self, tip, pip, wrist, hand_scale):
        """A finger is extended when its tip is clearly farther from the
        wrist than its PIP joint, relative to overall hand size.
        """
        return self._dist(tip, wrist) > self._dist(pip, wrist) + hand_scale * self.extension_factor

    def _classify_raw(self, landmarks):
        hand_scale = self._hand_scale(landmarks)
        pinch_threshold = hand_scale * self.pinch_factor

        tips = [4, 8, 12, 16, 20]
        pips = [3, 6, 10, 14, 18]
        extended = [
            self._extended(landmarks[tips[i]], landmarks[pips[i]], landmarks[0], hand_scale)
            for i in range(5)
        ]

        thumb_index_dist = self._dist(landmarks[4], landmarks[8])

        if thumb_index_dist < pinch_threshold:
            return Gesture.PINCH
        if all(extended):
            return Gesture.PALM
        if extended[1] and not any(extended[2:]):
            return Gesture.DRAW
        if extended[1] and extended[2] and not extended[3] and not extended[4]:
            return Gesture.NAVIGATE
        return Gesture.IDLE

    def detect(self, landmarks, frame_shape=None):
        """Return the smoothed gesture and normalized cursor position.

        The cursor follows the index fingertip (landmark 8). When pinching,
        the cursor is placed at the midpoint between thumb and index for a
        natural grab point.
        """
        self._last_raw = self._classify_raw(landmarks)
        gesture = self.smoother.update(self._last_raw)

        # The cursor always follows the index fingertip (landmark 8) strictly,
        # regardless of gesture. This keeps the on-screen point exactly at the
        # tip of the index finger for drawing, selecting, and dragging.
        cursor_norm = (1.0 - landmarks[8].x, landmarks[8].y)
        return gesture, cursor_norm

    def current_gesture(self):
        return self.smoother.stable

    def current_raw_gesture(self):
        return self._last_raw

    def reset(self):
        self.smoother = GestureSmoother(
            window=self.smoother.window, min_stable=self.smoother.min_stable
        )
        self._last_raw = Gesture.IDLE
