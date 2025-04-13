import sys
from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget
)
from PySide6.QtGui import QPainter, QScreen, QCursor, QColor, QPixmap

class MagnifierWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Set window to be frameless and stay on top
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        # Make the window background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set up the layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add a close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)


        self.magnifier_active = False
        self.magnification_factor = 2.0
        self.magnification_size = 200
        self.magnifier_position = QPoint(0, 0)

        self.setMouseTracking(True)
        self.showFullScreen()

    def paintEvent(self, event):
        super().painEvent(event)

        if not self.magnifier_active:
            return

        painter = QPainter(self)

        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(0)

        half_size = self.magnifier_size // 2
        half_scaled = int(half_size / self.magnification_factor)

        source_rect = QRect(
            self.magnifier_position.x() - half_scaled,
            self.magnifier_position.y() - half_scaled,
            half_scaled * 2,
            half_scaled * 2
        )

        target_rect = QRect(
            self.magnifier_position.x() - half_size,
            self.magnifier_position.y() - half_size,
            self.magnifier_size,
            self.magnifier_size
        )

        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(target_rect, pixmap, source_rect)

        painter.setPen(QColor(255, 255, 255, 180))
        painter.drawEllipse(target_rect)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MagnifierWidget()
    widget.show()
    sys.exit(app.exec())
