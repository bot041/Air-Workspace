"""Synthetic tests for the gesture detector.

These tests construct simple hand landmarks so we can verify classification
without a live camera.
"""

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tracking.gesture_detector import Gesture, GestureDetector


def lm(x, y):
    """Build a MediaPipe-compatible landmark."""
    return SimpleNamespace(x=x, y=y)


def _curled_finger(mcp, pip_pos):
    """Return tip and pip positions for a curled (non-extended) finger."""
    return pip_pos, pip_pos  # tip == pip


def _extended_finger(mcp, pip_pos, length=0.12):
    """Return tip and pip positions for an extended finger.

    The tip is placed `length` farther from the wrist than the pip.
    """
    # Place the pip at a fixed location and the tip straight above it.
    tip = (pip_pos[0], pip_pos[1] + length)
    return pip_pos, tip


def make_hand(
    thumb=("curled", (0.04, 0.08)),
    index=("extended", (0.08, 0.12)),
    middle=("curled", (0.10, 0.12)),
    ring=("curled", (0.12, 0.12)),
    pinky=("curled", (0.14, 0.12)),
):
    """Return a 21-landmark list.

    Wrist at (0,0) and middle MCP at (0,0.2), so hand_scale is 0.2.
    Each finger argument is a tuple: (state, pip_position).
    """
    fingers = {
        "thumb": thumb,
        "index": index,
        "middle": middle,
        "ring": ring,
        "pinky": pinky,
    }

    def finger_points(state, pip_pos):
        if state == "extended":
            return _extended_finger(None, pip_pos)
        return _curled_finger(None, pip_pos)

    t_pip, t_tip = finger_points(*fingers["thumb"])
    i_pip, i_tip = finger_points(*fingers["index"])
    m_pip, m_tip = finger_points(*fingers["middle"])
    r_pip, r_tip = finger_points(*fingers["ring"])
    p_pip, p_tip = finger_points(*fingers["pinky"])

    return [
        lm(0.0, 0.0),        # 0 wrist
        lm(0.02, 0.05),      # 1 thumb cmc
        lm(0.04, 0.07),      # 2 thumb mcp
        lm(*t_pip),          # 3 thumb ip (pip)
        lm(*t_tip),          # 4 thumb tip
        lm(0.08, 0.06),      # 5 index mcp
        lm(*i_pip),          # 6 index pip
        lm(0.08, 0.10),      # 7 index dip
        lm(*i_tip),          # 8 index tip
        lm(0.10, 0.08),      # 9 middle mcp
        lm(*m_pip),          # 10 middle pip
        lm(0.10, 0.10),      # 11 middle dip
        lm(*m_tip),          # 12 middle tip
        lm(0.12, 0.10),      # 13 ring mcp
        lm(*r_pip),          # 14 ring pip
        lm(0.12, 0.12),      # 15 ring dip
        lm(*r_tip),          # 16 ring tip
        lm(0.14, 0.12),      # 17 pinky mcp
        lm(*p_pip),          # 18 pinky pip
        lm(0.14, 0.14),      # 19 pinky dip
        lm(*p_tip),          # 20 pinky tip
    ]


def test_draw():
    detector = GestureDetector(smoother_min_stable=1)
    landmarks = make_hand(
        index=("extended", (0.08, 0.12)),
        middle=("curled", (0.10, 0.12)),
        ring=("curled", (0.12, 0.12)),
        pinky=("curled", (0.14, 0.12)),
    )
    assert detector.detect(landmarks)[0] == Gesture.DRAW


def test_navigate():
    detector = GestureDetector(smoother_min_stable=1)
    landmarks = make_hand(
        index=("extended", (0.08, 0.12)),
        middle=("extended", (0.10, 0.12)),
        ring=("curled", (0.12, 0.12)),
        pinky=("curled", (0.14, 0.12)),
    )
    assert detector.detect(landmarks)[0] == Gesture.NAVIGATE


def test_palm():
    detector = GestureDetector(smoother_min_stable=1)
    landmarks = make_hand(
        thumb=("extended", (0.04, 0.08)),
        index=("extended", (0.08, 0.12)),
        middle=("extended", (0.10, 0.12)),
        ring=("extended", (0.12, 0.12)),
        pinky=("extended", (0.14, 0.12)),
    )
    assert detector.detect(landmarks)[0] == Gesture.PALM


def test_pinch():
    detector = GestureDetector(smoother_min_stable=1)
    # Put thumb and index tips very close to each other.
    landmarks = make_hand(
        thumb=("extended", (0.08, 0.22)),
        index=("extended", (0.08, 0.22)),
        middle=("curled", (0.10, 0.12)),
        ring=("curled", (0.12, 0.12)),
        pinky=("curled", (0.14, 0.12)),
    )
    assert detector.detect(landmarks)[0] == Gesture.PINCH


def test_smoother_requires_stability():
    """A single-frame flicker should not change the stable output."""
    draw = make_hand(
        index=("extended", (0.08, 0.12)),
        middle=("curled", (0.10, 0.12)),
        ring=("curled", (0.12, 0.12)),
        pinky=("curled", (0.14, 0.12)),
    )
    navigate = make_hand(
        index=("extended", (0.08, 0.12)),
        middle=("extended", (0.10, 0.12)),
        ring=("curled", (0.12, 0.12)),
        pinky=("curled", (0.14, 0.12)),
    )
    detector = GestureDetector(smoother_window=5, smoother_min_stable=3)

    # Settle on DRAW
    for _ in range(5):
        gesture, _ = detector.detect(draw)
    assert gesture == Gesture.DRAW

    # One frame of NAVIGATE should not switch
    gesture, _ = detector.detect(navigate)
    assert gesture == Gesture.DRAW

    # After several frames it should switch
    for _ in range(4):
        gesture, _ = detector.detect(navigate)
    assert gesture == Gesture.NAVIGATE


if __name__ == "__main__":
    test_draw()
    test_navigate()
    test_palm()
    test_pinch()
    test_smoother_requires_stability()
    print("All gesture detector tests passed.")
