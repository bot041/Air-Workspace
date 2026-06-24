from PyQt6.QtCore import QRect
from PyQt6.QtGui import QColor

from ui.theme import Theme


class BrushMode:
    """A brush profile that combines color, width, opacity, and glow."""

    def __init__(self, name, base_width, alpha, glow_width, label):
        self.name = name
        self.base_width = base_width
        self.alpha = alpha
        self.glow_width = glow_width
        self.label = label

    def theme(self, color, thickness_offset=0):
        stroke = QColor(color)
        stroke.setAlpha(self.alpha)
        glow = QColor(color)
        glow.setAlpha(min(255, self.alpha + 40))
        width = max(1, self.base_width + thickness_offset)
        return Theme(self.name, stroke, width, glow, self.glow_width)


INK = BrushMode("ink", 4, 255, 6, "Ink")
NEON = BrushMode("neon", 3, 255, 12, "Neon")
MARKER = BrushMode("marker", 6, 130, 0, "Marker")
HIGHLIGHTER = BrushMode("highlighter", 18, 70, 0, "Highlighter")


class BrushManager:
    ORDER = [INK, NEON, MARKER, HIGHLIGHTER]

    def __init__(self, default=INK):
        self.selected = default
        self.thickness_offset = 0

    def select(self, mode):
        if mode in self.ORDER:
            self.selected = mode

    def select_by_name(self, name):
        for mode in self.ORDER:
            if mode.name == name:
                self.selected = mode
                return

    def mode_by_name(self, name):
        for mode in self.ORDER:
            if mode.name == name:
                return mode
        return self.selected

    def adjust_thickness(self, delta):
        self.thickness_offset = max(-5, min(10, self.thickness_offset + delta))

    def theme(self, color):
        return self.selected.theme(color, self.thickness_offset)

    # UI geometry for the left-side brush selector.
    SWATCH_SIZE = 44
    MARGIN = 20
    GAP = 12

    def swatch_rects(self, width, height):
        x = self.MARGIN
        total_h = len(self.ORDER) * self.SWATCH_SIZE + (len(self.ORDER) - 1) * self.GAP
        y = (height - total_h) // 2
        rects = []
        for mode in self.ORDER:
            rects.append((mode, QRect(x, y, self.SWATCH_SIZE, self.SWATCH_SIZE)))
            y += self.SWATCH_SIZE + self.GAP
        return rects

    def hit_test(self, point, width, height):
        for mode, rect in self.swatch_rects(width, height):
            if rect.contains(int(point[0]), int(point[1])):
                return mode.name
        return None
