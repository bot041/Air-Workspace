from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPen


class Theme:
    def __init__(self, name, stroke_color, stroke_width, glow_color=None, glow_width=0):
        self.name = name
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.glow_color = glow_color or stroke_color
        self.glow_width = glow_width

    def draw_stroke(self, painter, stroke, selected=False):
        if len(stroke.points) < 2:
            return

        pts = [QPointF(*p) for p in stroke.points]

        # All colors get a subtle outer glow for an AR/futuristic look.
        glow = QColor(self.glow_color)
        for width, alpha in (
            (self.stroke_width + self.glow_width + 8, 40),
            (self.stroke_width + self.glow_width + 4, 80),
            (self.stroke_width + self.glow_width, 140),
        ):
            glow.setAlpha(alpha)
            pen = QPen(glow)
            pen.setWidth(width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            for i in range(1, len(pts)):
                painter.drawLine(pts[i - 1], pts[i])

        # Extra glow when the object is selected.
        if selected:
            glow.setAlpha(200)
            pen = QPen(glow)
            pen.setWidth(self.stroke_width + self.glow_width + 6)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            for i in range(1, len(pts)):
                painter.drawLine(pts[i - 1], pts[i])

        # Neon mode adds a few extra bloom layers.
        if self.name == "neon":
            for width, alpha in ((self.stroke_width + 10, 50), (self.stroke_width + 5, 100)):
                color = QColor(self.stroke_color)
                color.setAlpha(alpha)
                pen = QPen(color)
                pen.setWidth(width)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                for i in range(1, len(pts)):
                    painter.drawLine(pts[i - 1], pts[i])

        # Main stroke.
        pen = QPen(self.stroke_color)
        pen.setWidth(self.stroke_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        for i in range(1, len(pts)):
            painter.drawLine(pts[i - 1], pts[i])


INK = Theme("ink", QColor(20, 20, 20), 4, QColor(100, 180, 255), 8)
NEON = Theme("neon", QColor(0, 255, 200), 3, QColor(0, 200, 255), 12)
DELETE_GLOW = Theme("delete_glow", QColor(220, 20, 20), 4, QColor(255, 0, 0), 10)
