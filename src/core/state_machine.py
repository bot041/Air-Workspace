class State:
    IDLE = "IDLE"
    NAVIGATING = "NAVIGATING"
    DRAWING = "DRAWING"
    OBJECT_OPEN = "OBJECT_OPEN"
    SELECTED = "SELECTED"
    DRAGGING = "DRAGGING"
    ERASING = "ERASING"


class StateMachine:
    def __init__(self):
        self.state = State.IDLE

    def transition(self, new_state):
        self.state = new_state
