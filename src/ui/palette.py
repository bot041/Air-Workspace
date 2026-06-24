from PyQt6.QtCore import QRect
from PyQt6.QtGui import QColor

from ui.theme import Theme


class ColorPalette:
    """Right-side color palette that can be selected via gestures."""

    COLORS = {
        "green": (QColor(0, 255, 100), QColor(150, 255, 180)),
        "red": (QColor(255, 50, 50), QColor(255, 150, 150)),
        "neon": (QColor(0, 255, 200), QColor(0, 200, 255)),
        "blue": (QColor(0, 150, 255), QColor(120, 200, 255)),
        "orange": (QColor(255, 140, 0), QColor(255, 200, 100)),
        "white": (QColor(255, 255, 255), QColor(180, 220, 255)),
    }

    ORDER = ["green", "red", "neon", "blue", "orange", "white"]

    SWATCH_SIZE = 50
    MARGIN = 20
    GAP = 12

    def __init__(self, default="white"):
        self.selected = default

    def theme(self, key=None):
        key = key or self.selected
        stroke, glow = self.COLORS[key]
        return Theme(key, QColor(stroke), 4, QColor(glow), 8)

    def color(self, key=None):
        key = key or self.selected
        return self.COLORS[key][0]

    def swatch_rects(self, width, height):
        """Return [(key, QRect), ...] for a vertical column on the right."""
        x = width - self.SWATCH_SIZE - self.MARGIN
        total_h = len(self.ORDER) * self.SWATCH_SIZE + (len(self.ORDER) - 1) * self.GAP
        y = (height - total_h) // 2
        rects = []
        for key in self.ORDER:
            rects.append((key, QRect(x, y, self.SWATCH_SIZE, self.SWATCH_SIZE)))
            y += self.SWATCH_SIZE + self.GAP
        return rects

    def hit_test(self, point, width, height):
        """Return the swatch key under ``point``, or None."""
        for key, rect in self.swatch_rects(width, height):
            if rect.contains(int(point[0]), int(point[1])):
                return key
        return None

    def select(self, key):
        if key in self.COLORS:
            self.selected = key
