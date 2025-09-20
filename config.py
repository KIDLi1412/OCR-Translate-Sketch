"""
This module handles application configuration, including loading settings from a YAML file,
validating configuration types, updating the configuration, and monitoring the configuration file
for changes to enable dynamic updates.
"""

import logging
import os
from typing import Any, ClassVar

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Path to the configuration file.
CONFIG_FILE = "config.yaml"


class _Config:
    """
    Manages application configuration, loading settings from a YAML file,
    and monitoring the file for changes to enable dynamic updates.
    """

    _config_types: ClassVar[dict] = {
        "TESSERACT_CMD": str,
        "OCR_LANGUAGE": str,
        "CONF_THRESHOLD": int,
        "PAR_CONF_THRESHOLD": int,
        "OCR_FPS": float,
        "DEBUG_MODE": bool,
        "STOP_HOTKEY": str,
        "UI_UPDATE_INTERVAL": int,
        "HIGHLIGHT_RECT_OUTLINE_COLOR": str,
        "HIGHLIGHT_RECT_OUTLINE_WIDTH": int,
        "DEBUG_RECT_OUTLINE_COLOR": str,
        "DEBUG_RECT_OUTLINE_WIDTH": int,
        "LOG_LEVEL": str,
    }

    def __init__(self):
        """
        Initializes the configuration by loading settings and starting the file watcher.
        """
        self._load_config()
        self._start_watcher()

    def _set_attribute(self, key: str, value: Any) -> None:
        """
        Validates, converts, and sets attributes based on the expected type.
        Ensures configuration values adhere to their defined types.

        Args:
            key (str): The name of the configuration item.
            value (Any): The value of the configuration item.
        """
        if key in self._config_types:
            expected_type = self._config_types[key]
            # Special handling for boolean values.
            if expected_type is bool:
                converted_value = str(value).lower() == "true"
                setattr(self, key, converted_value)
            else:
                try:
                    setattr(self, key, expected_type(value))
                except (ValueError, TypeError) as e:
                    logging.warning(
                        f"Value '{value}' for config item '{key}' could not be converted to {expected_type.__name__}, "
                        f"original value will be used. Error: {e}"
                    )
                    setattr(self, key, value)
        else:
            # Set attribute directly if no type is defined.
            setattr(self, key, value)

    def _load_config(self):
        """
        Loads configuration from the `config.yaml` file.
        Logs warnings or errors if the file is not found or is invalid.
        """
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                logging.info(f"Configuration file {CONFIG_FILE} is empty or invalid.")
                return

            # Set attributes for each item in the loaded configuration.
            for key, value in config_data.items():
                self._set_attribute(key, value)

            logging.info(f"Configuration reloaded from {CONFIG_FILE}.")

        except FileNotFoundError:
            logging.warning(f"Configuration file {CONFIG_FILE} not found. Default values will be used (if any).")
        except yaml.YAMLError as e:
            logging.error(f"Error loading configuration file {CONFIG_FILE}: {e}")

    def update_config_file(self, new_config: dict) -> None:
        """
        Updates the current configuration with new values and writes them to `config.yaml`.
        Handles type conversion for new values before saving.

        Args:
            new_config (dict): Dictionary of configuration items to update.
        """
        converted_config = {}
        for key, value in new_config.items():
            if key in self._config_types:
                expected_type = self._config_types[key]
                converted_value = str(value).lower() == "true" if expected_type is bool else expected_type(value)
                setattr(self, key, converted_value)
                converted_config[key] = converted_value
            else:
                setattr(self, key, value)
                converted_config[key] = value

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.safe_dump(converted_config, f, allow_unicode=True)
            logging.info(f"Configuration updated and saved to {CONFIG_FILE}.")
        except Exception as e:
            logging.error(f"Error saving configuration file: {e}")


    def _start_watcher(self):
        """
        Starts a file system watcher to monitor `config.yaml` for changes.
        Automatically reloads configuration when changes are detected.
        """
        event_handler = ConfigFileEventHandler(self)
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(CONFIG_FILE) or ".", recursive=False)
        observer.start()
        logging.info(f"Monitoring changes to {CONFIG_FILE}...")


class ConfigFileEventHandler(FileSystemEventHandler):
    """
    Custom event handler for `watchdog` to reload configuration upon file modification.
    Triggers a configuration reload when `config.yaml` is modified.
    """

    def __init__(self, config_instance: _Config):
        """
        Initializes the event handler with a reference to the _Config instance.

        Args:
            config_instance (_Config): The _Config instance to reload.
        """
        super().__init__()
        self.config_instance = config_instance

    def on_modified(self, event):
        """
        Called when a file or directory is modified.
        Reloads the configuration if the modified file is `config.yaml`.

        Args:
            event (FileSystemEvent): The event object representing the file system change.
        """
        if not event.is_directory and os.path.basename(event.src_path) == os.path.basename(CONFIG_FILE):
            logging.info(f"Changes detected in {CONFIG_FILE}, reloading configuration...")
            self.config_instance._load_config()


# Create a singleton instance for application-wide access.
config = _Config()
