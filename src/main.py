"""
This module serves as the main entry point for the OCR-Translate-Sketch application.
It initializes and coordinates various components such as OCR processing, UI management,
and event handling, orchestrating the application's startup and shutdown procedures.
"""

import contextlib
import ctypes
import logging
import multiprocessing
import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from logging.handlers import QueueListener

from config import config
from event_manager import EventManager
from logging_utils import get_log_level, setup_main_logging
from ocr_processor import OCRProcessor
from translator import TranslationProcessor
from ui_manager import UIManager

# Check for virtual environment and set TCL/TK library paths for PyInstaller compatibility.
if "VIRTUAL_ENV" in os.environ:
    base_python_path = sys.base_prefix
    tcl_path = os.path.join(base_python_path, "tcl", "tcl8.6")
    tk_path = os.path.join(base_python_path, "tcl", "tk8.6")
    if os.path.exists(tcl_path) and os.path.exists(tk_path):
        os.environ["TCL_LIBRARY"] = tcl_path
        os.environ["TK_LIBRARY"] = tk_path


class App:
    """
    Main application class responsible for initializing and coordinating OCR processing,
    UI management, and event handling. It manages the application's lifecycle.
    """

    def __init__(self, root: tk.Tk, log_queue: multiprocessing.Queue, log_level: int):
        """
        Initializes the main application components.

        Args:
            root (tk.Tk): The root Tkinter window.
            log_queue (multiprocessing.Queue): Queue for inter-process logging.
            log_level (int): The minimum logging level.
        """
        self.root = root
        self.running = True

        self.ocr_processor = OCRProcessor(self.root, log_queue, log_level)
        
        # Initialize translation processor if enabled
        self.translator = None
        if getattr(config, "TRANSLATION_ENABLED", False):
            try:
                self.translator = TranslationProcessor()
                logging.info("Translation processor initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize translation processor: {e}")
        
        self.ui_manager = UIManager(root, self.ocr_processor, self.translator)
        self.event_manager = EventManager(self.on_exit, self.toggle_translation)

    def on_exit(self):
        """
        Handles the application shutdown process.
        Stops all running threads and processes, then safely destroys the Tkinter window.
        """
        logging.info("Initiating application shutdown...")
        self.running = False
        self.ocr_processor.stop()
        self.ui_manager.stop()
        self.event_manager.stop()
        self.root.after(0, self.root.destroy)

    def toggle_translation(self):
        """
        Toggles the translation display mode in the UI manager.
        """
        if self.ui_manager:
            self.ui_manager.toggle_translation_display()

    def start(self):
        """
        Starts the application by initializing event listeners, OCR processes, and the UI.
        Sets up the main loop for the Tkinter application and begins all core functionalities.
        """
        self.event_manager.start_tray_icon()
        self.event_manager.start_notification()

        # Start keyboard listener in a separate daemon thread to avoid blocking the UI.
        keyboard_thread = threading.Thread(target=self.event_manager.start_keyboard_listener, daemon=True)
        keyboard_thread.start()

        self.ocr_processor.start()
        self.ui_manager.start()
        self.root.mainloop()


def main():
    """
    The main entry point of the application.
    Sets up logging, configures the Tkinter root window, and initializes and starts the main application instance.
    Handles DPI awareness for proper scaling on Windows.
    """
    log_level = get_log_level(config.LOG_LEVEL)
    log_queue = setup_main_logging(log_level)
    # Create a listener for logs from the multiprocessing queue.
    log_listener = QueueListener(log_queue, *logging.getLogger().handlers)
    log_listener.start()

    # Suppress potential errors during DPI awareness setting on Windows.
    with contextlib.suppress(AttributeError, OSError):
        # Set process DPI awareness for proper scaling on high-DPI displays.
        ctypes.windll.shcore.SetProcessDpiAwareness(2)

    # Set the icon path relative to the main script
    # This ensures the icon is found whether running from source or a bundled executable
    config.ICON_PATH = Path(__file__).parent.parent / "icon.png"

    root = tk.Tk()
    # Configure window properties for a borderless, always-on-top, and transparent overlay.
    root.overrideredirect(True)
    root.wm_attributes("-topmost", True)
    root.wm_attributes("-transparentcolor", "white")
    root.attributes("-alpha", 0.8)

    # Set window to cover the entire screen.
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")

    app = App(root, log_queue, log_level)
    app.start()

    log_listener.stop()


if __name__ == "__main__":
    # Enable multiprocessing support for PyInstaller bundles.
    multiprocessing.freeze_support()
    main()
