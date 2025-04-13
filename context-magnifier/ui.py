import sys
import os
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

        font_path = os.path.join(os.path.dirname(__file__), "fonts", "KdamThmorPro-Regular.ttf")
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
        top_widget = QSvgWidget("assets/top.svg")
        top_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        bottom_widget = QSvgWidget("assets/bottom.svg")
        bottom_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        settings_title = QSvgWidget("assets/settings.svg")
        settings_title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        leo_widget = QSvgWidget("assets/leo.svg")
        leo_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        virgo_widget = QSvgWidget("assets/virgo.svg")
        virgo_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        cancer_widget = QSvgWidget("assets/cancer.svg")
        cancer_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        

        design_widget = QSvgWidget("assets/design.svg")
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
        
        #Settings container
        settings_container = QWidget()
        settings_layout = QVBoxLayout()
        settings_container.setLayout(settings_layout)
        settings_layout.addWidget(settings_title)
        settings_layout.addWidget(scroll_area)

        #First Design Stack container
        stack1_container = QWidget()
        stack1_layout = QVBoxLayout()
        stack1_container.setLayout(stack1_layout)
        stack1_layout.addWidget(leo_widget)
        stack1_layout.addWidget(virgo_widget)

        #Middle container
        middle_container = QWidget()
        middle_layout = QHBoxLayout()
        middle_container.setLayout(middle_layout)
        middle_layout.addWidget(stack1_container)
        middle_layout.addWidget(design_widget)        
        middle_layout.addWidget(settings_container)
        middle_layout.addWidget(cancer_widget)
        middle_layout.setAlignment(
            cancer_widget,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight
        )        

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

            input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #0CBAFF;  /* Blue border matching your theme */
                }
            """)

            input.setFixedSize(200, 30)

            label_widget = QWidget()
            label_widget.setAttribute(Qt.WA_TranslucentBackground) 
            label_widget.setStyleSheet("background: transparent;")
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

        grid_layout.addWidget(middle_container)
        grid_layout.setAlignment(
            middle_container,
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