import sys
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QGridLayout, QWidget, QHBoxLayout,
    QLabel, QLineEdit, QScrollArea, QVBoxLayout, QSizePolicy
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtGui import QFontDatabase, QFont



class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        font_id = QFontDatabase.addApplicationFont("fonts/KdamThmorPro-Regular.ttf")  

        if font_id == -1:
            print("Failed to load font!")
        else:
            # Get the font family name
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

        custom_font = QFont(font_family, 20)

        central_widget = QWidget()
        grid_layout = QGridLayout()
        central_widget.setLayout(grid_layout)
        self.setCentralWidget(central_widget)

        # SVG widgets
        top_widget = QSvgWidget("assets/top.svg")
        top_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        bottom_widget = QSvgWidget("assets/bottom.svg")
        bottom_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        settings_title = QSvgWidget("assets/settings.svg")
        settings_title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) 
        
        scroll_content = QWidget()
        scroll_content.setLayout(QVBoxLayout())

        scroll_area.setStyleSheet("""
            QScrollArea {
                background: rgba(255, 255, 255, 0.10); 
                border: 2.5px solid #0CBAFF;
                min-width: 597px;
                max-width: 597px;
                min-height: 399px;
                max-height: 399px;
            }
        """)

        settings_container = QWidget()
        settings_layout = QVBoxLayout()
        settings_container.setLayout(settings_layout)
        settings_layout.addWidget(settings_title)
        settings_layout.addWidget(scroll_area)

        def SettingWidget(label):
            label = QLabel(label)
            label.setFont(custom_font)
            label.setStyleSheet("""
                QLabel {
                    color: #0CBAFF;
                    background: transparent;
                }
            """)

            label.setSizePolicy(
                QSizePolicy.Policy.Expanding,  
                QSizePolicy.Policy.Fixed      
            )
            input = QLineEdit()

            label_widget = QWidget()
            label_layout = QHBoxLayout(label_widget)
            

            label_layout.addWidget(label)
            label_layout.addWidget(input, stretch=1)

            scroll_content.layout().addWidget(label_widget)    

        SettingWidget("grid y")
        SettingWidget("base size")
        SettingWidget("max size")
        SettingWidget("min size")
        SettingWidget("confidence threshold")
        SettingWidget("button importance")
        SettingWidget("input field importance")
        SettingWidget("checkbox importance")
        SettingWidget("confirmation importance")
        SettingWidget("error importance")
        SettingWidget("comfortation importance")
        SettingWidget("title importance")
        SettingWidget("length importance")
        SettingWidget("density importance")

        scroll_content.layout().setAlignment(Qt.AlignTop)

        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content)
        scroll_area.setAlignment(Qt.AlignTop) 
        
        grid_layout.addWidget(top_widget) 

        grid_layout.setAlignment(
            top_widget, 
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )

        grid_layout.addWidget(settings_container)
        grid_layout.setAlignment(
            settings_container,
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter
        )

        close_button = QPushButton("close")

        close_button.clicked.connect(self.close)
        close_button.setFixedSize(100, 40)  
        close_button.setFont(custom_font)
        grid_layout.addWidget(close_button)
        grid_layout.setAlignment(
            close_button,
            Qt.AlignmentFlag.AlignHCenter
        )

        grid_layout.addWidget(bottom_widget)
        grid_layout.setAlignment(
            bottom_widget,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
        )
        
        self.showFullScreen()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()
    sys.exit(app.exec())