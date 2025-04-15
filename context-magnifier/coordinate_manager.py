import multiprocessing
import ctypes
import threading
import time
import numpy as np
from PySide6.QtGui import QCursor
import json
import os
from facial_recognition.main import EyeTracker
from ocr.main import ScreenAnalyzer


class CoordinateManager:
    """
    Manages coordinates from different sources (mouse, eye tracking) and importance map
    to determine the best magnification point.
    """

    def __init__(
        self,
        eye_tracking_enabled=False,
        importance_grid_enabled=False,
    ):
        self.eye_tracking_enabled = eye_tracking_enabled
        self.importance_grid_enabled = importance_grid_enabled

        # Initialize shared memory for eye tracker coordinates
        self.shared_eye_x = multiprocessing.Value(ctypes.c_double, 0.0)
        self.shared_eye_y = multiprocessing.Value(ctypes.c_double, 0.0)

        # Latest mouse coordinates
        self.mouse_x = 0
        self.mouse_y = 0

        # Eye tracker and screen analyzer
        self.eye_tracker = None
        self.screen_analyzer = None
        self.importance_matrix = None
        self.grid_cells = None
        self.cell_dimensions = None

        # Tracking objects
        self.tracking_thread = None
        self.dummy_thread = None
        self.stop_event = None

        # Continuous update thread
        self.continuous_update = False
        self.continuous_update_interval = 5.0  # seconds
        self.continuous_update_thread = None
        self.continuous_update_stop_event = threading.Event()

        # Calibration file
        self.calibration_file = None

    def load_calibration_and_track(self, calibration_file):
        """
        Load calibration data from a file and start eye tracking

        Args:
            calibration_file: Path to the calibration data JSON file

        Returns:
            True if successfully loaded and started tracking, False otherwise
        """
        try:
            # Stop any existing tracking first
            if self.eye_tracking_enabled:
                self.toggle_eye_tracking(False)

            # Check if file exists
            if not os.path.exists(calibration_file):
                print(f"Calibration file not found: {calibration_file}")
                return False

            # Load calibration data
            with open(calibration_file, "r") as f:
                cal_data = json.load(f)

            # Validate calibration data
            required_keys = [
                "calibrated_points",
                "calibration_screen_points",
                "screen_width",
                "screen_height",
            ]
            if not all(key in cal_data for key in required_keys):
                print(f"Invalid calibration data in {calibration_file}")
                return False

            # Save calibration file path
            self.calibration_file = calibration_file

            # Create eye tracker with calibration data
            self.eye_tracker = EyeTracker(
                callibrated_points=cal_data["calibrated_points"],
                screen_width=cal_data["screen_width"],
                screen_height=cal_data["screen_height"],
                calibration_screen_points=cal_data["calibration_screen_points"],
            )

            # Set calibration status
            self.eye_tracker.is_calibrated = True

            # Enable eye tracking
            self.eye_tracking_enabled = True

            # Start tracking with eye tracker
            def handle_gaze(coords):
                x, y = coords
                # Update shared memory values
                self.shared_eye_x.value = float(x)
                self.shared_eye_y.value = float(y)

            self.tracking_thread = self.eye_tracker.start_tracking(
                callback=handle_gaze, fps=10
            )

            print(f"Eye tracking started with calibration from {calibration_file}")
            return True

        except Exception as e:
            print(f"Error loading calibration and starting tracking: {e}")
            # Reset tracker state
            self.eye_tracker = None
            self.eye_tracking_enabled = False
            return False

    def setup_eye_tracking(self):
        """Set up eye tracking - either real or dummy"""
        # Check if we have a calibration file first
        if self.calibration_file and os.path.exists(self.calibration_file):
            return self.load_calibration_and_track(self.calibration_file)

        # Otherwise use dummy or do live calibration
        self.eye_tracker = EyeTracker()
        if self.eye_tracker.calibrate():

            def handle_gaze(coords):
                x, y = coords
                # Update shared memory values
                self.shared_eye_x.value = float(x)
                self.shared_eye_y.value = float(y)

            self.tracking_thread = self.eye_tracker.start_tracking(
                callback=handle_gaze, fps=4
            )
            print("Eye tracking started successfully")
        else:
            print("Eye tracking calibration failed")
            self.eye_tracking_enabled = False

    def toggle_eye_tracking(self, enabled):
        """Toggle eye tracking on/off"""
        # If turning on and not already enabled
        if enabled and not self.eye_tracking_enabled:
            self.eye_tracking_enabled = True
            self.setup_eye_tracking()
        # If turning off and currently enabled
        elif not enabled and self.eye_tracking_enabled:
            self.eye_tracking_enabled = False
            # Stop any running tracking
            if self.stop_event:
                self.stop_event.set()
            if self.eye_tracker:
                self.eye_tracker.stop_tracking()
                self.eye_tracker.stop_webcam()
                self.eye_tracker = None

    def toggle_importance_map(self, enabled):
        """Toggle importance map use on/off"""
        # If turning on and not already enabled
        if enabled and not self.importance_grid_enabled:
            self.importance_grid_enabled = True
            # Generate importance grid if not already done
            if self.importance_matrix is None:
                self.setup_importance_grid()
        # If turning off
        elif not enabled:
            self.importance_grid_enabled = False
            # Stop continuous update if running
            self.stop_continuous_updates()

    def setup_importance_grid(self, grid_x=9, grid_y=16):
        """Set up the screen analyzer and generate importance grid"""
        if self.screen_analyzer is None:
            self.screen_analyzer = ScreenAnalyzer(
                wait_seconds=4, grid_x=grid_x, grid_y=grid_y
            )
        else:
            # Update grid dimensions if they've changed
            self.screen_analyzer.grid_x = grid_x
            self.screen_analyzer.grid_y = grid_y

        # Generate the initial importance grid
        self.update_importance_grid()

    def update_importance_grid(self):
        """Update the importance grid by capturing the current screen and regenerating the grid"""
        if self.screen_analyzer is None:
            self.setup_importance_grid()
            return

        print("Capturing screen for importance analysis...")
        self.screen_analyzer.capture_screen()
        print("Generating importance grid (this may take a moment)...")
        self.grid_cells, self.cell_dimensions, self.importance_matrix = (
            self.screen_analyzer.generate_importance_grid()
        )
        print("Importance grid updated")

    def find_important_area_near(self, x, y, radius=200, importance_threshold=0.7):
        """Find the most important point within a radius of the given coordinates,
        using a weighted average based on importance values, ignoring cells with
        importance below the threshold"""
        if not self.importance_grid_enabled or self.importance_matrix is None:
            return x, y

        # Convert coordinates to grid cells
        cell_width, cell_height = self.cell_dimensions
        cell_x = int(x / cell_width)
        cell_y = int(y / cell_height)

        # Define the search area (bounded by the grid size)
        grid_y, grid_x = self.importance_matrix.shape
        radius_cells_x = min(int(radius / cell_width), grid_x // 2)
        radius_cells_y = min(int(radius / cell_height), grid_y // 2)

        start_x = max(0, cell_x - radius_cells_x)
        end_x = min(grid_x, cell_x + radius_cells_x + 1)
        start_y = max(0, cell_y - radius_cells_y)
        end_y = min(grid_y, cell_y + radius_cells_y + 1)

        # Extract the submatrix of importance values in the search area
        search_area = self.importance_matrix[start_y:end_y, start_x:end_x]

        if search_area.size == 0:
            return x, y

        # Create mask for cells that exceed the importance threshold
        # Normalize search area to 0-1 range if not already normalized
        if np.max(search_area) > 1.0:
            normalized_search_area = search_area / np.max(search_area)
        else:
            normalized_search_area = search_area

        importance_mask = normalized_search_area >= importance_threshold

        # If no cells meet the threshold, return original coordinates
        if not np.any(importance_mask):
            return x, y

        # Filter search area to only include important cells
        filtered_search_area = np.copy(search_area)
        filtered_search_area[~importance_mask] = 0

        # Calculate weights based on filtered importance values
        epsilon = 1e-6
        weights = filtered_search_area + epsilon

        # Normalize weights so they sum to 1
        weights = weights / np.sum(weights)

        # Create meshgrid of coordinates
        y_indices, x_indices = np.indices(search_area.shape)

        # Calculate weighted average coordinates (only for important cells)
        weighted_x = np.sum(x_indices * weights)
        weighted_y = np.sum(y_indices * weights)

        # Convert back to global grid coordinates
        weighted_cell_x = start_x + weighted_x
        weighted_cell_y = start_y + weighted_y

        # Convert from grid coordinates to screen coordinates
        weighted_x_screen = (weighted_cell_x + 0.5) * cell_width
        weighted_y_screen = (weighted_cell_y + 0.5) * cell_height

        return weighted_x_screen, weighted_y_screen

    def get_coordinates(self):
        cursor_pos = QCursor.pos()
        mouse_x, mouse_y = cursor_pos.x(), cursor_pos.y()

        # Initialize x and y with mouse coordinates
        x, y = mouse_x, mouse_y

        # If importance grid is enabled, find important area
        if self.importance_grid_enabled and self.importance_matrix is not None:
            x, y = self.find_important_area_near(mouse_x, mouse_y)

        # If eye tracking is enabled, use eye coordinates
        if self.eye_tracking_enabled:
            x, y = self.shared_eye_x.value, self.shared_eye_y.value

        return x, y

    def _continuous_update_loop(self):
        """Background thread function that continuously updates the importance map"""
        print("Starting continuous importance map updates")
        while not self.continuous_update_stop_event.is_set():
            try:
                if self.importance_grid_enabled:
                    self.update_importance_grid()
                # Sleep for the specified interval
                self.continuous_update_stop_event.wait(self.continuous_update_interval)
            except Exception as e:
                print(f"Error in continuous update thread: {e}")
                # Sleep briefly to avoid rapid error loops
                time.sleep(1.0)

    def start_continuous_updates(self, interval=5.0):
        """Start a background thread that continuously updates the importance map

        Args:
            interval: Time between updates in seconds
        """
        # Don't start if already running
        if self.continuous_update:
            return

        self.continuous_update = True
        self.continuous_update_interval = interval
        self.continuous_update_stop_event.clear()

        if (
            self.continuous_update_thread is None
            or not self.continuous_update_thread.is_alive()
        ):
            self.continuous_update_thread = threading.Thread(
                target=self._continuous_update_loop
            )
            self.continuous_update_thread.daemon = True
            self.continuous_update_thread.start()

    def stop_continuous_updates(self):
        """Stop the continuous update thread"""
        if not self.continuous_update:
            return

        self.continuous_update = False
        self.continuous_update_stop_event.set()

        if self.continuous_update_thread and self.continuous_update_thread.is_alive():
            self.continuous_update_thread.join(timeout=1.0)
            self.continuous_update_thread = None

    def set_continuous_update_interval(self, interval):
        """Set the interval between continuous updates

        Args:
            interval: Time between updates in seconds
        """
        self.continuous_update_interval = max(1.0, interval)  # Minimum 1 second

    def cleanup(self):
        """Clean up resources"""
        self.mouse_thread_active = False
        if self.mouse_thread:
            self.mouse_thread.join(timeout=1.0)

        if self.eye_tracking_enabled:
            if self.stop_event:
                self.stop_event.set()
            if self.dummy_thread:
                self.dummy_thread.join(timeout=1.0)
            if self.eye_tracker:
                self.eye_tracker.stop_tracking()
                self.eye_tracker.stop_webcam()

        # Stop continuous updates
        self.stop_continuous_updates()
