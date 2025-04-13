from PIL import ImageGrab
import pytesseract
import cv2
import numpy as np
import matplotlib.pyplot as plt
import timeit
import time


class ScreenAnalyzer:
    """
    A class for analyzing screen content and identifying important areas
    based on text and UI elements.
    """

    def __init__(
        self,
        grid_x=7,
        grid_y=14,
        base_size=20,
        max_size_factor=4.0,
        min_size_factor=1.0,
        confidence_threshold=20,
        button_importance=3.0,
        input_field_importance=2.0,
        checkbox_importance=1.0,
        confirmation_text_importance=3.0,
        error_importance=2.5,
        title_importance=1.5,
        length_importance=1.5,
        density_importance=0.2,
    ):
        """
        Initialize the ScreenAnalyzer with specified grid dimensions.

        Args:
            grid_x: Number of horizontal grid cells
            grid_y: Number of vertical grid cells
            base_size: Base font size for text importance calculation
            max_size_factor: max factor to multiply the text importance by for small text
            min_size_factor: min factor to multiply the text importance by for large text
            confidence_threshold: Minimum confidence threshold for text, text with lower confidence is ignored
            button_importance: Importance score for buttons
            input_field_importance: Importance score for input fields
            checkbox_importance: Importance score for checkboxes
            confirmation_text_importance: Importance score for confirmation (ok, submit, accept) text
            error_importance: Importance score for error text
            title_importance: Importance score for title text
            length_importance: Importance score for length of text
            density_importance: Importance score for density of text
        """
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.screenshot = None
        self.grid_cells = None
        self.cell_dimensions = None
        self.importance_matrix = None
        self.base_size = base_size
        self.max_size_factor = max_size_factor
        self.min_size_factor = min_size_factor
        self.button_importance = button_importance
        self.input_field_importance = input_field_importance
        self.checkbox_importance = checkbox_importance
        self.confidence_threshold = confidence_threshold
        self.confirmation_text_importance = confirmation_text_importance
        self.error_importance = error_importance
        self.title_importance = title_importance
        self.length_importance = length_importance
        self.density_importance = density_importance

    def capture_screen(self, wait_seconds=0):
        """
        Capture the screen after an optional delay.

        Args:
            wait_seconds: Number of seconds to wait before capturing

        Returns:
            screenshot: numpy array of the screenshot or None if failed
        """
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        try:
            # Take a screenshot
            screenshot = ImageGrab.grab()

            # Check if screenshot is valid
            if screenshot is None or screenshot.size == (0, 0):
                print("Error: Failed to capture screen - empty screenshot")
                return None

            self.screenshot = np.array(screenshot)

            # Convert from BGR to RGB (OpenCV uses BGR by default)
            self.screenshot = cv2.cvtColor(self.screenshot, cv2.COLOR_BGR2RGB)

            print(f"Screenshot captured with shape: {self.screenshot.shape}")
            return self.screenshot

        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None

    def create_grid(self):
        """
        Divide the screenshot into a grid of cells.

        Returns:
            grid_cells: List of cell information including coordinates
            cell_dimensions: Tuple of (cell_width, cell_height)
        """
        if self.screenshot is None:
            raise ValueError("No screenshot available. Call capture_screen() first.")

        height, width = self.screenshot.shape[:2]

        # Calculate cell dimensions
        cell_width = width // self.grid_x
        cell_height = height // self.grid_y

        # Create a list to store all cells
        grid_cells = []

        # Cut the image into grid cells
        for y in range(self.grid_y):
            for x in range(self.grid_x):
                # Calculate cell boundaries
                x1 = x * cell_width
                y1 = y * cell_height
                x2 = min(
                    (x + 1) * cell_width, width
                )  # Ensure we don't exceed image bounds
                y2 = min((y + 1) * cell_height, height)

                # Extract the cell
                cell = self.screenshot[y1:y2, x1:x2]

                # Store cell along with its coordinates
                cell_info = {
                    "cell_id": f"{x}_{y}",
                    "cell": cell,
                    "position": (x, y),
                    "coordinates": (x1, y1, x2, y2),
                    "dimensions": (cell_width, cell_height),
                }
                grid_cells.append(cell_info)

        self.grid_cells = grid_cells
        self.cell_dimensions = (cell_width, cell_height)
        return grid_cells, (cell_width, cell_height)

    def visualize_grid(self):
        """
        Create a visual representation of the grid on the screenshot.

        Returns:
            grid_image: Image with grid lines drawn
        """
        if self.screenshot is None:
            raise ValueError("No screenshot available. Call capture_screen() first.")

        if self.cell_dimensions is None:
            self.create_grid()

        height, width = self.screenshot.shape[:2]
        cell_width, cell_height = self.cell_dimensions

        # Create a copy of the image to draw on
        grid_image = self.screenshot.copy()

        # Draw horizontal lines
        for y in range(1, self.grid_y):
            cv2.line(
                grid_image,
                (0, y * cell_height),
                (width, y * cell_height),
                (0, 255, 0),
                1,
            )

        # Draw vertical lines
        for x in range(1, self.grid_x):
            cv2.line(
                grid_image,
                (x * cell_width, 0),
                (x * cell_width, height),
                (0, 255, 0),
                1,
            )

        return grid_image

    @staticmethod
    def ocr_cell(cell):
        """
        Perform OCR on a cell image.

        Args:
            cell: Cell image as a numpy array

        Returns:
            data: Dictionary of OCR results
        """
        gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)
        return data

    def analyze_text_importance(self, cell_image):
        """
        Analyze text importance based on size, contrast, and density.

        Args:
            cell_image: Cell image as a numpy array

        Returns:
            importance_score: Numeric score of text importance
        """
        # Preprocess for OCR
        ocr_data = ScreenAnalyzer.ocr_cell(cell_image)

        importance_score = 0
        for i in range(len(ocr_data["text"])):
            if (
                int(ocr_data["conf"][i]) > self.confidence_threshold
                and ocr_data["text"][i].strip()
            ):  # Filter low-confidence results
                text = ocr_data["text"][i]
                h = ocr_data["height"][i]

                # Font size factor - smaller text is more important
                # Use a baseline of 20px for "normal" text
                base_size = self.base_size
                if h < base_size:
                    # Smaller text gets higher score, with a multiplier based on how small it is
                    size_factor = base_size / max(
                        h, 5
                    )  # Prevent division by very small numbers
                    size_factor = min(
                        size_factor, self.max_size_factor
                    )  # Cap at 4x importance
                else:
                    # Larger text gets progressively less importance
                    size_factor = max(
                        base_size / h, self.min_size_factor
                    )  # Floor at 1.0x importance

                # Text content factor (titles, buttons, etc. are important)
                content_factor = 1.0
                if text.lower() in ["error", "warning", "alert", "caution"]:
                    content_factor = self.error_importance
                elif any(
                    btn in text.lower() for btn in ["ok", "cancel", "submit", "save"]
                ):
                    content_factor = self.confirmation_text_importance
                elif text[0].isupper() and len(text) > 3:  # Possible title or heading
                    content_factor = self.title_importance

                # Consider text length - shorter texts might be more important (like labels, numbers)
                length_factor = 1.0
                if len(text.strip()) <= 5:
                    length_factor = self.length_importance

                # Calculate final score for this text element
                text_score = size_factor * content_factor * length_factor

                # Add some importance score for density (multiple small text items are important)
                # This will make areas with many small text elements score higher
                density_factor = self.density_importance
                importance_score += text_score + density_factor

        return importance_score

    def detect_ui_elements(self, cell_image):
        """
        Detect UI elements like buttons, input fields, checkboxes in a cell.

        Args:
            cell_image: Cell image as a numpy array

        Returns:
            cell_importance: Numeric score of UI element importance
            ui_elements: List of detected UI elements with their properties
        """
        # Convert to grayscale
        gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Find contours (potential UI elements)
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        ui_elements = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Filter out very small contours
            if w < 10 or h < 10:
                continue

            # Calculate contour properties
            aspect_ratio = w / float(h)
            area = w * h

            # Classify potential UI elements
            element_type = None
            importance = 0

            # Detect buttons (often rectangular with moderate aspect ratio)
            if 1.5 < aspect_ratio < 5 and area > 500:
                # Extract the potential button region
                button_roi = cell_image[y : y + h, x : x + w]

                # Check for text inside (buttons often have text)
                button_text = pytesseract.image_to_string(button_roi).strip()

                if button_text:
                    element_type = "button"
                    importance = self.button_importance

            # Detect input fields (often rectangular with larger aspect ratio)
            elif 3 < aspect_ratio < 10 and area > 1000:
                element_type = "input_field"
                importance = self.input_field_importance

            # Detect checkboxes (often square)
            elif 0.8 < aspect_ratio < 1.2 and 8000 < area < 1000:
                element_type = "checkbox"
                importance = self.checkbox_importance

            if element_type:
                ui_elements.append(
                    {
                        "type": element_type,
                        "bbox": (x, y, w, h),
                        "importance": importance,
                    }
                )

        cell_importance = 0
        for element in ui_elements:
            cell_importance += element["importance"]

        return cell_importance, ui_elements

    def generate_importance_grid(self):
        """
        Generate a grid with importance scores for each cell.

        Returns:
            grid_cells: List of cell information including importance scores
            cell_dimensions: Tuple of (cell_width, cell_height)
            importance_matrix: 2D numpy array of importance scores
        """
        try:
            if self.screenshot is None:
                print("No screenshot available. Attempting to capture screen now.")
                self.capture_screen(wait_seconds=1)

                # If still no screenshot, return a default grid
                if self.screenshot is None:
                    raise ValueError("Failed to capture screen after retry")

            # Verify screenshot is valid
            if len(self.screenshot.shape) != 3 or any(
                dim == 0 for dim in self.screenshot.shape
            ):
                raise ValueError(f"Invalid screenshot shape: {self.screenshot.shape}")

            # Create the grid
            start_time = timeit.default_timer()
            self.grid_cells, self.cell_dimensions = self.create_grid()

            # Create a 2D matrix to store importance scores
            self.importance_matrix = np.zeros(
                (self.grid_y, self.grid_x), dtype=np.float32
            )

            # Calculate importance for each cell
            for cell_info in self.grid_cells:
                x, y = cell_info["position"]

                # Verify cell image is valid
                cell_image = cell_info["cell"]
                if cell_image is None or cell_image.size == 0:
                    print(f"Warning: Invalid cell image at position ({x}, {y})")
                    continue

                # Calculate importance score
                try:
                    ui_importance, ui_elements = self.detect_ui_elements(cell_image)
                    text_importance = self.analyze_text_importance(cell_image)
                    total_importance = ui_importance + text_importance
                except Exception as cell_error:
                    print(f"Error analyzing cell ({x}, {y}): {cell_error}")
                    # Use default importance for this cell
                    ui_importance, ui_elements = 0, []
                    text_importance = 0
                    total_importance = 0

                # Store the importance score in the cell info
                cell_info["importance"] = total_importance
                cell_info["ui_elements"] = ui_elements
                cell_info["text_importance"] = text_importance

                # Add to the importance matrix
                self.importance_matrix[y, x] = total_importance

            end_time = timeit.default_timer()
            print(
                f"Time taken to generate importance grid: {end_time - start_time:.2f} seconds"
            )

            return self.grid_cells, self.cell_dimensions, self.importance_matrix

        except Exception as e:
            print(f"Error generating importance grid: {e}")

            # Create a default grid as fallback
            if self.grid_cells is None or self.cell_dimensions is None:
                # Get screen dimensions
                try:
                    # Try to get screen dimensions from PIL
                    import PIL.ImageGrab

                    screen = PIL.ImageGrab.grab()
                    width, height = screen.size
                except:
                    # Fallback dimensions
                    width, height = 1920, 1080

                # Calculate cell dimensions
                cell_width = width // self.grid_x
                cell_height = height // self.grid_y
                self.cell_dimensions = (cell_width, cell_height)

            # Create default importance matrix
            self.importance_matrix = np.ones(
                (self.grid_y, self.grid_x), dtype=np.float32
            )

            return [], self.cell_dimensions, self.importance_matrix

    def visualize_importance(self):
        """
        Visualize the importance score of each cell as a heatmap overlay.

        Returns:
            blended: Visualization of the screenshot with importance heatmap overlay
        """
        if (
            self.screenshot is None
            or self.grid_cells is None
            or self.importance_matrix is None
        ):
            raise ValueError(
                "Importance grid not generated. Call generate_importance_grid() first."
            )

        # Create a blank heatmap image with the same dimensions as the screenshot
        height, width = self.screenshot.shape[:2]
        heatmap = np.zeros((height, width), dtype=np.float32)

        # Get the max score for normalization
        max_score = (
            np.max(self.importance_matrix) if np.any(self.importance_matrix) else 1.0
        )

        # Build the heatmap from the importance matrix
        for cell_info in self.grid_cells:
            x, y = cell_info["position"]
            x1, y1, x2, y2 = cell_info["coordinates"]

            # Get the precalculated importance score
            score = cell_info["importance"]

            # Fill the heatmap region with the importance score
            heatmap[y1:y2, x1:x2] = score

        # Normalize heatmap values to 0-1 range
        if max_score > 0:
            heatmap = heatmap / max_score

        # Convert heatmap to color map (using a colormap like INFERNO for better visibility)
        heatmap_colored = cv2.applyColorMap(
            (heatmap * 255).astype(np.uint8), cv2.COLORMAP_INFERNO
        )

        # Create a blended visualization (overlay heatmap on screenshot)
        alpha = 0.5  # Transparency factor
        blended = cv2.addWeighted(self.screenshot, 1 - alpha, heatmap_colored, alpha, 0)

        # Draw grid lines
        cell_width, cell_height = self.cell_dimensions
        for y in range(1, self.grid_y):
            cv2.line(
                blended,
                (0, y * cell_height),
                (width, y * cell_height),
                (255, 255, 255),
                1,
            )
        for x in range(1, self.grid_x):
            cv2.line(
                blended,
                (x * cell_width, 0),
                (x * cell_width, height),
                (255, 255, 255),
                1,
            )

        # Add text labels for scores
        for cell_info in self.grid_cells:
            x, y = cell_info["position"]
            score = cell_info["importance"]

            x_pos = x * cell_width + 5  # 5 pixels padding
            y_pos = y * cell_height + 15  # 15 pixels from top for text

            # Different color based on importance
            if score > max_score * 0.7:
                color = (255, 255, 255)  # White for high importance
            else:
                color = (200, 200, 200)  # Light gray for lower importance

            # Add UI element type indicators
            ui_indicator = ""
            if "ui_elements" in cell_info and cell_info["ui_elements"]:
                ui_types = set(elem["type"] for elem in cell_info["ui_elements"])
                if ui_types:
                    ui_indicator = f" ({', '.join(ui_types)})"

            label = f"{score:.1f}{ui_indicator}"
            cv2.putText(
                blended, label, (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1
            )

        return blended

    def visualize_detailed_cell(self, cell_info):
        """
        Create a detailed visualization of a specific cell with its detected elements.

        Args:
            cell_info: Dictionary containing cell information

        Returns:
            combined_img: Visualization of the cell with detection overlays and context
        """
        if self.screenshot is None:
            raise ValueError("No screenshot available.")

        cell_img = cell_info["cell"].copy()

        # Draw UI elements if present
        if "ui_elements" in cell_info and cell_info["ui_elements"]:
            for element in cell_info["ui_elements"]:
                x, y, w, h = element["bbox"]
                element_type = element["type"]

                # Use different colors for different UI element types
                if element_type == "button":
                    color = (0, 255, 0)  # Green for buttons
                elif element_type == "input_field":
                    color = (255, 0, 0)  # Blue for input fields
                elif element_type == "checkbox":
                    color = (0, 0, 255)  # Red for checkboxes
                else:
                    color = (255, 255, 0)  # Yellow for other elements

                cv2.rectangle(cell_img, (x, y), (x + w, y + h), color, 2)
                cv2.putText(
                    cell_img,
                    element_type,
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1,
                )

        # Show the cell in context
        x1, y1, x2, y2 = cell_info["coordinates"]
        context_img = self.screenshot.copy()
        cv2.rectangle(context_img, (x1, y1), (x2, y2), (0, 255, 0), 3)

        # Resize both images to have the same height for side-by-side display
        height, width = context_img.shape[:2]
        cell_height, cell_width = cell_img.shape[:2]

        # Scale the cell image to be larger for better visibility
        scale_factor = min(height / cell_height, 4.0)
        cell_img_resized = cv2.resize(
            cell_img, (int(cell_width * scale_factor), int(cell_height * scale_factor))
        )

        # Create side-by-side display
        combined_width = width + cell_img_resized.shape[1]
        combined_img = np.zeros((height, combined_width, 3), dtype=np.uint8)
        combined_img[:, :width] = context_img

        # Center the cell image vertically in the right panel
        y_offset = max(0, (height - cell_img_resized.shape[0]) // 2)
        combined_img[
            y_offset : y_offset + cell_img_resized.shape[0],
            width : width + cell_img_resized.shape[1],
        ] = cell_img_resized

        return combined_img

    def get_most_important_cells(self, top_n=5):
        """
        Get the most important cells based on their importance scores.

        Args:
            top_n: Number of top cells to return

        Returns:
            sorted_cells: List of top N most important cells
        """
        if self.grid_cells is None or self.importance_matrix is None:
            raise ValueError(
                "Importance grid not generated. Call generate_importance_grid() first."
            )

        sorted_cells = sorted(
            self.grid_cells, key=lambda x: x["importance"], reverse=True
        )
        return sorted_cells[:top_n]

    def print_top_cells_info(self, top_n=5):
        """
        Print information about the top N most important cells.

        Args:
            top_n: Number of top cells to print information about
        """
        top_cells = self.get_most_important_cells(top_n)

        print(f"\nTop {top_n} most important cells:")
        for i, cell_info in enumerate(top_cells):
            x, y = cell_info["position"]
            score = cell_info["importance"]
            ui_elements = cell_info.get("ui_elements", [])
            ui_types = [elem["type"] for elem in ui_elements]

            print(f"{i + 1}. Cell ({x}, {y}): Score {score:.2f}")
            if ui_types:
                print(f"   - UI Elements: {', '.join(ui_types)}")
            if "text_importance" in cell_info:
                print(f"   - Text Importance: {cell_info['text_importance']:.2f}")


def main():
    # Create a screen analyzer with specified grid dimensions
    analyzer = ScreenAnalyzer(grid_x=7, grid_y=14)

    # Capture the screen after a 5-second delay
    analyzer.capture_screen(wait_seconds=5)

    # Generate the importance grid
    analyzer.generate_importance_grid()

    # Create and display the importance visualization
    importance_viz = analyzer.visualize_importance()
    cv2.imshow("Importance Heatmap", importance_viz)

    # Get and display the most important cell
    most_important_cells = analyzer.get_most_important_cells(1)
    if most_important_cells:
        detailed_viz = analyzer.visualize_detailed_cell(most_important_cells[0])
        cv2.imshow("Most Important Cell Detail", detailed_viz)

    # Print information about the top 5 most important cells
    analyzer.print_top_cells_info(5)

    # Wait for a key press to exit
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
