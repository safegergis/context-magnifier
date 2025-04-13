import sys

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget
)

from __feature__ import snake_case, true_property

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    sys.exit(app.exec())
