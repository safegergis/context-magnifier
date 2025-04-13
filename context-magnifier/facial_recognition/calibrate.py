import json
import os
from facial_recognition.main import EyeTracker


def run_calibration(save_path="calibration_data.json"):
    """
    Run the eye tracker calibration process and save the results to a file.

    Args:
        save_path: Path to save the calibration data JSON file

    Returns:
        True if calibration was successful, False otherwise
    """
    # Create and run the eye tracker calibration
    tracker = EyeTracker()

    if tracker.calibrate():
        print(f"Calibration successful! Saving data to {save_path}")

        # Extract calibration data
        calibration_data = {
            "calibrated_points": tracker.calibrated_points,
            "calibration_screen_points": tracker.calibration_screen_points,
            "screen_width": tracker.screen_width,
            "screen_height": tracker.screen_height,
        }

        # Save calibration data to a JSON file
        with open(save_path, "w") as f:
            json.dump(calibration_data, f, indent=2)

        print(f"Calibration data saved to {save_path}")
        tracker.run_circle_visualization()
        return True
    else:
        print("Calibration was not completed successfully.")
        return False


if __name__ == "__main__":
    run_calibration()
