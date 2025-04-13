import cv2
from GazeTracking.gaze_tracking import GazeTracking
import numpy as np
import time
import tkinter as tk
from PIL import Image, ImageTk


class EyeTracker:
    def __init__(
        self,
        calibration_samples=10,
        screen_width=None,
        screen_height=None,
        calibration_screen_points=None,
    ):
        self.gaze = GazeTracking()
        self.webcam = cv2.VideoCapture(0)

        self.callibrated_points = {
            "left": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "right": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "center": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "top": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "bottom": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
        }

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.calibration_screen_points = (
            calibration_screen_points if calibration_screen_points is not None else {}
        )

        self.is_calibrated = False
        self.calibration_samples = calibration_samples
        self.current_position = 0
        self.calibration_positions = ["center", "left", "right", "top", "bottom"]

    def calibrate(self):
        if (
            not self.screen_width
            or not self.screen_height
            or not self.calibration_screen_points
        ):
            print(
                "Error: Screen dimensions or calibration points not provided for calibration."
            )
            self.screen_width, self.screen_height = get_screen_resolution()
            if not self.screen_width or not self.screen_height:
                print("Could not determine screen resolution. Aborting calibration.")
                return
            margin = 50
            self.calibration_screen_points = {
                "center": (self.screen_width // 2, self.screen_height // 2),
                "left": (margin, self.screen_height // 2),
                "right": (self.screen_width - margin, self.screen_height // 2),
                "top": (self.screen_width // 2, margin),
                "bottom": (self.screen_width // 2, self.screen_height - margin),
            }
            print(
                "Using automatically determined screen resolution and default calibration points."
            )

        print("Starting Calibration...")
        self.root = tk.Tk()
        self.root.title("Calibration")
        self.root.attributes("-fullscreen", True)
        self.root.configure(background="black")

        # Create a canvas to draw on
        self.canvas = tk.Canvas(
            self.root,
            width=self.screen_width,
            height=self.screen_height,
            bg="black",
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind keyboard events
        self.root.bind("<Escape>", self.end_calibration)
        self.root.bind("<space>", self.capture_current_position)
        self.root.bind("q", self.end_calibration)

        # Display instructions
        instruction_text = "Look at the RED DOT and press SPACE to capture each position.\nPress ESC or Q to exit."
        self.canvas.create_text(
            self.screen_width // 2,
            30,
            text=instruction_text,
            fill="white",
            font=("Arial", 16),
        )

        # Start with first position
        self.show_next_calibration_point()

        # Main tkinter loop
        self.root.mainloop()

    def show_next_calibration_point(self):
        if self.current_position >= len(self.calibration_positions):
            self.finish_calibration()
            return

        position = self.calibration_positions[self.current_position]
        target_coords = self.calibration_screen_points.get(position)

        if not target_coords:
            print(
                f"Warning: No screen coordinates defined for position '{position}'. Skipping."
            )
            self.current_position += 1
            self.show_next_calibration_point()
            return

        # Clear canvas
        self.canvas.delete("target")

        # Draw the target point
        x, y = int(target_coords[0]), int(target_coords[1])

        # Draw dot
        self.canvas.create_oval(
            x - 15, y - 15, x + 15, y + 15, fill="red", outline="red", tags="target"
        )

        # Draw crosshair
        self.canvas.create_line(
            x, y - 25, x, y + 25, fill="white", width=1, tags="target"
        )
        self.canvas.create_line(
            x - 25, y, x + 25, y, fill="white", width=1, tags="target"
        )

        # Draw position label
        self.canvas.create_text(
            self.screen_width // 2,
            self.screen_height - 30,
            text=f"Position {self.current_position + 1}/{len(self.calibration_positions)} ({position.upper()})",
            fill="green",
            font=("Arial", 14),
            tags="target",
        )

    def capture_current_position(self, event=None):
        if self.current_position >= len(self.calibration_positions):
            return

        position = self.calibration_positions[self.current_position]
        print(f"Capturing samples for {position.upper()}...")

        # Variables to store pupil coordinates
        temp_left_pupils_x = []
        temp_left_pupils_y = []
        temp_right_pupils_x = []
        temp_right_pupils_y = []
        samples_collected = 0

        # Create a progress indicator
        progress_text = self.canvas.create_text(
            self.screen_width // 2,
            self.screen_height - 60,
            text="Sampling... 0/" + str(self.calibration_samples),
            fill="orange",
            font=("Arial", 14),
        )

        self.root.update()

        start_time = time.time()
        while samples_collected < self.calibration_samples:
            if time.time() - start_time > 10:
                print("Timeout waiting for pupil detection.")
                break

            # Update the webcam and detect pupils
            _, frame = self.webcam.read()
            if frame is None:
                time.sleep(0.05)
                continue

            self.gaze.refresh(frame)
            left_pupil = self.gaze.pupil_left_coords()
            right_pupil = self.gaze.pupil_right_coords()

            # Update progress text
            self.canvas.itemconfig(
                progress_text,
                text=f"Sampling... {samples_collected}/{self.calibration_samples}",
            )
            self.root.update()

            if left_pupil and right_pupil:
                temp_left_pupils_x.append(left_pupil[0])
                temp_left_pupils_y.append(left_pupil[1])
                temp_right_pupils_x.append(right_pupil[0])
                temp_right_pupils_y.append(right_pupil[1])
                samples_collected += 1

            time.sleep(0.05)

        # Delete progress indicator
        self.canvas.delete(progress_text)

        # Check if enough samples were collected
        if samples_collected == self.calibration_samples:
            avg_left_x = np.mean(temp_left_pupils_x)
            avg_left_y = np.mean(temp_left_pupils_y)
            avg_right_x = np.mean(temp_right_pupils_x)
            avg_right_y = np.mean(temp_right_pupils_y)

            self.callibrated_points[position]["left_pupil"] = (avg_left_x, avg_left_y)
            self.callibrated_points[position]["right_pupil"] = (
                avg_right_x,
                avg_right_y,
            )

            print(
                f"Calibrated {position} position: Left pupil {self.callibrated_points[position]['left_pupil']}, Right pupil {self.callibrated_points[position]['right_pupil']}"
            )

            # Show success message
            success_text = self.canvas.create_text(
                self.screen_width // 2,
                self.screen_height - 60,
                text=f"{position.upper()} Calibrated!",
                fill="green",
                font=("Arial", 14),
            )
            self.root.update()
            time.sleep(1)
            self.canvas.delete(success_text)

            # Move to next position
            self.current_position += 1
            self.show_next_calibration_point()
        else:
            # Show error message
            error_text = self.canvas.create_text(
                self.screen_width // 2,
                self.screen_height - 60,
                text=f"Failed {position.upper()}. Try again.",
                fill="red",
                font=("Arial", 14),
            )
            self.root.update()
            time.sleep(1.5)
            self.canvas.delete(error_text)

            # Retry the same position
            self.show_next_calibration_point()

    def end_calibration(self, event=None):
        print("Calibration aborted by user.")
        self.is_calibrated = False
        self.root.destroy()
        self.webcam.release()

    def finish_calibration(self):
        if self.current_position == len(self.calibration_positions):
            print("Calibration complete!")
            print("Calibrated Pupil Positions:", self.callibrated_points)
            self.is_calibrated = True
        else:
            print("Calibration was not completed.")
            self.is_calibrated = False

        self.root.destroy()
        self.webcam.release()


def get_screen_resolution():
    """Gets the primary screen resolution."""
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return width, height
    except tk.TclError:
        print("Warning: Could not initialize Tkinter. Display required?")
        # Fallback or default values if needed
        return None, None


if __name__ == "__main__":
    screen_width, screen_height = get_screen_resolution()
    if screen_width and screen_height:
        print(f"Screen Resolution: {screen_width}x{screen_height}")

        screen_calibration_points = {
            "center": (screen_width // 2, screen_height // 2),
            "left": (50, screen_height // 2),
            "right": (screen_width - 50, screen_height // 2),
            "top": (screen_width // 2, 50),
            "bottom": (screen_width // 2, screen_height - 50),
        }
        print("Target Screen Calibration Points:", screen_calibration_points)

        eye_tracker = EyeTracker(
            calibration_samples=15,
            screen_width=screen_width,
            screen_height=screen_height,
            calibration_screen_points=screen_calibration_points,
        )
        eye_tracker.calibrate()

        if eye_tracker.is_calibrated:
            print("Eye tracking can now begin (implementation pending).")
        else:
            print("Eye tracking cannot start without successful calibration.")

    else:
        print("Could not determine screen resolution. Cannot start calibration.")
