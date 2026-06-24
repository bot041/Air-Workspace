import time
from drawing.stroke import Stroke


class StrokeObject:
    """A drawable object composed of one or more strokes."""

    _id_counter = 0

    def __init__(self, strokes=None, theme="white", brush="ink", thickness_offset=0):
        StrokeObject._id_counter += 1
        self.object_id = StrokeObject._id_counter
        self.strokes = strokes or []
        self.position = (0.0, 0.0)
        self.bounding_box = (0, 0, 0, 0)
        self.z_index = 0
        self.selected = False
        self.panel_location = "workspace"
        self.timestamp = time.time()
        self.theme = theme
        self.brush = brush
        self.thickness_offset = thickness_offset
        self._update_bbox()

    def add_stroke(self, stroke: Stroke):
        self.strokes.append(stroke)
        self._update_bbox()

    def _update_bbox(self):
        all_pts = [p for s in self.strokes for p in s.points]
        if not all_pts:
            self.bounding_box = (self.position[0], self.position[1], 0, 0)
            return
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        x = min(xs)
        y = min(ys)
        self.position = (x, y)
        self.bounding_box = (x, y, max(xs) - x, max(ys) - y)

    def translate(self, dx, dy):
        for stroke in self.strokes:
            stroke.translate(dx, dy)
        self._update_bbox()

    def draw(self, painter, theme):
        for stroke in self.strokes:
            theme.draw_stroke(painter, stroke, self.selected)

    def contains(self, point, padding=8):
        x, y, w, h = self.bounding_box
        return (
            x - padding <= point[0] <= x + w + padding
            and y - padding <= point[1] <= y + h + padding
        )
