from PyQt6.QtGui import QImage, QPixmap


class Renderer:
    """Helpers for converting OpenCV frames to Qt pixmaps."""

    @staticmethod
    def cv_frame_to_pixmap(frame):
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        image = QImage(
            frame.tobytes(),
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_BGR888,
        )
        return QPixmap.fromImage(image)
