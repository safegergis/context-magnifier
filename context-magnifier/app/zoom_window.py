import cv2
import numpy as np
import pyautogui
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QMenu,
    QAction,
    QSystemTrayIcon,
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QIcon


class ScreenMagnifier(QWidget):
    exit_signal = pyqtSignal()

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
            self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
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

        # Create a system tray icon
        self.create_context_menu()
        self.tray_icon = QSystemTrayIcon(self)
        # Use fallback icon if icon.png is missing
        try:
            self.tray_icon.setIcon(QIcon("icon.png"))
        except:
            self.tray_icon.setIcon(QIcon.fromTheme("zoom-fit-best"))

        # Set the context menu for the system tray icon
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def update_source_dimensions(self):
        """Update source region dimensions based on scale factor"""
        self.source_width = int(self.window_width / self.scale_factor)
        self.source_height = int(self.window_height / self.scale_factor)

    def create_context_menu(self):
        # Create a context menu for the system tray icon
        self.tray_menu = QMenu(self)
        self.zoom_in_action = QAction("Zoom In      (Ctrl+Up)", self)
        self.zoom_out_action = QAction("Zoom Out    (Ctrl+Down)", self)
        self.hide_action = QAction("Hide            (Esc)", self)
        self.unhide_action = QAction("Unhide", self)
        self.exit_action = QAction("Exit", self)

        # Connect actions to their respective slots
        self.zoom_in_action.triggered.connect(self.zoom_in)
        self.zoom_out_action.triggered.connect(self.zoom_out)
        self.hide_action.triggered.connect(self.hide)
        self.unhide_action.triggered.connect(self.show)
        self.exit_action.triggered.connect(self.close)

        # Add actions to the context menu
        self.tray_menu.addAction(self.zoom_in_action)
        self.tray_menu.addAction(self.zoom_out_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.hide_action)
        self.tray_menu.addAction(self.unhide_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.exit_action)

    def update_magnifier(self):
        """Method for updating the window to follow cursor"""
        # Get the mouse position
        mx, my = pyautogui.position()

        # Position the window with offset to avoid capturing itself
        window_x = mx + self.x_offset
        window_y = my + self.y_offset

        # Check if the magnifier window would go offscreen and adjust if needed
        screen_width, screen_height = pyautogui.size()
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

        # Capture the screen
        screen = pyautogui.screenshot(
            region=(magnify_x1, magnify_y1, self.source_width, self.source_height)
        )

        # Convert the screenshot to a NumPy array
        frame = np.array(screen)

        # Convert BGR to RGB (OpenCV uses BGR, but QImage expects RGB)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Resize the frame using high-quality interpolation
        magnified_frame = cv2.resize(
            frame,
            (self.window_width, self.window_height),
            interpolation=cv2.INTER_LANCZOS4,
        )

        # Convert the magnified frame to QImage and display it
        height, width, channel = magnified_frame.shape
        bytesPerLine = 3 * width
        qImg = QImage(
            magnified_frame.data, width, height, bytesPerLine, QImage.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qImg)
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
        if event.modifiers() == Qt.ControlModifier:
            # zoom in (ctrl + up)
            if event.key() == Qt.Key_Up:
                self.zoom_in()

            # zoom out (ctrl + down)
            elif event.key() == Qt.Key_Down:
                self.zoom_out()

        # hide magnifier (Esc)
        elif event.key() == Qt.Key_Escape:
            self.hide()

    def closeEvent(self, event):
        self.exit_signal.emit()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    magnifier = ScreenMagnifier()
    magnifier.show()

    # Connect the exit signal to the QApplication quit method
    magnifier.exit_signal.connect(app.quit)

    sys.exit(app.exec_())
