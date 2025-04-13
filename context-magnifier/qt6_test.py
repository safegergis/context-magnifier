import sys
from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget
)
from PySide6.QtGui import QPixmap, QPainter, QScreen, QCursor, QColor

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
        
        # Add a close button in the top-right corner
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        close_button.setFixedSize(80, 30)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        # Magnifier settings
        self.magnifier_active = False
        self.magnification_factor = 2.0
        self.magnifier_size = 200
        self.magnifier_position = QPoint(0, 0)
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
        # Show fullscreen
        self.showFullScreen()
    
    def keyPressEvent(self, event):
        # Toggle magnifier with spacebar
        if event.key() == Qt.Key.Key_Space:
            self.magnifier_active = not self.magnifier_active
            self.update()
        # Increase magnification with + key
        elif event.key() == Qt.Key.Key_Plus:
            self.magnification_factor += 0.5
            self.update()
        # Decrease magnification with - key
        elif event.key() == Qt.Key.Key_Minus:
            if self.magnification_factor > 1.0:
                self.magnification_factor -= 0.5
            self.update()
        # Exit on Escape
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.magnifier_active:
            self.magnifier_position = event.position().toPoint()
            self.update()
        super().mouseMoveEvent(event)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if not self.magnifier_active:
            return
            
        painter = QPainter(self)
        
        # Capture screen content
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(0)
        
        # Calculate source and target rectangles for magnification
        half_size = self.magnifier_size // 2
        half_scaled = int(half_size / self.magnification_factor)
        
        # Source rectangle (area to magnify)
        source_rect = QRect(
            self.magnifier_position.x() - half_scaled,
            self.magnifier_position.y() - half_scaled,
            half_scaled * 2,
            half_scaled * 2
        )
        
        # Target rectangle (where to draw magnified content)
        target_rect = QRect(
            self.magnifier_position.x() - half_size,
            self.magnifier_position.y() - half_size,
            self.magnifier_size,
            self.magnifier_size
        )
        
        # Draw magnified content
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(target_rect, pixmap, source_rect)
        
        # Draw border around magnifier
        painter.setPen(QColor(255, 255, 255, 180))
        painter.drawEllipse(target_rect)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MagnifierWidget()
    widget.show()
    sys.exit(app.exec())
