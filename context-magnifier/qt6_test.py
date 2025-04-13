import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QToolBar, QPushButton

class MinimalTransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        toolbar.addWidget(close_button)
        
        self.showFullScreen()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MinimalTransparentWindow()
    window.show()
    sys.exit(app.exec())
