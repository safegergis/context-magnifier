import numpy as np
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QMenu,
)
from PySide6.QtCore import QTimer, Qt, Signal, QPoint, QRect
from PySide6.QtGui import QImage, QPixmap, QIcon, QScreen, QCursor, QAction


class ScreenMagnifier(QWidget):
    exit_signal = Signal()

    def __init__(self):
        super().__init__()
        self.scale_factor = 2.5  # Default scale factor
        self.zoom_increment = 0.1  # Zoom increment for each step

        # Set fixed dimensions for magnifier window
        self.window_width = 300
        self.window_height = 200

        # Calculate source region dimensions based on the scale factor
        self.update_source_dimensions()

        # set window attributes
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)
        self.setFixedSize(self.window_width, self.window_height)

        # Create a label to display the magnified region
        self.label = QLabel(self)
        self.label.setFixedSize(self.window_width, self.window_height)

        # Create an offset to prevent the window from covering what we're trying to magnify
        self.x_offset = 20
        self.y_offset = 20

        # Start a timer to update the magnifier
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_magnifier)
        self.timer.start(30)  # Update every 30 milliseconds

    def update_source_dimensions(self):
        """Update source region dimensions based on scale factor"""
        self.source_width = int(self.window_width / self.scale_factor)
        self.source_height = int(self.window_height / self.scale_factor)

    def update_magnifier(self):
        """Method for updating the window to follow cursor"""
        # Get the mouse position using Qt
        cursor_pos = QCursor.pos()
        mx, my = cursor_pos.x(), cursor_pos.y()
        # print(f"x: {mx}, y: {my}")

        # Position the window with offset to avoid capturing itself
        window_x = mx + self.x_offset
        window_y = my + self.y_offset

        # Check if the magnifier window would go offscreen and adjust if needed
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        
        if window_x + self.window_width > screen_width:
            window_x = mx - self.window_width - self.x_offset
        if window_y + self.window_height > screen_height:
            window_y = my - self.window_height - self.y_offset

        # Move the window before taking the screenshot
        self.move(window_x, window_y)

        # Give the window time to move before capturing
        QApplication.processEvents()

        # Calculate the region to capture centered on cursor
        half_source_width = self.source_width // 2
        half_source_height = self.source_height // 2

        magnify_x1 = max(0, mx - half_source_width)
        magnify_y1 = max(0, my - half_source_height)

        # Capture the screen using Qt
        screen = QApplication.primaryScreen()
        capture_rect = QRect(magnify_x1, magnify_y1, self.source_width, self.source_height)
        pixmap = screen.grabWindow(0, magnify_x1, magnify_y1, self.source_width, self.source_height)
        
        # Scale the pixmap to the desired size with high-quality interpolation
        pixmap = pixmap.scaled(
            self.window_width, 
            self.window_height,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.label.setPixmap(pixmap)

    def zoom_in(self):
        """Method for zooming in"""
        self.scale_factor = min(self.scale_factor + self.zoom_increment, 5)
        self.update_source_dimensions()

    def zoom_out(self):
        """Method for zooming out"""
        self.scale_factor = max(1.1, self.scale_factor - self.zoom_increment)
        self.update_source_dimensions()

    def keyPressEvent(self, event):
        """Handles key events for the app"""
        # Ctrl + ...
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # zoom in (ctrl + up)
            if event.key() == Qt.Key.Key_Up:
                self.zoom_in()

            # zoom out (ctrl + down)
            elif event.key() == Qt.Key.Key_Down:
                self.zoom_out()

        # hide magnifier (Esc)
        elif event.key() == Qt.Key.Key_Escape:
            self.hide()

    def closeEvent(self, event):
        self.exit_signal.emit()


async def run_zoom_window():
    import sys

    app = QApplication(sys.argv)
    magnifier = ScreenMagnifier()
    magnifier.show()

    # Connect the exit signal to the QApplication quit method
    magnifier.exit_signal.connect(app.quit)

    sys.exit(app.exec())

if __name__ == "__main__":
    run_zoom_window()