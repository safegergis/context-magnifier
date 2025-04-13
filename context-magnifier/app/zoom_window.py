import numpy as np
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QMenu,
)
from PySide6.QtCore import QTimer, Qt, Signal, QPoint, QRect
from PySide6.QtGui import QImage, QPixmap, QIcon, QScreen, QCursor, QAction
from typing import Callable, Tuple


class ScreenMagnifier(QWidget):
    exit_signal = Signal()
    toggle_eye_tracking_signal = Signal(bool)
    toggle_importance_map_signal = Signal(bool)
    update_importance_map_signal = Signal()
    toggle_continuous_updates_signal = Signal(bool)
    set_update_interval_signal = Signal(float)

    def __init__(
        self,
        coord_source: Callable[[], Tuple[int, int]] | None = None,
        scale_factor: float = 2.5,
        zoom_increment: float = 0.1,
        window_width: int = 600,
        window_height: int = 400,
        follow_mouse: bool = False,
        fixed_position: bool = False,
    ):
        super().__init__()
        self.coord_source = coord_source
        self.scale_factor = scale_factor  # Default scale factor
        self.zoom_increment = zoom_increment  # Zoom increment for each step
        self.follow_mouse = follow_mouse  # Whether to position window at mouse cursor
        self.fixed_position = fixed_position  # Whether to fix position at bottom right

        # Set fixed dimensions for magnifier window
        self.window_width = window_width
        self.window_height = window_height

        # Feature toggle states
        self.eye_tracking_enabled = False
        self.importance_map_enabled = True
        self.continuous_updates_enabled = False

        # Calculate source region dimensions based on the scale factor
        self.update_source_dimensions()

        # set window attributes
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)
        self.setFixedSize(self.window_width, self.window_height)

        # Create a label to display the magnified region
        self.label = QLabel(self)
        self.label.setFixedSize(self.window_width, self.window_height)

        # Setup context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Create an offset to prevent the window from covering what we're trying to magnify
        self.x_offset = 20
        self.y_offset = 20

        # Start a timer to update the magnifier
        self.timer = QTimer(self)
        try:
            self.timer.timeout.connect(self.update_magnifier)
            self.timer.start(30)  # Update every 30 milliseconds
        except Exception as e:
            print(f"Error connecting timer: {e}")

    def show_context_menu(self, position):
        """Show the context menu with options to toggle features"""
        menu = QMenu(self)

        # Eye tracking toggle
        eye_tracking_action = QAction("Eye Tracking", self, checkable=True)
        eye_tracking_action.setChecked(self.eye_tracking_enabled)
        eye_tracking_action.triggered.connect(self.toggle_eye_tracking)
        menu.addAction(eye_tracking_action)

        # Importance map toggle
        importance_map_action = QAction("Use Importance Map", self, checkable=True)
        importance_map_action.setChecked(self.importance_map_enabled)
        importance_map_action.triggered.connect(self.toggle_importance_map)
        menu.addAction(importance_map_action)

        # Fixed position toggle
        fixed_position_action = QAction("Fixed Position", self, checkable=True)
        fixed_position_action.setChecked(self.fixed_position)
        fixed_position_action.triggered.connect(self.toggle_fixed_position)
        menu.addAction(fixed_position_action)

        # Update importance map action
        if self.importance_map_enabled:
            update_map_action = QAction("Update Importance Map", self)
            update_map_action.triggered.connect(self.update_importance_map)
            menu.addAction(update_map_action)

            # Continuous updates toggle
            continuous_updates_action = QAction(
                "Continuous Updates", self, checkable=True
            )
            continuous_updates_action.setChecked(self.continuous_updates_enabled)
            continuous_updates_action.triggered.connect(self.toggle_continuous_updates)
            menu.addAction(continuous_updates_action)

            # Update interval submenu
            interval_menu = QMenu("Update Interval", self)

            # Create interval options
            intervals = [1, 2, 5, 10, 30]
            for interval in intervals:
                interval_action = QAction(f"{interval} seconds", self)
                interval_action.triggered.connect(
                    lambda checked, i=interval: self.set_update_interval(i)
                )
                interval_menu.addAction(interval_action)

            menu.addMenu(interval_menu)

        # Follow mouse toggle
        follow_mouse_action = QAction("Follow Mouse", self, checkable=True)
        follow_mouse_action.setChecked(self.follow_mouse)
        follow_mouse_action.triggered.connect(self.toggle_follow_mouse)
        menu.addAction(follow_mouse_action)

        # Separator
        menu.addSeparator()

        # Zoom controls
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        menu.addAction(zoom_out_action)

        # Separator
        menu.addSeparator()

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)

        # Show the menu
        menu.exec(self.mapToGlobal(position))

    def toggle_follow_mouse(self, checked):
        """Toggle whether window follows mouse position"""
        self.follow_mouse = checked
        print(f"Follow mouse {'enabled' if checked else 'disabled'}")

    def toggle_eye_tracking(self, checked):
        """Toggle eye tracking on/off"""
        self.eye_tracking_enabled = checked
        self.toggle_eye_tracking_signal.emit(checked)
        print(f"Eye tracking {'enabled' if checked else 'disabled'}")

    def toggle_importance_map(self, checked):
        """Toggle importance map on/off"""
        self.importance_map_enabled = checked
        self.toggle_importance_map_signal.emit(checked)
        print(f"Importance map {'enabled' if checked else 'disabled'}")

        # If importance map is disabled, disable continuous updates too
        if not checked and self.continuous_updates_enabled:
            self.continuous_updates_enabled = False
            self.toggle_continuous_updates_signal.emit(False)

    def update_importance_map(self):
        """Update the importance map"""
        print("Updating importance map...")
        self.update_importance_map_signal.emit()

    def toggle_continuous_updates(self, checked):
        """Toggle continuous updates on/off"""
        self.continuous_updates_enabled = checked
        self.toggle_continuous_updates_signal.emit(checked)
        print(f"Continuous updates {'enabled' if checked else 'disabled'}")

    def set_update_interval(self, interval):
        """Set the interval between continuous updates"""
        print(f"Setting update interval to {interval} seconds")
        self.set_update_interval_signal.emit(float(interval))

    def update_source_dimensions(self):
        """Update source region dimensions based on scale factor"""
        self.source_width = int(self.window_width / self.scale_factor)
        self.source_height = int(self.window_height / self.scale_factor)

    def update_magnifier(self):
        """Method for updating the window to follow cursor and magnify content at specified coordinates"""
        # Get the mouse position for window positioning
        try:
            cursor_pos = QCursor.pos()
            mouse_x, mouse_y = cursor_pos.x(), cursor_pos.y()
        except Exception as e:
            print(f"Error getting cursor position: {e}")
            mouse_x, mouse_y = 0, 0

        # Get coordinates for content to magnify
        if not self.coord_source:
            # If no coord_source, use mouse position for content as well
            content_x, content_y = mouse_x, mouse_y
        else:
            # Use coordinate manager's coordinates for the content
            content_x, content_y = self.coord_source()

        # Determine window position
        if self.fixed_position:
            # Get screen dimensions for fixed positioning
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()

            # Position in bottom right with a small margin
            window_x = screen_width - self.window_width - 20
            window_y = screen_height - self.window_height - 20
        elif self.follow_mouse:
            window_x = mouse_x
            window_y = mouse_y
        else:
            window_x = content_x
            window_y = content_y

        # Check if the magnifier window would go offscreen and adjust if needed
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # Prevent window from going off the right or left sides
        if window_x + self.window_width > screen_width:
            window_x = window_x - self.window_width
        if window_x < 0:
            window_x = 0

        # Prevent window from going off the bottom or top sides
        if window_y + self.window_height > screen_height:
            window_y = window_y - self.window_height
        if window_y < 0:
            window_y = 0

        # Move the window before taking the screenshot
        self.move(window_x, window_y)

        # Give the window time to move before capturing
        QApplication.processEvents()

        # Calculate the region to capture centered on content coordinates
        half_source_width = self.source_width // 2
        half_source_height = self.source_height // 2

        magnify_x1 = max(0, content_x - half_source_width)
        magnify_y1 = max(0, content_y - half_source_height)

        # Capture the screen using Qt
        screen = QApplication.primaryScreen()
        capture_rect = QRect(
            magnify_x1, magnify_y1, self.source_width, self.source_height
        )
        pixmap = screen.grabWindow(
            0, magnify_x1, magnify_y1, self.source_width, self.source_height
        )

        # Scale the pixmap to the desired size with high-quality interpolation
        pixmap = pixmap.scaled(
            self.window_width,
            self.window_height,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
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

    def toggle_fixed_position(self, checked):
        """Toggle whether window stays in fixed position"""
        self.fixed_position = checked
        # If fixed position is enabled, disable follow mouse
        if checked and self.follow_mouse:
            self.follow_mouse = False
        print(f"Fixed position {'enabled' if checked else 'disabled'}")

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

            # update importance map (ctrl + i)
            elif event.key() == Qt.Key.Key_I:
                if self.importance_map_enabled:
                    self.update_importance_map()

            # toggle continuous updates (ctrl + u)
            elif event.key() == Qt.Key.Key_U:
                if self.importance_map_enabled:
                    self.toggle_continuous_updates(not self.continuous_updates_enabled)

            # toggle follow mouse (ctrl + f)
            elif event.key() == Qt.Key.Key_F:
                self.toggle_follow_mouse(not self.follow_mouse)

            # toggle fixed position (ctrl + p)
            elif event.key() == Qt.Key.Key_P:
                self.toggle_fixed_position(not self.fixed_position)

        # hide magnifier (Esc)
        elif event.key() == Qt.Key.Key_Escape:
            self.hide()

    def closeEvent(self, event):
        self.exit_signal.emit()


def run_zoom_window(
    coord_source: Callable[[], Tuple[int, int]] | None = None,
    scale_factor: float = 2.5,
    zoom_increment: float = 0.1,
    window_width: int = 600,
    window_height: int = 400,
    follow_mouse: bool = False,
    fixed_position: bool = False,
):
    import sys

    app = QApplication(sys.argv)
    magnifier = ScreenMagnifier(
        coord_source,
        scale_factor,
        zoom_increment,
        window_width,
        window_height,
        follow_mouse,
        fixed_position,
    )
    magnifier.show()

    # Connect the exit signal to the QApplication quit method
    magnifier.exit_signal.connect(app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    run_zoom_window()
