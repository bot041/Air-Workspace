import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QApplication, QMainWindow

from core.app_controller import AppController
from panels.workspace import Workspace


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AirScript MVP")

        self.workspace = Workspace()
        self.setCentralWidget(self.workspace)

        self.controller = AppController(self.workspace, parent=self)
        self.workspace.controller = self.controller

        self._build_menu()

    def _build_menu(self):
        menu = self.menuBar()
        app_menu = menu.addMenu("AirScript")

        color_menu = app_menu.addMenu("Colors")
        for i, key in enumerate(self.controller.palette.ORDER, start=1):
            action = QAction(f"{key.capitalize()} ({i})", self)
            action.setShortcut(QKeySequence(str(i)))
            action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
            action.triggered.connect(lambda checked=False, k=key: self.controller.select_color(k))
            color_menu.addAction(action)

        brush_menu = app_menu.addMenu("Brush")
        for i, mode in enumerate(self.controller.brush.ORDER, start=1):
            action = QAction(f"{mode.label} (F{i})", self)
            action.setShortcut(QKeySequence(f"F{i}"))
            action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
            action.triggered.connect(lambda checked=False, n=mode.name: self.controller.select_brush(n))
            brush_menu.addAction(action)

        thicker_action = QAction("Thicker (+)", self)
        thicker_action.setShortcut(QKeySequence("+"))
        thicker_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        thicker_action.triggered.connect(lambda: self.controller.adjust_thickness(1))
        brush_menu.addAction(thicker_action)

        thinner_action = QAction("Thinner (-)", self)
        thinner_action.setShortcut(QKeySequence("-"))
        thinner_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        thinner_action.triggered.connect(lambda: self.controller.adjust_thickness(-1))
        brush_menu.addAction(thinner_action)

        app_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Esc"))
        quit_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        quit_action.triggered.connect(self.close)
        app_menu.addAction(quit_action)

    def closeEvent(self, event):
        self.controller.cleanup()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.showFullScreen()

    if "--smoke-test" in sys.argv:
        QTimer.singleShot(3000, window.close)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
