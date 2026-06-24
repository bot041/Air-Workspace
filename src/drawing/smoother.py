class Smoother:
    """Moving-average point smoother."""

    def __init__(self, window=4):
        self.window = window
        self._buf = []

    def add(self, point):
        self._buf.append(point)
        if len(self._buf) > self.window:
            self._buf.pop(0)
        xs = [p[0] for p in self._buf]
        ys = [p[1] for p in self._buf]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def reset(self):
        self._buf.clear()
