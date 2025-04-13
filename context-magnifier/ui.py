import sys
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QGridLayout, QWidget, 
    QLabel, QLineEdit, QScrollArea, QVBoxLayout, QSizePolicy
)
from PySide6.QtSvgWidgets import QSvgWidget

class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        central_widget = QWidget()
        grid_layout = QGridLayout()
        central_widget.setLayout(grid_layout)
        self.setCentralWidget(central_widget)

        # SVG widgets
        top_widget = QSvgWidget("assets/top.svg")
        top_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        bottom_widget = QSvgWidget("assets/bottom.svg")
        bottom_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) 
        scroll_area.setStyleSheet("background: transparent; border: 1px solid white;")

        scroll_content = QWidget()
        scroll_content.setLayout(QVBoxLayout())

        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent; 
                border: 1px solid white;
                min-width: 200px;
                max-width: 200px;
                min-height: 200px;
                max-height: 200px;
            }
        """)

        for i in range(20):
            label = QLabel(f"Item {i+1}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: white; font-size: 16px; padding: 10px;")
            scroll_content.layout().addWidget(label)

        scroll_area.setWidget(scroll_content)

        # Force square aspect ratio
        scroll_area.setMinimumSize(300, 300)  
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Configuration Form
        test_label = QLabel("Test:")
        test_input = QLineEdit()
        test_input.setPlaceholderText("Enter Value")
        
        grid_layout.addWidget(top_widget) 

        grid_layout.setAlignment(
            top_widget, 
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )
        
        # grid_layout.addWidget(test_label)
        # grid_layout.addWidget(test_input)
        grid_layout.addWidget(scroll_area)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        grid_layout.addWidget(close_button)

        grid_layout.addWidget(bottom_widget)
        grid_layout.setAlignment(
            bottom_widget,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
        )
        
        self.showFullScreen()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()
    sys.exit(app.exec())