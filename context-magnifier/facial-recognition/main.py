import cv2
import numpy as np
import time
import tkinter as tk
from GazeTracking.gaze_tracking import GazeTracking


class EyeTracker:
    """Eye tracking and calibration class using GazeTracking and tkinter."""

    def __init__(
        self,
        calibration_samples=10,
        screen_width=None,
        screen_height=None,
        calibration_screen_points=None,
    ):
        """
        Initialize the eye tracker.

        Args:
            calibration_samples: Number of samples to collect per calibration point
            screen_width: Width of the screen in pixels
            screen_height: Height of the screen in pixels
            calibration_screen_points: Dictionary mapping position names to (x,y) coordinates
        """
        self.gaze = GazeTracking()
        self.webcam = None

        # Auto-detect screen dimensions if not provided
        if not screen_width or not screen_height:
            screen_width, screen_height = get_screen_resolution()

        self.screen_width = screen_width
        self.screen_height = screen_height

        # Initialize calibration data dictionary
        self.calibrated_points = {
            "center": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "left": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "right": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "top": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "bottom": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "top_left": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "top_right": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "bottom_left": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "bottom_right": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "mid_left": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "mid_right": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "mid_top": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
            "mid_bottom": {"left_pupil": (0, 0), "right_pupil": (0, 0)},
        }

        # Set up calibration screen points if not provided
        if not calibration_screen_points:
            margin = 50
            quarter_w = self.screen_width // 4
            quarter_h = self.screen_height // 4

            self.calibration_screen_points = {
                "center": (self.screen_width // 2, self.screen_height // 2),
                "left": (margin, self.screen_height // 2),
                "right": (self.screen_width - margin, self.screen_height // 2),
                "top": (self.screen_width // 2, margin),
                "bottom": (self.screen_width // 2, self.screen_height - margin),
                "top_left": (margin, margin),
                "top_right": (self.screen_width - margin, margin),
                "bottom_left": (margin, self.screen_height - margin),
                "bottom_right": (
                    self.screen_width - margin,
                    self.screen_height - margin,
                ),
                "mid_left": (quarter_w, self.screen_height // 2),
                "mid_right": (self.screen_width - quarter_w, self.screen_height // 2),
                "mid_top": (self.screen_width // 2, quarter_h),
                "mid_bottom": (self.screen_width // 2, self.screen_height - quarter_h),
            }
        else:
            self.calibration_screen_points = calibration_screen_points

        # Calibration state
        self.is_calibrated = False
        self.calibration_samples = calibration_samples
        self.current_position = 0

        # Order of calibration points
        self.calibration_positions = [
            "center",
            "left",
            "right",
            "top",
            "bottom",
            "top_left",
            "top_right",
            "bottom_left",
            "bottom_right",
            "mid_left",
            "mid_right",
            "mid_top",
            "mid_bottom",
        ]

        # UI elements
        self.root = None
        self.canvas = None

    def start_webcam(self):
        """Initialize and start the webcam capture."""
        if self.webcam is None:
            self.webcam = cv2.VideoCapture(0)
            if not self.webcam.isOpened():
                raise RuntimeError("Could not open webcam")
        return self.webcam.isOpened()

    def stop_webcam(self):
        """Release the webcam resources."""
        if self.webcam is not None:
            self.webcam.release()
            self.webcam = None

    def calibrate(self):
        """Run the calibration process with visual feedback."""
        try:
            self.start_webcam()

            print("Starting Calibration...")

            # Create tkinter window for calibration
            self.root = tk.Tk()
            self.root.title("Eye Tracking Calibration")
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

            return self.is_calibrated

        except Exception as e:
            print(f"Calibration error: {e}")
            self.is_calibrated = False
            if self.root:
                self.root.destroy()
            self.stop_webcam()
            return False

    def show_next_calibration_point(self):
        """Display the next calibration point and UI elements."""
        # Check if we've finished all positions
        if self.current_position >= len(self.calibration_positions):
            self.finish_calibration()
            return

        position = self.calibration_positions[self.current_position]
        target_coords = self.calibration_screen_points.get(position)

        if not target_coords:
            print(f"Warning: No coordinates defined for '{position}'. Skipping.")
            self.current_position += 1
            self.show_next_calibration_point()
            return

        # Clear previous target elements
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

        # Draw calibration progress bar
        progress_width = (
            self.current_position / len(self.calibration_positions)
        ) * self.screen_width
        self.canvas.create_rectangle(
            0, 5, progress_width, 10, fill="green", outline="", tags="target"
        )

        # Show a visual representation of calibration points (mini-map)
        map_scale = 0.2
        map_width = self.screen_width * map_scale
        map_height = self.screen_height * map_scale
        map_x = self.screen_width - map_width - 20
        map_y = 20

        # Draw mini-map background
        self.canvas.create_rectangle(
            map_x,
            map_y,
            map_x + map_width,
            map_y + map_height,
            fill="black",
            outline="white",
            width=1,
            tags="target",
        )

        # Draw all calibration points on mini-map
        for i, pos in enumerate(self.calibration_positions):
            point_coords = self.calibration_screen_points.get(pos)
            if point_coords:
                mini_x = map_x + (point_coords[0] * map_scale)
                mini_y = map_y + (point_coords[1] * map_scale)

                # Choose color based on status
                if i < self.current_position:
                    color = "green"  # Completed
                elif i == self.current_position:
                    color = "red"  # Current
                else:
                    color = "gray"  # Upcoming

                # Draw the point
                self.canvas.create_oval(
                    mini_x - 3,
                    mini_y - 3,
                    mini_x + 3,
                    mini_y + 3,
                    fill=color,
                    outline=color,
                    tags="target",
                )

                # Label for the current point
                if i == self.current_position:
                    self.canvas.create_text(
                        mini_x,
                        mini_y - 10,
                        text=pos,
                        fill="white",
                        font=("Arial", 9),
                        tags="target",
                    )

        # Display calibration instructions
        description = self._get_position_description(position)
        self.canvas.create_text(
            self.screen_width // 2,
            80,
            text=description,
            fill="white",
            font=("Arial", 20, "bold"),
            tags="target",
        )

    def _get_position_description(self, position):
        """Get a human-readable description for a calibration position."""
        if "center" in position:
            return "Look at the center"
        elif "top" in position and "left" in position:
            return "Look at the top-left corner"
        elif "top" in position and "right" in position:
            return "Look at the top-right corner"
        elif "bottom" in position and "left" in position:
            return "Look at the bottom-left corner"
        elif "bottom" in position and "right" in position:
            return "Look at the bottom-right corner"
        elif "mid_left" in position:
            return "Look at the middle-left"
        elif "mid_right" in position:
            return "Look at the middle-right"
        elif "mid_top" in position:
            return "Look at the middle-top"
        elif "mid_bottom" in position:
            return "Look at the middle-bottom"
        elif "left" in position:
            return "Look to the left"
        elif "right" in position:
            return "Look to the right"
        elif "top" in position:
            return "Look up"
        elif "bottom" in position:
            return "Look down"
        return "Look at the target"

    def capture_current_position(self, event=None):
        """Capture pupil positions for the current calibration point."""
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

        # Sampling loop
        start_time = time.time()
        while samples_collected < self.calibration_samples:
            # Check for timeout
            if time.time() - start_time > 10:
                print("Timeout waiting for pupil detection.")
                break

            # Update the webcam and detect pupils
            ret, frame = self.webcam.read()
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
            # Calculate average pupil positions
            avg_left_x = np.mean(temp_left_pupils_x)
            avg_left_y = np.mean(temp_left_pupils_y)
            avg_right_x = np.mean(temp_right_pupils_x)
            avg_right_y = np.mean(temp_right_pupils_y)

            # Store calibrated data
            self.calibrated_points[position]["left_pupil"] = (avg_left_x, avg_left_y)
            self.calibrated_points[position]["right_pupil"] = (
                avg_right_x,
                avg_right_y,
            )

            print(
                f"Calibrated {position} position: Left pupil {self.calibrated_points[position]['left_pupil']}, "
                f"Right pupil {self.calibrated_points[position]['right_pupil']}"
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
        """End calibration process (called when user aborts)."""
        print("Calibration aborted by user.")
        self.is_calibrated = False
        self.root.destroy()
        self.stop_webcam()

    def finish_calibration(self):
        """Complete the calibration process."""
        if self.current_position == len(self.calibration_positions):
            print("Calibration complete!")
            print("Calibrated Pupil Positions:", self.calibrated_points)
            self.is_calibrated = True
        else:
            print("Calibration was not completed.")
            self.is_calibrated = False

        self.root.destroy()
        self.stop_webcam()

    def get_gaze_point(self, frame=None):
        """
        Get the current gaze point as screen coordinates.

        Args:
            frame: Optional video frame. If not provided, a new frame will be captured.

        Returns:
            Tuple (x, y) with screen coordinates or None if gaze can't be determined
        """
        if not self.is_calibrated:
            return None

        # Start webcam if needed
        if self.webcam is None:
            self.start_webcam()

        # Get a frame if none provided
        if frame is None:
            ret, frame = self.webcam.read()
            if not ret or frame is None:
                return None

        # Process the frame
        self.gaze.refresh(frame)
        left_pupil = self.gaze.pupil_left_coords()
        right_pupil = self.gaze.pupil_right_coords()

        # Map eye position to screen position
        return self.map_eye_position_to_screen((left_pupil, right_pupil))

    def map_eye_position_to_screen(self, eye_position):
        """
        Maps eye pupil coordinates to screen coordinates using weighted interpolation.

        Args:
            eye_position: Tuple (left_pupil, right_pupil) where each pupil is (x,y)

        Returns:
            (x, y) coordinates on screen or None if pupils not detected
        """
        left_pupil, right_pupil = eye_position

        # Use available pupil data
        if left_pupil and right_pupil:
            current_left_x, current_left_y = left_pupil
            current_right_x, current_right_y = right_pupil
        elif left_pupil:
            current_left_x, current_left_y = left_pupil
            current_right_x, current_right_y = 0, 0
        elif right_pupil:
            current_left_x, current_left_y = 0, 0
            current_right_x, current_right_y = right_pupil
        else:
            # No pupils detected
            return None

        # Calculate weights based on distance to calibration points
        weights = {}
        total_weight = 0

        for position, data in self.calibrated_points.items():
            # Get calibrated pupil positions
            cal_left_x, cal_left_y = data["left_pupil"]
            cal_right_x, cal_right_y = data["right_pupil"]

            # Calculate squared Euclidean distance
            left_distance_sq = (current_left_x - cal_left_x) ** 2 + (
                current_left_y - cal_left_y
            ) ** 2
            right_distance_sq = (current_right_x - cal_right_x) ** 2 + (
                current_right_y - cal_right_y
            ) ** 2

            # Combined distance (average of both eyes)
            if left_pupil and right_pupil:
                distance_sq = (left_distance_sq + right_distance_sq) / 2
            elif left_pupil:
                distance_sq = left_distance_sq
            else:
                distance_sq = right_distance_sq

            # Avoid division by zero
            epsilon = 1e-10

            # Weight is inversely proportional to distance squared
            weight = 1.0 / (distance_sq + epsilon)
            weights[position] = weight
            total_weight += weight

        # Normalize weights
        if total_weight > 0:
            for position in weights:
                weights[position] /= total_weight

        # Map to screen coordinates with weighted average
        screen_x = 0
        screen_y = 0

        # Get screen coordinates based on calibration points
        for position, weight in weights.items():
            point_coords = self.calibration_screen_points.get(position)
            if point_coords:
                screen_x += weight * point_coords[0]
                screen_y += weight * point_coords[1]

        return int(screen_x), int(screen_y)

    def start_tracking(self, callback=None, fps=30):
        """
        Start continuous eye tracking in a separate thread and call the callback
        function with the screen coordinates.

        Args:
            callback: Function to call with (x, y) screen coordinates
            fps: Target frames per second for tracking

        Returns:
            The tracking thread object
        """
        import threading

        if not self.is_calibrated:
            raise ValueError("Eye tracker must be calibrated before tracking")

        self.start_webcam()
        self._tracking_active = True

        def tracking_loop():
            frame_time = 1.0 / fps
            while self._tracking_active:
                start = time.time()

                # Get gaze point
                ret, frame = self.webcam.read()
                if ret and frame is not None:
                    gaze_point = self.get_gaze_point(frame)
                    if gaze_point and callback:
                        callback(gaze_point)

                # Maintain consistent frame rate
                elapsed = time.time() - start
                sleep_time = max(0, frame_time - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        # Start tracking in a thread
        tracking_thread = threading.Thread(target=tracking_loop)
        tracking_thread.daemon = True
        tracking_thread.start()
        return tracking_thread

    def stop_tracking(self):
        """Stop the continuous eye tracking."""
        self._tracking_active = False
        self.stop_webcam()

    def run_circle_visualization(self, duration=None):
        """
        Run a visual demo showing a circle following the user's gaze.

        Args:
            duration: Optional number of seconds to run before exiting
                     If None, runs until user exits with ESC or Q

        Returns:
            True if ran successfully, False otherwise
        """
        if not self.is_calibrated:
            print("Cannot visualize gaze: Eye tracker not calibrated")
            return False

        try:
            # Create visualization window
            vis_root = tk.Tk()
            vis_root.title("Gaze Visualization")
            vis_root.attributes("-fullscreen", True)
            vis_root.configure(background="black")

            # Create canvas for drawing
            canvas = tk.Canvas(
                vis_root,
                width=self.screen_width,
                height=self.screen_height,
                bg="black",
                highlightthickness=0,
            )
            canvas.pack(fill=tk.BOTH, expand=True)

            # Add keyboard bindings to exit
            vis_root.bind("<Escape>", lambda e: vis_root.destroy())
            vis_root.bind("q", lambda e: vis_root.destroy())

            # Create the gaze indicator circle
            circle_size = 30
            gaze_circle = canvas.create_oval(
                -circle_size,
                -circle_size,
                circle_size,
                circle_size,
                fill="blue",
                outline="white",
                width=2,
            )

            # Text instructions
            canvas.create_text(
                self.screen_width // 2,
                30,
                text="Your gaze position is shown with the blue circle\nPress ESC or Q to exit",
                fill="white",
                font=("Arial", 16),
            )

            # Flag to check if the window is still open
            window_open = True
            vis_root.protocol(
                "WM_DELETE_WINDOW", lambda: setattr(window_open, "value", False)
            )

            # Define callback for gaze updates
            def update_circle_position(coords):
                x, y = coords
                canvas.coords(
                    gaze_circle,
                    x - circle_size,
                    y - circle_size,
                    x + circle_size,
                    y + circle_size,
                )
                if window_open:
                    canvas.update()

            # Start tracking with the callback
            tracking_thread = self.start_tracking(callback=update_circle_position)

            # If duration is set, start a timer to close the window
            if duration:
                vis_root.after(int(duration * 1000), vis_root.destroy)

            # Start the UI loop
            vis_root.mainloop()

            # Cleanup
            self.stop_tracking()
            return True

        except Exception as e:
            print(f"Visualization error: {e}")
            self.stop_tracking()
            return False


def get_screen_resolution():
    """
    Get the primary screen resolution using tkinter.

    Returns:
        Tuple (width, height) or (None, None) if detection fails
    """
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return width, height
    except tk.TclError:
        print("Warning: Could not initialize Tkinter. Display required?")
        return None, None


def demo_eye_tracker():
    tracker = EyeTracker()
    if tracker.calibrate():
        gaze_point = tracker.get_gaze_point()

        def handle_gaze(coords):
            x, y = coords
            print(f"Gaze at: {x}, {y}")

        tracking_thread = tracker.start_tracking(callback=handle_gaze)

        # When done
        tracker.stop_tracking()


def circle_visualization_demo():
    """Run just the circle visualization demo with a calibrated tracker."""
    tracker = EyeTracker()
    if tracker.calibrate():
        tracker.run_circle_visualization()


if __name__ == "__main__":
    demo_eye_tracker()
