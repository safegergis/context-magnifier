import multiprocessing
from app.main_window import run_main_window
from facial_recognition.main import EyeTracker
from ocr.main import ScreenAnalyzer
import numpy as np
from collections import defaultdict
import ctypes

from app.zoom_window import run_zoom_window


def find_most_important_cells(grid_cells, importance_matrix, screen_position):
    """
    Find the most important cells in the importance matrix based on the screen position.

    Args:
        grid_cells: List of cell information including coordinates
        importance_matrix: Matrix of importance values for each cell
        screen_position: Tuple (x, y) representing the current screen position

    Returns:
        List of important cell clusters near the screen position
    """

    # Convert screen position to grid cell coordinates
    x, y = screen_position
    grid_x, grid_y = len(importance_matrix[0]), len(importance_matrix)

    # Find the cell that contains the screen position
    cell_width = grid_cells[0]["dimensions"][0]
    cell_height = grid_cells[0]["dimensions"][1]

    grid_pos_x = int(min(x / cell_width, grid_x - 1))
    grid_pos_y = int(min(y / cell_height, grid_y - 1))

    # Define search radius (adjust as needed)
    search_radius = 3

    # Find cells within the radius
    important_cells = []
    for i in range(
        max(0, grid_pos_y - search_radius), min(grid_y, grid_pos_y + search_radius + 1)
    ):
        for j in range(
            max(0, grid_pos_x - search_radius),
            min(grid_x, grid_pos_x + search_radius + 1),
        ):
            # Calculate distance from current position
            distance = np.sqrt((grid_pos_y - i) ** 2 + (grid_pos_x - j) ** 2)

            # Add cell if it's important (importance above threshold)
            importance = importance_matrix[i][j]
            if importance > 0.5:  # Threshold can be adjusted
                cell_info = next(
                    (cell for cell in grid_cells if cell["position"] == (j, i)), None
                )
                if cell_info:
                    important_cells.append(
                        {
                            "cell_info": cell_info,
                            "importance": importance,
                            "distance": distance,
                        }
                    )

    # Cluster important cells that are adjacent
    clusters = []
    visited = set()

    def dfs(cell_idx, current_cluster):
        visited.add(cell_idx)
        current_cluster.append(important_cells[cell_idx])

        # Check neighbors
        for neighbor_idx in range(len(important_cells)):
            if neighbor_idx not in visited:
                cell1 = important_cells[cell_idx]["cell_info"]["position"]
                cell2 = important_cells[neighbor_idx]["cell_info"]["position"]

                # If cells are adjacent (including diagonals)
                if abs(cell1[0] - cell2[0]) <= 1 and abs(cell1[1] - cell2[1]) <= 1:
                    dfs(neighbor_idx, current_cluster)

    # Find all clusters
    for i in range(len(important_cells)):
        if i not in visited:
            current_cluster = []
            dfs(i, current_cluster)
            if current_cluster:
                clusters.append(current_cluster)

    # Sort clusters by average importance and distance from screen position
    clusters.sort(
        key=lambda cluster: (
            -sum(cell["importance"] for cell in cluster)
            / len(cluster),  # Higher importance first
            min(cell["distance"] for cell in cluster),  # Closer distance first
        )
    )

    # Debug information about clusters
    print(f"Found {len(clusters)} clusters of important cells")
    for i, cluster in enumerate(clusters):
        avg_importance = sum(cell["importance"] for cell in cluster) / len(cluster)
        min_distance = min(cell["distance"] for cell in cluster)
        cells_positions = [cell["cell_info"]["position"] for cell in cluster]
        print(
            f"Cluster {i + 1}: {len(cluster)} cells, avg importance: {avg_importance:.2f}, "
            f"min distance: {min_distance:.2f}, positions: {cells_positions}"
        )

    return clusters


if __name__ == "__main__":
    tracker = EyeTracker()
    screen_analyzer = ScreenAnalyzer()

    # Create shared memory for coordinates
    shared_x = multiprocessing.Value(ctypes.c_double, 0.0)
    shared_y = multiprocessing.Value(ctypes.c_double, 0.0)

    if tracker.calibrate():

        def handle_gaze(coords):
            x, y = coords
            # Update shared memory values
            shared_x.value = float(x)
            shared_y.value = float(y)

        tracking_thread = tracker.start_tracking(callback=handle_gaze, fps=4)

        # When done
        # tracker.stop_tracking()

    screen_analyzer.capture_screen()
    grid_cells, cell_dimensions, importance_matrix = (
        screen_analyzer.generate_importance_grid()
    )

    def return_coords():
        return (shared_x.value, shared_y.value)

    p1 = multiprocessing.Process(target=run_zoom_window, args=(return_coords,))
    p2 = multiprocessing.Process(target=run_main_window)

    p1.start()
    p2.start()

    p1.join()
    # Stop tracking when processes finish
    tracker.stop_tracking()
