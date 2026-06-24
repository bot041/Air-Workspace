import math
from drawing.stroke import Stroke


class Eraser:
    """Removes stroke points near the cursor or along a movement path."""

    def __init__(self, radius=28):
        self.radius = radius

    def erase_at(self, point, objects, prev=None):
        """Erase a circular area at ``point``.

        If ``prev`` is provided, the eraser is swept along the line segment
        from ``prev`` to ``point`` so fast palm swipes still remove strokes
        rather than leaving dotted gaps.
        """
        if prev is None or self._dist(point, prev) < 1e-6:
            return self._erase_points(objects, point)
        return self._erase_segment(objects, prev, point)

    def _erase_points(self, objects, center):
        return self._filter_objects(objects, lambda p: self._dist(p, center) <= self.radius)

    def _erase_segment(self, objects, a, b):
        return self._filter_objects(objects, lambda p: self._point_segment_distance(p, a, b) <= self.radius)

    def _filter_objects(self, objects, should_erase):
        survivors = []
        for obj in objects:
            new_strokes = []
            for stroke in obj.strokes:
                for segment in self._split_segments(stroke.points, should_erase):
                    if len(segment) >= 2:
                        new_strokes.append(Stroke(segment))
            obj.strokes = new_strokes
            if obj.strokes:
                obj._update_bbox()
                survivors.append(obj)
        return survivors

    def _split_segments(self, points, should_erase):
        segments = []
        current = []
        for p in points:
            if should_erase(p):
                if len(current) >= 2:
                    segments.append(current)
                current = []
            else:
                current.append(p)
        if len(current) >= 2:
            segments.append(current)
        return segments

    @staticmethod
    def _dist(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    @staticmethod
    def _point_segment_distance(p, a, b):
        """Shortest distance from point p to the segment a-b."""
        ax, ay = a
        bx, by = b
        px, py = p
        if ax == bx and ay == by:
            return math.hypot(px - ax, py - ay)

        # Project p onto the line ab, clamped to the segment.
        abx = bx - ax
        aby = by - ay
        t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / (abx * abx + aby * aby)))
        projx = ax + t * abx
        projy = ay + t * aby
        return math.hypot(px - projx, py - projy)
