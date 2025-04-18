import multiprocessing
from app.main_window import run_main_window
import sys
from PySide6.QtWidgets import QApplication


from app.zoom_window import ScreenMagnifier
from coordinate_manager import CoordinateManager


def apply_settings(settings, coord_manager):
    """Apply settings from the main window to the coordinate manager and screen analyzer"""
    try:
        print("Applying settings:", settings)

        # Update ScreenAnalyzer settings
        if coord_manager.screen_analyzer:
            if "grid x" in settings:
                coord_manager.screen_analyzer.grid_x = settings["grid x"]
            if "grid y" in settings:
                coord_manager.screen_analyzer.grid_y = settings["grid y"]
            if "base size" in settings:
                coord_manager.screen_analyzer.base_size = settings["base size"]
            if "max size factor" in settings:
                coord_manager.screen_analyzer.max_size_factor = settings[
                    "max size factor"
                ]
            if "min size factor" in settings:
                coord_manager.screen_analyzer.min_size_factor = settings[
                    "min size factor"
                ]
            if "confidence threshold" in settings:
                coord_manager.screen_analyzer.confidence_threshold = settings[
                    "confidence threshold"
                ]
            if "button importance" in settings:
                coord_manager.screen_analyzer.button_importance = settings[
                    "button importance"
                ]
            if "input field importance" in settings:
                coord_manager.screen_analyzer.input_field_importance = settings[
                    "input field importance"
                ]
            if "checkbox importance" in settings:
                coord_manager.screen_analyzer.checkbox_importance = settings[
                    "checkbox importance"
                ]
            if "confirmation importance" in settings:
                coord_manager.screen_analyzer.confirmation_text_importance = settings[
                    "confirmation importance"
                ]
            if "error importance" in settings:
                coord_manager.screen_analyzer.error_importance = settings[
                    "error importance"
                ]
            if "title importance" in settings:
                coord_manager.screen_analyzer.title_importance = settings[
                    "title importance"
                ]
            if "length importance" in settings:
                coord_manager.screen_analyzer.length_importance = settings[
                    "length importance"
                ]
            if "density importance" in settings:
                coord_manager.screen_analyzer.density_importance = settings[
                    "density importance"
                ]

            # Regenerate importance grid with new settings
            if coord_manager.importance_grid_enabled:
                coord_manager.update_importance_grid()

        return True
    except Exception as e:
        print(f"Error applying settings: {e}")
        return False


def process_command(command, coord_manager):
    """Process a command from the command queue"""
    try:
        print(f"Processing command: {command}")

        if command.get("command") == "enable_eye_tracking":
            calibration_file = command.get("file")
            if calibration_file:
                # Load calibration and enable eye tracking
                return coord_manager.load_calibration_and_track(calibration_file)
        elif command.get("command") == "toggle_continuous_updates":
            # Toggle continuous updates
            if coord_manager.continuous_update:
                coord_manager.stop_continuous_updates()
                print("Stopped continuous updates")
            else:
                coord_manager.start_continuous_updates()
                print("Started continuous updates")
            return True

        return False
    except Exception as e:
        print(f"Error processing command: {e}")
        return False


def run_zoom_window_app(coord_manager, settings_queue, command_queue):
    """Run the zoom window application with the given coordinate manager"""
    app = QApplication(sys.argv)

    # Check for fixed position setting (default to False if not set)
    fixed_position = getattr(coord_manager, "fixed_position", False)

    magnifier = ScreenMagnifier(
        coord_source=coord_manager.get_coordinates,
        scale_factor=2.5,
        zoom_increment=0.1,
        window_width=1000,
        window_height=562,
        follow_mouse=True,  # Enable follow_mouse by default
        fixed_position=fixed_position,  # Apply fixed position setting
    )

    # Connect signals for feature toggling
    magnifier.toggle_eye_tracking_signal.connect(coord_manager.toggle_eye_tracking)
    magnifier.toggle_importance_map_signal.connect(coord_manager.toggle_importance_map)
    magnifier.update_importance_map_signal.connect(coord_manager.update_importance_grid)

    # Connect continuous update signals
    def handle_continuous_toggle(enabled):
        if enabled:
            coord_manager.start_continuous_updates()
        else:
            coord_manager.stop_continuous_updates()

    magnifier.toggle_continuous_updates_signal.connect(handle_continuous_toggle)
    magnifier.set_update_interval_signal.connect(
        coord_manager.set_continuous_update_interval
    )

    # Set initial UI state to match coordinator state
    if coord_manager.eye_tracking_enabled:
        magnifier.eye_tracking_enabled = True

    if coord_manager.importance_grid_enabled:
        magnifier.importance_map_enabled = True

    # Start a worker thread to process queues
    def queue_worker():
        while True:
            try:
                # Check for settings
                try:
                    settings = settings_queue.get(block=False)
                    if settings:
                        apply_settings(settings, coord_manager)
                except:
                    pass

                # Check for commands
                try:
                    command = command_queue.get(block=False)
                    if command:
                        process_command(command, coord_manager)
                except:
                    pass

                # Sleep to avoid high CPU usage
                import time

                time.sleep(0.1)

            except:
                # Queue might be closed if process is shutting down
                break

    import threading

    queue_thread = threading.Thread(target=queue_worker)
    queue_thread.daemon = True
    queue_thread.start()

    magnifier.show()

    # Connect the exit signal to the QApplication quit method
    magnifier.exit_signal.connect(app.quit)

    return app.exec()


if __name__ == "__main__":
    # Configuration options
    USE_EYE_TRACKING = False  # Set to True to enable eye tracking
    USE_IMPORTANCE_MAP = True  # Set to True to use importance map for zoom targeting

    # Create queues for communication between processes
    settings_queue = multiprocessing.Queue()
    command_queue = multiprocessing.Queue()

    # Create the coordinate manager
    coord_manager = CoordinateManager(
        eye_tracking_enabled=USE_EYE_TRACKING,
        importance_grid_enabled=USE_IMPORTANCE_MAP,
    )

    # Set up components
    if USE_IMPORTANCE_MAP:
        coord_manager.setup_importance_grid()

    # Start the application
    p1 = multiprocessing.Process(
        target=run_main_window, args=(settings_queue, command_queue)
    )
    p1.start()

    try:
        run_zoom_window_app(coord_manager, settings_queue, command_queue)
    finally:
        # Cleanup
        coord_manager.cleanup()
        settings_queue.close()
        command_queue.close()
        p1.join()
