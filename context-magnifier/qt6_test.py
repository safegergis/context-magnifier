import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget
)

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Set window to be frameless and stay on top
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        # Make the window background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set up the layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add some content (optional)
        label = QLabel("Transparent Fullscreen Window")
        label.setStyleSheet("color: white; font-size: 24px;")
        layout.addWidget(label)

        # Add a close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        # Show fullscreen
        self.showFullScreen()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    sys.exit(app.exec())
