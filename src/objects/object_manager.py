class ObjectManager:
    """Owns workspace objects and output-tray objects."""

    def __init__(self):
        self.objects = []
        self.tray_objects = []
        self._z = 1

    def add_workspace_object(self, obj):
        obj.panel_location = "workspace"
        obj.z_index = self._z
        self._z += 1
        self.objects.append(obj)

    def remove_object(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)
        if obj in self.tray_objects:
            self.tray_objects.remove(obj)

    def move_to_tray(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)
        if obj not in self.tray_objects:
            self.tray_objects.append(obj)
        obj.panel_location = "tray"

    def move_to_workspace(self, obj, position=None):
        if obj in self.tray_objects:
            self.tray_objects.remove(obj)
        if obj not in self.objects:
            obj.z_index = self._z
            self._z += 1
            self.objects.append(obj)
        obj.panel_location = "workspace"
        if position is not None:
            dx = position[0] - obj.position[0]
            dy = position[1] - obj.position[1]
            obj.translate(dx, dy)

    def bring_to_front(self, obj):
        if obj in self.objects:
            obj.z_index = self._z
            self._z += 1

    def top_workspace_object_at(self, point):
        for obj in sorted(self.objects, key=lambda o: o.z_index, reverse=True):
            if obj.contains(point):
                return obj
        return None

    def tray_object_at(self, point, tray_width, tray_height):
        n = len(self.tray_objects)
        if n == 0 or tray_width == 0:
            return None
        slot_w = tray_width / n
        idx = int(point[0] / slot_w)
        if 0 <= idx < n:
            return self.tray_objects[idx]
        return None
