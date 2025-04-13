import multiprocessing
from app.main_window import run_main_window
import sys
from PySide6.QtWidgets import QApplication

from app.zoom_window import ScreenMagnifier
from coordinate_manager import CoordinateManager


def run_zoom_window_app(coord_manager):
    """Run the zoom window application with the given coordinate manager"""
    app = QApplication(sys.argv)

    magnifier = ScreenMagnifier(
        coord_source=coord_manager.get_coordinates,
        scale_factor=2.5,
        zoom_increment=0.1,
        window_width=1000,
        window_height=562,
    )

    # Connect signals for feature toggling
    magnifier.toggle_eye_tracking_signal.connect(coord_manager.toggle_eye_tracking)
    magnifier.toggle_importance_map_signal.connect(coord_manager.toggle_importance_map)

    # Set initial UI state to match coordinator state
    if coord_manager.eye_tracking_enabled:
        magnifier.eye_tracking_enabled = True

    if coord_manager.importance_grid_enabled:
        magnifier.importance_map_enabled = True

    magnifier.show()

    # Connect the exit signal to the QApplication quit method
    magnifier.exit_signal.connect(app.quit)

    return app.exec()


if __name__ == "__main__":
    # Configuration options
    USE_DUMMY_TRACKER = False  # Set to True to use dummy eye tracking
    USE_EYE_TRACKING = False  # Set to True to enable eye tracking
    USE_IMPORTANCE_MAP = True  # Set to True to use importance map for zoom targeting

    # Create the coordinate manager
    coord_manager = CoordinateManager(
        eye_tracking_enabled=USE_EYE_TRACKING,
        importance_grid_enabled=USE_IMPORTANCE_MAP,
        use_dummy_tracker=USE_DUMMY_TRACKER,
    )

    # Set up components
    if USE_EYE_TRACKING:
        coord_manager.setup_eye_tracking()

    if USE_IMPORTANCE_MAP:
        coord_manager.setup_importance_grid()

    # Start the application
    p1 = multiprocessing.Process(target=run_main_window)
    p1.start()

    try:
        run_zoom_window_app(coord_manager)
    finally:
        # Cleanup
        coord_manager.cleanup()
        p1.join()
