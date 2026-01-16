from PyQt5.QtCore import QObject, pyqtSignal
import json
from pathlib import Path
from PIL import Image
from utils.resource_locator import resource_path
from utils.folder_validator import validate_output_folder

class Worker(QObject):
    finished = pyqtSignal(list, list)
    
    def __init__(self, image_paths, format_combo, logger=None):
        super().__init__()
        self.image_paths = image_paths
        self.format_combo = format_combo
        self.logger = logger
    

    def convert(self):
        try:

            selected_format = self.format_combo.currentText()
            with open(resource_path("settings.json"), "r") as file:
                settings = json.loads(file.read())
            
            # output folder validation
            try:
                output_path = validate_output_folder(settings.get("output_folder", ""))
                if output_path is None:
                    output_path = Path.home() / "Pictures" / "PicSwitch_Output"
            except (TypeError, PermissionError) as t:
                self.logger.error(f"{t} Using default folder.")
                output_path = Path.home() / "Pictures" / "PicSwitch_Output"
            except Exception as e:
                self.logger.error(f"Unexpected error with output folder: {e}. Using default folder.")
                output_path = Path.home() / "Pictures" / "PicSwitch_Output"

            # start conversion
            successful_paths = []
            failed_images = []
            
            for path in self.image_paths:
                try:
                    with Image.open(path) as img:
                        # Convert RGBA images to RGB if the selected format doesn't support transparency
                        if img.mode in ("RGBA", "LA", "P") and selected_format in ["JPEG", "BMP"]:
                            img = img.convert("RGB")
                        new_path = output_path / f"{Path(path).stem}.{selected_format.lower()}"
                        
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                        img.save(new_path, format=selected_format)
                    successful_paths.append(path)
                except Exception as e:
                    self.logger.error(f"Error converting {path}: {e}")
                    failed_images.append(path)
                    
            self.finished.emit(successful_paths, failed_images)

        except PermissionError:
            self.logger.error("Permission denied. File may be in use or folder is protected.")
            return

        except OSError as e:
            self.logger.error(f"File system error: {e}")
            return

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return