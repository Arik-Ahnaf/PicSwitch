import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QListWidget,
    QMessageBox
)
from PyQt5.QtCore import QThread, Qt
from PyQt5.QtGui import QIcon, QMovie
from pathlib import Path
from utils.worker import Worker
import json
from utils.resource_locator import resource_path
from utils.logger import get_logger


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PicSwitch")

        self.logger = get_logger()
        self.starting_folder = None
        self.image_paths = []
        self.image_names = []
        self.thread = None
        self.worker = None
        layout = QVBoxLayout()
        first_row = QHBoxLayout()
        self.setMinimumSize(400, 500)
        # self.setMaximumSize(700, 700)


        self.select_btn = QPushButton(" Select Images")
        self.select_btn.setObjectName("selectButton")
        self.select_btn.clicked.connect(self.open_image_dialog)


        self.clear_all_btn = QPushButton(" Clear All ")
        self.clear_all_btn.setObjectName("clearAllButton")
        self.clear_all_btn.clicked.connect(self.clear_all_images)
        

        self.convert_btn = QPushButton(" Convert ")
        self.convert_btn.setObjectName("convertButton")
        self.convert_btn.clicked.connect(self.start_conversion)


        self.list_widget = QListWidget()
        self.list_widget.setItemAlignment(Qt.AlignCenter)
    

        self.format_label = QLabel("Select output image format:")
        self.format_label.setStyleSheet("font-size: 14px")
        

        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "PNG",
            "JPEG",
            "WEBP",
            "BMP",
            "TIFF"
        ])
        self.format_combo.setCurrentText("PNG")
        self.format_combo.setToolTip("Select image output format")
        self.format_combo.setStyleSheet("font-size: 14px; padding: 4px")


        first_row.addWidget(self.select_btn)
        first_row.addWidget(self.clear_all_btn)
        layout.addLayout(first_row)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.format_label)
        layout.addWidget(self.format_combo)
        layout.addWidget(self.convert_btn)
        self.setLayout(layout)


    def clear_all_images(self):
        self.image_paths = []
        self.image_names = []
        self.update_list_widget()
        

    def open_image_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image(s)",
            self.starting_folder if self.starting_folder else str(Path.home() / "Pictures"),
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tiff)"
        )

        if files:
            self.image_paths = files
            self.image_names = [file.split("/")[-1] for file in files]
            self.update_list_widget()


    def update_list_widget(self, failed_paths=[]):
        self.list_widget.clear()
        if failed_paths and len(failed_paths) > 10:
            for name in failed_paths:
                self.list_widget.addItem(name)
        else:
            for name in self.image_names:
                self.list_widget.addItem(name)


    def start_conversion(self):
        self.thread = QThread()
        self.worker = Worker(self.image_paths, self.format_combo, self.logger)
        self.worker.moveToThread(self.thread)

        # Connect the worker's finished signal to clean up the thread and callback
        self.worker.finished.connect(self.on_conversion_complete)
        self.worker.finished.connect(self.thread.quit)

        self.thread.finished.connect(self.cleanup_thread)
        self.thread.started.connect(self.worker.convert)
        self.thread.start()
    
        self.updates_window = UpdatesWindow()
        self.updates_window.show()


    def on_conversion_complete(self, successful_paths, failed_paths=[]):
        """Callback after conversion completes to clear converted images from the list."""
        self.image_paths = [path for path in self.image_paths if path not in successful_paths]
        self.image_names = [name for name in self.image_names if name not in [Path(path).name for path in successful_paths]]

        self.update_list_widget(failed_paths)
        self.updates_window.movie.stop()
        self.updates_window.gif_label.hide()

        if not failed_paths:
            self.updates_window.close()
            QMessageBox.information(
                self,
                "Conversion Completed",
                "All images have been successfully converted!"
            )
        else:
            self.updates_window.label.setText(f"Conversion Completed with {len(failed_paths)} failure(s). Check the log file for details.")
            self.updates_window.ok_button.setVisible(True)
            QMessageBox.warning(
                self,
                "Conversion Completed with Errors",
                f"Some images failed to convert. {len(failed_paths)} image(s) could not be processed. Please check the log file for details."
            )
    

    def cleanup_thread(self):

        self.worker.deleteLater()
        self.thread.deleteLater()
        self.thread = None
        self.worker = None


class UpdatesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.setWindowTitle("Updates")
        self.setFixedSize(600, 200)


        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setFixedSize(64, 64)
        self.gif_label.setScaledContents(True)


        self.layout.addWidget(self.gif_label, 0, Qt.AlignHCenter)
        self.setLayout(self.layout)


        self.movie = QMovie(resource_path("assets/loading.gif"))
        self.gif_label.setMovie(self.movie)
        self.movie.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/logo.svg")))

    window = Window()
    window.setObjectName("body")
    window.show()

    default_settings = {
        "theme": "default",
        "output_folder": "",
        "starting_folder": ""
    }
    
    try:

        with open(resource_path("settings.json"), "r") as file:
            data = json.loads(file.read())

    except (FileNotFoundError, json.JSONDecodeError):

        data = default_settings
        with open(resource_path("settings.json"), "w") as file:
            json.dump(default_settings, file)
    
    window.starting_folder = data.get("starting_folder", None)

    with open(resource_path("styles/default.qss"), 'r') as f:
        app.setStyleSheet(f.read())

    sys.exit(app.exec())
