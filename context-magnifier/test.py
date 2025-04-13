import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter

class TransparentWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Remove window decorations (title bar, etc.)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # Enable translucency
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Optional: Make the background transparent
        self.resize(400, 300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Semi-transparent red rectangle (for example)
        painter.setBrush(QColor(255, 0, 0, 128))  # RGBA
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()
    sys.exit(app.exec())
