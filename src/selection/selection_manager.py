class SelectionManager:
    """Tracks the selected object and the natural grab offset."""

    def __init__(self):
        self.selected = None
        self.drag_offset = (0.0, 0.0)
        self.start_cursor = (0.0, 0.0)

    def select(self, obj, cursor):
        if self.selected is not None and self.selected != obj:
            self.clear()
        self.selected = obj
        self.selected.selected = True
        self.start_cursor = cursor
        self.drag_offset = (obj.position[0] - cursor[0], obj.position[1] - cursor[1])

    def clear(self):
        if self.selected is not None:
            self.selected.selected = False
        self.selected = None
        self.drag_offset = (0.0, 0.0)
        self.start_cursor = (0.0, 0.0)
