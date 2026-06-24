from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPen


class Stroke:
    """A single polyline stroke."""

    def __init__(self, points=None):
        self.points = points or []

    def add_point(self, point):
        self.points.append(point)

    def bounding_box(self):
        if not self.points:
            return (0, 0, 0, 0)
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        x = min(xs)
        y = min(ys)
        return (x, y, max(xs) - x, max(ys) - y)

    def translate(self, dx, dy):
        self.points = [(p[0] + dx, p[1] + dy) for p in self.points]

    def draw(self, painter, color, thickness):
        if len(self.points) < 2:
            return
        pen = QPen(color)
        pen.setWidth(thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        for i in range(1, len(self.points)):
            painter.drawLine(QPointF(*self.points[i - 1]), QPointF(*self.points[i]))
