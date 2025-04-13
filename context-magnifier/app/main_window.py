import sys
import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QGridLayout,
    QWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QSizePolicy,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtGui import QFontDatabase, QFont


class TransparentWindow(QMainWindow):
    settings_changed_signal = Signal(dict)
    enable_eye_tracking_signal = Signal(
        str
    )  # Signal to enable eye tracking with calibration file path

    def __init__(self, settings_queue=None, command_queue=None):
        super().__init__()

        self.settings_inputs = {}
        self.settings_queue = settings_queue
        self.command_queue = command_queue

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        font_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "fonts",
            "KdamThmorPro-Regular.ttf",
        )
        font_id = QFontDatabase.addApplicationFont(font_path)

        if font_id == -1:
            print("Failed to load font!")
        else:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

        custom_font = QFont(font_family, 20)

        central_widget = QWidget()
        grid_layout = QGridLayout()
        central_widget.setLayout(grid_layout)
        self.setCentralWidget(central_widget)

        # SVG widgets
        top_widget = QSvgWidget(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "assets", "top.svg"
            )
        )
        top_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        bottom_widget = QSvgWidget(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "assets", "bottom.svg"
            )
        )
        bottom_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        settings_title = QSvgWidget(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "assets", "settings.svg"
            )
        )
        settings_title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        leo_widget = QSvgWidget(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "assets", "leo.svg"
            )
        )
        leo_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        virgo_widget = QSvgWidget(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "assets", "virgo.svg"
            )
        )
        virgo_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        cancer_widget = QSvgWidget(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "assets", "cancer.svg"
            )
        )
        cancer_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        design_widget = QSvgWidget(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "assets", "design.svg"
            )
        )
        design_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setLayout(QVBoxLayout())
        scroll_content.setAttribute(Qt.WA_TranslucentBackground)
        scroll_content.setStyleSheet("background: transparent;")

        scroll_area.setStyleSheet("""
            QScrollArea {
                background: rgba(255, 255, 255, 0.12); 
                border: 2.5px solid #0CBAFF;
                min-width: 597px;
                max-width: 597px;
                min-height: 399px;
                max-height: 399px;
            }
        """)

        # Settings container
        settings_container = QWidget()
        settings_layout = QVBoxLayout()
        settings_container.setLayout(settings_layout)
        settings_layout.addWidget(settings_title)
        settings_layout.addWidget(scroll_area)

        # First Design Stack container
        stack1_container = QWidget()
        stack1_layout = QVBoxLayout()
        stack1_container.setLayout(stack1_layout)
        stack1_layout.addWidget(leo_widget)
        stack1_layout.addWidget(virgo_widget)

        # Middle container
        middle_container = QWidget()
        middle_layout = QHBoxLayout()
        middle_container.setLayout(middle_layout)
        middle_layout.addWidget(stack1_container)
        middle_layout.addWidget(design_widget)
        middle_layout.addWidget(settings_container)
        middle_layout.addWidget(cancer_widget)
        middle_layout.setAlignment(
            cancer_widget, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight
        )

        def SettingWidget(label, default_value=""):
            label_widget = QLabel(label)
            label_widget.setFont(custom_font)
            label_widget.setStyleSheet("""
                QLabel {
                    color: #0CBAFF;
                    background: transparent;
                }
            """)

            label_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            input = QLineEdit()
            input.setText(str(default_value))

            input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #0CBAFF;  /* Blue border matching your theme */
                    color: white;
                    background: rgba(0, 0, 0, 0.5);
                }
            """)

            input.setFixedSize(200, 30)

            container_widget = QWidget()
            container_widget.setAttribute(Qt.WA_TranslucentBackground)
            container_widget.setStyleSheet("background: transparent;")
            container_layout = QHBoxLayout(container_widget)

            container_layout.addWidget(label_widget)
            container_layout.addWidget(input, stretch=1)

            scroll_content.layout().addWidget(container_widget)

            # Save the input field using the label as key
            self.settings_inputs[label] = input

        # Add settings with default values
        SettingWidget("grid x", "16")
        SettingWidget("grid y", "9")
        SettingWidget("base size", "20")
        SettingWidget("max size factor", "4")
        SettingWidget("min size factor", "1")
        SettingWidget("confidence threshold", "20")
        SettingWidget("button importance", "3")
        SettingWidget("input field importance", "2")
        SettingWidget("checkbox importance", "1")
        SettingWidget("confirmation importance", "3")
        SettingWidget("error importance", "2.5")
        SettingWidget("title importance", "1.5")
        SettingWidget("length importance", "1.5")
        SettingWidget("density importance", "0.2")

        scroll_content.layout().setAlignment(Qt.AlignTop)

        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content)
        scroll_area.setAlignment(Qt.AlignTop)

        grid_layout.addWidget(top_widget)

        grid_layout.setAlignment(
            top_widget, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )

        grid_layout.addWidget(middle_container)
        grid_layout.setAlignment(
            middle_container,
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter,
        )

        # Button Container
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_container.setLayout(button_layout)

        # Apply Button
        apply_button = QPushButton("apply")
        apply_button.clicked.connect(self.apply_settings)
        apply_button.setFixedSize(100, 40)
        apply_button.setFont(custom_font)
        apply_button.setStyleSheet("""
            QPushButton {
                background-color: #0CBAFF;
                color: black;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0A9AE0;
            }
        """)

        # Eye Tracking Button
        eye_tracking_button = QPushButton("eye tracking")
        eye_tracking_button.clicked.connect(self.enable_eye_tracking)
        eye_tracking_button.setFixedSize(150, 40)
        eye_tracking_button.setFont(custom_font)
        eye_tracking_button.setStyleSheet("""
            QPushButton {
                background-color: #0CBAFF;
                color: black;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0A9AE0;
            }
        """)

        # Continuous Updates Button
        continuous_updates_button = QPushButton("continuous updates")
        continuous_updates_button.clicked.connect(self.toggle_continuous_updates)
        continuous_updates_button.setFixedSize(200, 40)
        continuous_updates_button.setFont(custom_font)
        continuous_updates_button.setStyleSheet("""
            QPushButton {
                background-color: #0CBAFF;
                color: black;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0A9AE0;
            }
        """)

        # Close Button
        close_button = QPushButton("close")
        close_button.clicked.connect(self.close)
        close_button.setFixedSize(100, 40)
        close_button.setFont(custom_font)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(200, 200, 200, 0.3);
                color: #0CBAFF;
                border: 2px solid #0CBAFF;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(200, 200, 200, 0.5);
            }
        """)

        # Add buttons to layout
        button_layout.addWidget(apply_button)
        button_layout.addWidget(eye_tracking_button)
        button_layout.addWidget(continuous_updates_button)
        button_layout.addWidget(close_button)

        grid_layout.addWidget(button_container)
        grid_layout.setAlignment(button_container, Qt.AlignmentFlag.AlignHCenter)

        grid_layout.addWidget(bottom_widget)
        grid_layout.setAlignment(
            bottom_widget, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
        )

        self.showFullScreen()

    def get_settings(self):
        """Get all settings as a dictionary with appropriate type conversion"""
        settings = {}
        try:
            for label, input_field in self.settings_inputs.items():
                value = input_field.text().strip()

                # Convert numeric values to their appropriate types
                if label in ["grid x", "grid y", "confidence threshold"]:
                    settings[label] = int(value) if value else 0
                else:
                    try:
                        settings[label] = float(value) if value else 0.0
                    except ValueError:
                        settings[label] = value

            return settings
        except Exception as e:
            print(f"Error getting settings: {e}")
            return {}

    def apply_settings(self):
        """Apply the settings by sending them through the queue or emitting a signal"""
        try:
            settings = self.get_settings()
            if not settings:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Failed to get settings. Please check your input values.",
                )
                return

            # Display success message
            QMessageBox.information(self, "Success", "Settings applied successfully!")

            # Send settings via queue if available
            if self.settings_queue:
                self.settings_queue.put(settings)

            # Emit signal for local connections
            self.settings_changed_signal.emit(settings)

            print("Applied settings:", settings)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {e}")
            print(f"Error applying settings: {e}")

    def enable_eye_tracking(self):
        """Enable eye tracking with calibration file"""
        try:
            # Open file dialog to select calibration file
            file_dialog = QFileDialog()
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            file_dialog.setNameFilter("Calibration files (*.json)")
            if file_dialog.exec():
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    calibration_file = selected_files[0]
                    # Send command to enable eye tracking with calibration file
                    if self.command_queue:
                        self.command_queue.put(
                            {
                                "command": "enable_eye_tracking",
                                "file": calibration_file,
                            }
                        )
        except Exception as e:
            print(f"Error enabling eye tracking: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to enable eye tracking: {str(e)}"
            )

    def toggle_continuous_updates(self):
        """Toggle continuous updates for the importance map"""
        try:
            # Send command to toggle continuous updates
            if self.command_queue:
                self.command_queue.put(
                    {
                        "command": "toggle_continuous_updates",
                    }
                )
                QMessageBox.information(
                    self,
                    "Continuous Updates",
                    "Toggled continuous importance map updates",
                )
        except Exception as e:
            print(f"Error toggling continuous updates: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to toggle continuous updates: {str(e)}"
            )


def run_main_window(settings_queue=None, command_queue=None):
    app = QApplication(sys.argv)
    window = TransparentWindow(settings_queue, command_queue)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_main_window()
