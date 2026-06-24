import cv2


class Webcam:
    """Simple OpenCV webcam wrapper."""

    def __init__(self, index=0, width=640, height=480, fps=30):
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or width
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or height

    def read(self):
        ok, frame = self.cap.read()
        return frame if ok else None

    def release(self):
        self.cap.release()
