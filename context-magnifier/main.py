import multiprocessing
import ctypes
import threading
import time
from PySide6.QtWidgets import QApplication  # Required for QCursor if using mouse
from PySide6.QtGui import QCursor

from app.zoom_window import run_zoom_window
from facial_recognition.main import EyeTracker, get_screen_resolution
from ocr.main import ScreenAnalyzer

# --- Configuration Flags ---
USE_EYE_TRACKER = False  # Set to True to use eye tracking, False for mouse
USE_IMPORTANCE_ADJUSTMENT = (
    True  # Set to True to adjust coordinates based on importance map
)
SCREEN_ANALYSIS_INTERVAL = 2  # Seconds between screen analysis updates
TRACKING_FPS = 15  # Target FPS for coordinate updates (mouse or eye)
# -------------------------

# --- Shared Data ---
shared_x = multiprocessing.Value(ctypes.c_double, 0.0)
shared_y = multiprocessing.Value(ctypes.c_double, 0.0)
shared_importance_data = {
    "importance_matrix": None,
    "cell_dimensions": None,
    "grid_shape": None,  # Store (grid_y, grid_x)
}
data_lock = threading.Lock()
stop_event = threading.Event()
# -----------------


def analyze_screen_periodically(analyzer):
    """
    Periodically analyzes the screen and updates shared importance data.
    Runs in a separate thread.
    """
    print("Starting screen analysis thread...")
    while not stop_event.is_set():
        try:
            start_time = time.time()
            analyzer.capture_screen()
            grid_cells, cell_dimensions, importance_matrix = (
                analyzer.generate_importance_grid()
            )
            with data_lock:
                shared_importance_data["importance_matrix"] = importance_matrix
                shared_importance_data["cell_dimensions"] = cell_dimensions
                shared_importance_data["grid_shape"] = (
                    analyzer.grid_y,
                    analyzer.grid_x,
                )
            # print("Screen analysis updated.") # Optional: for debugging

            elapsed = time.time() - start_time
            sleep_time = max(0, SCREEN_ANALYSIS_INTERVAL - elapsed)
            if sleep_time > 0:
                stop_event.wait(
                    sleep_time
                )  # Use wait instead of sleep for responsiveness

        except Exception as e:
            print(f"Error in screen analysis thread: {e}")
            stop_event.wait(SCREEN_ANALYSIS_INTERVAL)  # Wait before retrying on error
    print("Stopping screen analysis thread.")


def update_mouse_coordinates():
    """
    Continuously updates shared coordinates based on mouse position.
    Runs in a separate thread if USE_EYE_TRACKER is False.
    """
    print("Starting mouse tracking thread...")
    # Need a QApplication instance to use QCursor outside the main GUI thread sometimes
    # Check if an instance already exists
    app_instance = QApplication.instance()
    if not app_instance:
        # Create a dummy instance if none exists (won't show a window)
        app_instance = QApplication([])

    frame_time = 1.0 / TRACKING_FPS
    while not stop_event.is_set():
        start_time = time.time()
        try:
            cursor_pos = QCursor.pos()
            mx, my = cursor_pos.x(), cursor_pos.y()
            shared_x.value = float(mx)
            shared_y.value = float(my)
        except Exception as e:
            print(f"Error getting mouse position: {e}")
            # Keep previous values or set to 0,0? Let's keep previous for now.
            pass

        elapsed = time.time() - start_time
        sleep_time = max(0, frame_time - elapsed)
        if sleep_time > 0:
            stop_event.wait(sleep_time)
    print("Stopping mouse tracking thread.")


