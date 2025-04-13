import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QPushButton, QGridLayout, QWidget, QFormLayout,
    QLabel,
    QLineEdit
)

class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        central_widget = QWidget()
        grid_layout = QGridLayout()
        central_widget.setLayout(grid_layout)
        self.setCentralWidget(central_widget)

        # Configuration Form
        
        test_label = QLabel("Test:")
        test_input = QLineEdit()
        test_input.setPlaceholderText("Enter Value")

        grid_layout.addWidget(test_label, 1, 1)
        grid_layout.addWidget(test_input, 1, 2)

        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        toolbar.addWidget(close_button)

        self.showFullScreen()


async def run_main_window():
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_main_window()