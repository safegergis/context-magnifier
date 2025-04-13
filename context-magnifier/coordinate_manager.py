import multiprocessing
import ctypes
import threading
import time
import math
import tkinter as tk  # For getting screen dimensions
import pyautogui  # For getting mouse position
import numpy as np

from facial_recognition.main import EyeTracker
from ocr.main import ScreenAnalyzer


def create_dummy_eye_tracker(shared_x, shared_y, fps=20):
    """
    Creates a dummy thread that simulates eye movements for testing.
    Generates a figure-8 pattern across the screen.

    Args:
        shared_x: multiprocessing.Value for x coordinate
        shared_y: multiprocessing.Value for y coordinate
        fps: Updates per second
    """
    # Get screen dimensions
    root = tk.Tk()
    root.withdraw()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()

    # Center of screen
    center_x = screen_width // 2
    center_y = screen_height // 2

    # Pattern size - 1/3 of screen dimensions
    width_amplitude = screen_width // 3
    height_amplitude = screen_height // 3

    stop_event = threading.Event()

    def dummy_eye_movement():
        step = 0
        while not stop_event.is_set():
            # Calculate time-based position (figure-8 pattern)
            t = step / 50.0  # Adjust for speed

            # Figure-8 parametric equations
            x = center_x + width_amplitude * math.sin(t)
            y = center_y + height_amplitude * math.sin(2 * t) / 2

            # Update shared memory
            shared_x.value = x
            shared_y.value = y

            # Print for debugging
            if step % 20 == 0:
                print(f"Dummy eye position: ({int(x)}, {int(y)})")

            step += 1
            time.sleep(1.0 / fps)

    thread = threading.Thread(target=dummy_eye_movement)
    thread.daemon = True
    thread.start()

    return stop_event, thread


class CoordinateManager:
    """
    Manages coordinates from different sources (mouse, eye tracking) and importance map
    to determine the best magnification point.
    """

    def __init__(
        self,
        eye_tracking_enabled=False,
        importance_grid_enabled=False,
        use_dummy_tracker=False,
    ):
        self.eye_tracking_enabled = eye_tracking_enabled
        self.importance_grid_enabled = importance_grid_enabled
        self.use_dummy_tracker = use_dummy_tracker

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

        # Initialize mouse tracking thread
        self.mouse_thread_active = True
        self.mouse_thread = threading.Thread(target=self._track_mouse)
        self.mouse_thread.daemon = True
        self.mouse_thread.start()

    def _track_mouse(self):
        """Thread function to continuously update mouse position"""
        while self.mouse_thread_active:
            try:
                x, y = pyautogui.position()
                self.mouse_x = x
                self.mouse_y = y
            except:
                pass
            time.sleep(0.05)  # 20 fps

    def setup_eye_tracking(self):
        """Set up eye tracking - either real or dummy"""
        if self.use_dummy_tracker:
            print("Using dummy eye tracker for debugging")
            self.stop_event, self.dummy_thread = create_dummy_eye_tracker(
                self.shared_eye_x, self.shared_eye_y
            )
        else:
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

    def setup_importance_grid(self):
        """Set up the screen analyzer and generate importance grid"""
        if self.screen_analyzer is None:
            self.screen_analyzer = ScreenAnalyzer(grid_x=16, grid_y=9)

        # Generate the initial importance grid
        self.update_importance_grid()

    def update_importance_grid(self):
        """Update the importance grid by capturing the current screen and regenerating the grid"""
        if self.screen_analyzer is None:
            self.setup_importance_grid()
            return

        print("Capturing screen for importance analysis...")
        self.screen_analyzer.capture_screen(wait_seconds=2)
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
        """Get the current coordinates to use for magnification"""
        # Start with mouse coordinates
        x, y = self.mouse_x, self.mouse_y

        # If eye tracking is enabled, use that instead
        if self.eye_tracking_enabled:
            x, y = self.shared_eye_x.value, self.shared_eye_y.value

        # If importance grid is enabled, find nearby important area
        if self.importance_grid_enabled:
            x, y = self.find_important_area_near(x, y)

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

        # Stop continuous updates
        self.stop_continuous_updates()
