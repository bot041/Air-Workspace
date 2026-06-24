from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class OutputTray(QWidget):
    """Bottom panel: stored object thumbnails."""

    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setFixedHeight(160)
        self.setMinimumWidth(640)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(45, 45, 55))

        if self.controller is None:
            painter.end()
            return

        tray_objects = self.controller.tray_objects()
        n = len(tray_objects)
        width = self.width()
        height = self.height()
        slot_w = width / max(1, n)

        selected = self.controller.selected_object()
        state = self.controller.current_state()

        for i, obj in enumerate(tray_objects):
            if obj == selected and state in ("DRAGGING", "SELECTED"):
                continue

            x = i * slot_w
            painter.setPen(QPen(QColor(100, 100, 120)))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(int(x), 0, int(slot_w) - 1, height - 1)

            if obj.strokes:
                bx, by, bw, bh = obj.bounding_box
                scale = min((slot_w - 20) / max(bw, 1), (height - 20) / max(bh, 1))
                cx = x + slot_w / 2
                cy = height / 2
                painter.save()
                painter.translate(cx, cy)
                painter.scale(scale, scale)
                painter.translate(-(bx + bw / 2), -(by + bh / 2))
                obj.draw(painter, self.controller.theme_for(obj))
                painter.restore()

        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(10, 20, "Output Tray")

        cursor = self.controller.cursor()
        if cursor is not None and cursor[1] >= self.controller.workspace_height():
            x = cursor[0]
            y = cursor[1] - self.controller.workspace_height()
            color = self.controller.cursor_color()
            painter.setPen(QPen(color))
            painter.setBrush(color)
            r = 6
            painter.drawEllipse(int(x - r), int(y - r), r * 2, r * 2)

        painter.end()