def get_adjusted_coordinates():
    """
    Returns the current coordinates, optionally adjusted based on the importance map.
    This function is passed to the zoom window.
    """
    base_x = shared_x.value
    base_y = shared_y.value

    if not USE_IMPORTANCE_ADJUSTMENT:
        return (base_x, base_y)

    with data_lock:
        matrix = shared_importance_data["importance_matrix"]
        dims = shared_importance_data["cell_dimensions"]
        grid_shape = shared_importance_data["grid_shape"]

    if matrix is None or dims is None or grid_shape is None:
        # print("Importance data not yet available.") # Optional debug
        return (base_x, base_y)

    cell_width, cell_height = dims
    grid_y, grid_x = grid_shape

    if cell_width <= 0 or cell_height <= 0:
        print("Invalid cell dimensions.")
        return (base_x, base_y)

    # Find the grid cell containing the base coordinates
    current_cell_x = min(grid_x - 1, max(0, int(base_x // cell_width)))
    current_cell_y = min(grid_y - 1, max(0, int(base_y // cell_height)))

    # Find the most important cell in a 3x3 neighborhood around the current cell
    best_score = -1.0
    best_cell_x, best_cell_y = current_cell_x, current_cell_y

    for dy in range(-1, 2):  # Check rows -1, 0, +1
        for dx in range(-1, 2):  # Check cols -1, 0, +1
            check_y = current_cell_y + dy
            check_x = current_cell_x + dx

            # Check bounds
            if 0 <= check_y < grid_y and 0 <= check_x < grid_x:
                score = matrix[check_y, check_x]
                if score > best_score:
                    best_score = score
                    best_cell_x, best_cell_y = check_x, check_y

    # Calculate the center coordinates of the most important cell
    adjusted_x = (best_cell_x + 0.5) * cell_width
    adjusted_y = (best_cell_y + 0.5) * cell_height

    # Optional: Add smoothing or inertia later if needed
    # print(f"Base: ({base_x:.0f}, {base_y:.0f}) -> Adjusted: ({adjusted_x:.0f}, {adjusted_y:.0f}) [Cell: {best_cell_x},{best_cell_y}, Score: {best_score:.2f}]") # Debug
    return (adjusted_x, adjusted_y)


if __name__ == "__main__":
    print("Starting Context Magnifier...")

    screen_analyzer = ScreenAnalyzer()
    screen_width, screen_height = get_screen_resolution()  # Use utility from EyeTracker

    # Start screen analysis thread
    analysis_thread = threading.Thread(
        target=analyze_screen_periodically, args=(screen_analyzer,)
    )
    analysis_thread.daemon = True
    analysis_thread.start()

    tracking_thread = None
    tracker = None

    # Start coordinate tracking (Eye or Mouse)
    if USE_EYE_TRACKER:
        print("Initializing Eye Tracker...")
        tracker = EyeTracker(screen_width=screen_width, screen_height=screen_height)
        if tracker.calibrate():
            print("Calibration successful. Starting eye tracking...")

            def handle_gaze(coords):
                # This runs in the tracker's thread
                x, y = coords
                shared_x.value = float(x)
                shared_y.value = float(y)

            # tracker.start_tracking creates and returns its own thread
            # We don't need to store it directly here as stop_tracking handles it
            tracker.start_tracking(callback=handle_gaze, fps=TRACKING_FPS)
            print("Eye tracking started.")
        else:
            print("Calibration failed or aborted. Exiting.")
            stop_event.set()  # Signal other threads to stop
            analysis_thread.join()
            exit()
    else:
        print("Using Mouse Pointer for coordinates.")
        tracking_thread = threading.Thread(target=update_mouse_coordinates)
        tracking_thread.daemon = True
        tracking_thread.start()

    # Ensure some analysis data exists before starting zoom window?
    # Or let it start with unadjusted coords initially. Let's let it start.

    print("Starting Zoom Window...")
    # This will block until the window is closed
    try:
        run_zoom_window(
            coord_source=get_adjusted_coordinates,  # Pass our adjustment function
            scale_factor=2.5,
            zoom_increment=0.1,
            window_width=600,  # Adjust size as needed
            window_height=400,
        )
    except Exception as e:
        print(f"Error running zoom window: {e}")
    finally:
        # --- Cleanup ---
        print("Shutting down...")
        stop_event.set()  # Signal all threads to stop

        if analysis_thread:
            analysis_thread.join(timeout=2.0)
            if analysis_thread.is_alive():
                print("Warning: Analysis thread did not exit cleanly.")

        if tracker:  # Eye tracker cleanup
            print("Stopping eye tracker...")
            tracker.stop_tracking()
            # tracker's internal thread should stop via stop_tracking

        if tracking_thread:  # Mouse tracker cleanup
            tracking_thread.join(timeout=1.0)
            if tracking_thread.is_alive():
                print("Warning: Mouse tracking thread did not exit cleanly.")

        print("Exited.")
