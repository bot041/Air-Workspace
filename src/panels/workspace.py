import time

import cv2

from PyQt6.QtCore import Qt
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from ui.renderer import Renderer


_GESTURE_HINTS = {
    "DRAW": ("Draw", "Index finger only"),
    "NAVIGATE": ("Navigate", "Index + Middle"),
    "PINCH": ("Pinch", "Select / Drag"),
    "PALM": ("Palm", "Erase / Hold to delete"),
    "IDLE": ("Idle", "Show hand to start"),
}


class Workspace(QWidget):
    """Fullscreen workspace: live camera feed + drawings + gesture overlay + palette."""

    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setMinimumSize(640, 480)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self.controller is None:
            painter.fillRect(self.rect(), QColor(30, 30, 30))
            painter.end()
            return

        frame = self.controller.current_frame()
        if frame is not None:
            # Mirror the webcam preview so it behaves like a mirror.
            frame = cv2.flip(frame, 1)
            pm = Renderer.cv_frame_to_pixmap(frame)
            pm = pm.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x_offset = (self.width() - pm.width()) // 2
            y_offset = (self.height() - pm.height()) // 2
            painter.drawPixmap(x_offset, y_offset, pm)
        else:
            painter.fillRect(self.rect(), QColor(30, 30, 30))

        for obj in self.controller.workspace_objects():
            obj.draw(painter, self.controller.theme_for(obj))

        active = self.controller.active_object()
        if active is not None:
            active.draw(painter, self.controller.current_theme())

        cursor = self.controller.cursor()
        if cursor is not None:
            x, y = cursor
            color = self.controller.cursor_color()
            painter.setPen(color)
            painter.setBrush(color)
            r = 8
            painter.drawEllipse(int(x - r), int(y - r), r * 2, r * 2)

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(10, 20, f"{self.controller.status_text()} | {self.controller.fps_text()}")

        self._draw_gesture_overlay(painter)
        self._draw_brush_selector(painter)
        self._draw_palette(painter)

        painter.end()

    def _draw_gesture_overlay(self, painter):
        gesture = self.controller.current_gesture()
        label, hint = _GESTURE_HINTS.get(gesture, (gesture, ""))
        theme = self.controller.current_theme()
        color = QColor(theme.stroke_color)
        glow = QColor(theme.glow_color)

        title_font = QFont("Segoe UI", 13)
        title_font.setBold(True)
        hint_font = QFont("Segoe UI", 11)

        title_fm = QFontMetrics(title_font)
        hint_fm = QFontMetrics(hint_font)
        title_w = title_fm.horizontalAdvance(label)
        hint_w = hint_fm.horizontalAdvance(hint)

        pad = 14
        width = max(title_w, hint_w) + pad * 2
        height = 64
        x = 20
        y = 20

        # Translucent background
        bg = QColor(10, 10, 15)
        bg.setAlpha(180)
        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(x, y, width, height, 10, 10)

        # Neon glow behind the title when in neon mode
        if theme.name == "neon":
            for offset, alpha in ((3, 60), (2, 120), (1, 180)):
                glow.setAlpha(alpha)
                glow_font = QFont(title_font)
                glow_font.setPointSize(title_font.pointSize() + offset)
                painter.setFont(glow_font)
                painter.setPen(glow)
                painter.drawText(x + pad, y + 28, label)

        # Title
        painter.setFont(title_font)
        painter.setPen(color)
        painter.drawText(x + pad, y + 28, label)

        # Hint
        painter.setFont(hint_font)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(x + pad, y + 52, hint)

    def _draw_palette(self, painter):
        palette = self.controller.palette
        rects = palette.swatch_rects(self.width(), self.height())
        if not rects:
            return

        # Futuristic glass panel behind the swatches.
        first = rects[0][1]
        last = rects[-1][1]
        panel_pad = 18
        title_room = 42
        panel_x = first.left() - panel_pad
        panel_y = first.top() - panel_pad - title_room
        panel_w = first.width() + panel_pad * 2
        panel_h = (last.bottom() - first.top()) + panel_pad * 2 + title_room

        panel = QRect(panel_x, panel_y, panel_w, panel_h)

        # Dark translucent background
        bg = QColor(8, 8, 14)
        bg.setAlpha(200)
        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(panel, 14, 14)

        # Neon border in the current ink color
        border = QColor(palette.color())
        border.setAlpha(180)
        pen = QPen(border)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(panel.adjusted(2, 2, -2, -2), 12, 12)

        # Title
        title_font = QFont("Segoe UI", 10)
        title_font.setBold(True)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(title_font)
        painter.setPen(QColor(200, 200, 210))
        title_x = panel_x + (panel_w - QFontMetrics(title_font).horizontalAdvance("COLORS")) // 2
        painter.drawText(title_x, panel_y + 24, "COLORS")

        # Dwell-selection progress for index-finger hover.
        hover_key = self.controller._palette_hover_key
        hover_start = self.controller._palette_hover_start
        progress = 0.0
        if hover_key:
            progress = min(1.0, (time.time() - hover_start) / 0.35)

        for key, rect in rects:
            self._draw_glowing_swatch(
                painter, rect, palette.color(key),
                selected=(key == palette.selected),
                hovered=(key == hover_key),
                progress=progress if key == hover_key else 0.0,
            )

    def _draw_glowing_swatch(self, painter, rect, color, selected=False, hovered=False, progress=0.0):
        """Draw a rounded color swatch with layered glow."""
        base = QColor(color)

        # Outer glow layers
        for offset, alpha in ((14, 35), (10, 60), (6, 110)):
            glow = QColor(base)
            glow.setAlpha(alpha)
            painter.setBrush(glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect.adjusted(-offset, -offset, offset, offset), 12, 12)

        # Fill
        painter.setBrush(base)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 10, 10)

        # Inner highlight
        highlight = QColor(255, 255, 255)
        highlight.setAlpha(40)
        painter.setBrush(highlight)
        painter.drawRoundedRect(rect.adjusted(4, 4, -4, -rect.height() // 2), 6, 6)

        if selected:
            # Bright selection ring
            ring = QPen(QColor(255, 255, 255))
            ring.setWidth(3)
            painter.setPen(ring)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(3, 3, -3, -3), 8, 8)

            # Extra selection glow
            for offset, alpha in ((10, 80), (6, 140)):
                glow = QColor(base)
                glow.setAlpha(alpha)
                painter.setBrush(glow)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(rect.adjusted(-offset, -offset, offset, offset), 12, 12)

        if hovered and progress > 0:
            # Index-finger dwell progress ring.
            arc_rect = rect.adjusted(-8, -8, 8, 8)
            span = int(progress * 360 * 16)
            pen = QPen(QColor(255, 255, 255))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(arc_rect, -90 * 16, span)

    def _draw_brush_selector(self, painter):
        brush = self.controller.brush
        rects = brush.swatch_rects(self.width(), self.height())
        if not rects:
            return

        first = rects[0][1]
        last = rects[-1][1]
        panel_pad = 16
        title_room = 42
        panel_x = first.left() - panel_pad
        panel_y = first.top() - panel_pad - title_room
        panel_w = first.width() + panel_pad * 2
        panel_h = (last.bottom() - first.top()) + panel_pad * 2 + title_room + 24  # extra for thickness

        panel = QRect(panel_x, panel_y, panel_w, panel_h)

        # Glass panel
        bg = QColor(8, 8, 14)
        bg.setAlpha(200)
        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(panel, 14, 14)

        # Neon border
        border = QColor(self.controller.palette.color())
        border.setAlpha(180)
        pen = QPen(border)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(panel.adjusted(2, 2, -2, -2), 12, 12)

        # Title
        title_font = QFont("Segoe UI", 10)
        title_font.setBold(True)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(title_font)
        painter.setPen(QColor(200, 200, 210))
        title_x = panel_x + (panel_w - QFontMetrics(title_font).horizontalAdvance("BRUSH")) // 2
        painter.drawText(title_x, panel_y + 24, "BRUSH")

        # Thickness readout
        thick_font = QFont("Segoe UI", 9)
        painter.setFont(thick_font)
        thick_text = f"W: {brush.selected.base_width + brush.thickness_offset}"
        painter.setPen(QColor(180, 180, 180))
        painter.drawText(
            panel_x + (panel_w - QFontMetrics(thick_font).horizontalAdvance(thick_text)) // 2,
            panel_y + panel_h - 8,
            thick_text,
        )

        # Dwell progress
        hover_name = self.controller._brush_hover_name
        hover_start = self.controller._brush_hover_start
        progress = 0.0
        if hover_name:
            progress = min(1.0, (time.time() - hover_start) / 0.3)

        color = self.controller.palette.color()
        for mode, rect in rects:
            self._draw_brush_swatch(
                painter, rect, mode, color,
                selected=(mode.name == brush.selected.name),
                hovered=(mode.name == hover_name),
                progress=progress if mode.name == hover_name else 0.0,
            )

    def _draw_brush_swatch(self, painter, rect, mode, color, selected=False, hovered=False, progress=0.0):
        """Draw a brush-mode swatch with a preview stroke."""
        base = QColor(color)

        # Glow
        for offset, alpha in ((12, 30), (8, 60), (4, 100)):
            glow = QColor(base)
            glow.setAlpha(alpha)
            painter.setBrush(glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect.adjusted(-offset, -offset, offset, offset), 10, 10)

        # Fill
        painter.setBrush(QColor(25, 25, 30))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 8, 8)

        # Preview stroke across the swatch
        preview = mode.theme(color, self.controller.brush.thickness_offset)
        pen = QPen(preview.stroke_color)
        pen.setWidth(min(rect.height() // 2, preview.stroke_width))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        y_mid = rect.center().y()
        painter.drawLine(rect.left() + 6, y_mid, rect.right() - 6, y_mid)

        # Label below swatch
        label_font = QFont("Segoe UI", 8)
        painter.setFont(label_font)
        painter.setPen(QColor(200, 200, 200))
        label_w = QFontMetrics(label_font).horizontalAdvance(mode.label)
        painter.drawText(rect.center().x() - label_w // 2, rect.bottom() + 12, mode.label)

        if selected:
            ring = QPen(QColor(255, 255, 255))
            ring.setWidth(2)
            painter.setPen(ring)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 6, 6)

        if hovered and progress > 0:
            arc_rect = rect.adjusted(-6, -6, 6, 6)
            span = int(progress * 360 * 16)
            pen = QPen(QColor(255, 255, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(arc_rect, -90 * 16, span)
