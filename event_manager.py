"""
This module defines the EventManager and SettingsWindow classes for the OCR-Translate-Sketch application.

- The `EventManager` handles keyboard listening, system tray icon management, and notifications.
- The `SettingsWindow` provides a graphical user interface for viewing and modifying application settings.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk

import pystray
from PIL import Image
from pynput import keyboard
from win10toast_persist import ToastNotifier

from config import config


class EventManager:
    """
    Manages application events such as keyboard input, system tray interactions, and notifications.
    """

    def __init__(self, on_exit_callback):
        """
        Initializes the EventManager with an exit callback.

        Args:
            on_exit_callback (function): Function to call when the application is requested to exit.
        """
        self.on_exit_callback = on_exit_callback
        self.listener = None
        self.icon = None
        self.settings_window = None

    def start_tray_icon(self):
        """
        Sets up and starts the system tray icon with a context menu.
        The menu includes options to open settings and exit the application.
        """
        logging.info("Starting tray icon...")
        image = Image.open("icon.png")
        menu = (
            pystray.MenuItem("Settings", self.open_settings),
            pystray.MenuItem("Exit", self.on_exit_callback),
        )
        self.icon = pystray.Icon("OCR-Translate-Sketch", image, "OCR-Translate-Sketch", menu)
        self.icon.run_detached()

    def open_settings(self):
        """
        Opens the application settings window.
        Creates a new window if one doesn't exist or is closed; otherwise, brings the existing one to the foreground.
        """
        logging.info("Opening settings window...")
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self.icon)
        self.settings_window.deiconify()
        self.settings_window.focus_force()

    def start_keyboard_listener(self):
        """
        Starts a keyboard listener to monitor for the configured STOP_HOTKEY.
        Triggers the `on_exit_callback` when the hotkey is pressed.
        """
        logging.info(f"Starting keyboard listener, monitoring hotkey: {config.STOP_HOTKEY}")
        hotkey = keyboard.HotKey(keyboard.HotKey.parse(config.STOP_HOTKEY), self.on_exit_callback)

        def on_press(key):
            """
            Handles key press events for the keyboard listener.
            """
            hotkey.press(self.listener.canonical(key))

        def on_release(key):
            """
            Handles key release events for the keyboard listener.
            """
            hotkey.release(self.listener.canonical(key))

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            self.listener = listener
            listener.join()

    def start_notification(self):
        """
        Displays a Windows 10 toast notification indicating the program has started
        and how to stop it.
        """
        toaster = ToastNotifier()
        toaster.show_toast(
            "OCR-Translate-Sketch",
            f"Program started, press {config.STOP_HOTKEY} to stop",
            duration=5,
            threaded=True,
        )

    def stop(self):
        """
        Stops all active components: keyboard listener, system tray icon, and settings window.
        """
        logging.info("Stopping event manager...")
        if self.listener:
            self.listener.stop()
            logging.info("Keyboard listener stopped.")
        if self.icon:
            self.icon.stop()
            logging.info("Tray icon stopped.")
        if self.settings_window:
            self.settings_window.destroy()
            logging.info("Settings window destroyed.")


class SettingsWindow(tk.Toplevel):
    """
    A Tkinter Toplevel window for displaying and modifying application configuration settings.
    """

    def __init__(self, tray_icon):
        """
        Initializes the SettingsWindow.

        Args:
            tray_icon (pystray.Icon): The system tray icon instance.
        """
        super().__init__()
        self.tray_icon = tray_icon
        self.title("Settings")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.config_entries = {}
        self._load_config_to_ui()
        self._create_widgets()
        logging.info("Settings window initialized.")

    def _load_config_to_ui(self):
        """
        Loads configuration values from the `config` module into Tkinter `StringVar` objects
        to populate the settings UI. Only uppercase attributes are considered.
        """
        for key in dir(config):
            if not key.startswith("_") and key.isupper():
                value = getattr(config, key)
                self.config_entries[key] = tk.StringVar(value=str(value))

    def _create_widgets(self):
        """
        Creates and arranges the widgets within the settings window,
        including a scrollable frame for configuration entries and a save button.
        """
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for row_idx, (key, var) in enumerate(self.config_entries.items()):
            ttk.Label(scrollable_frame, text=key + ":").grid(row=row_idx, column=0, sticky="w", pady=2)
            entry = ttk.Entry(scrollable_frame, textvariable=var, width=40)
            entry.grid(row=row_idx, column=1, sticky="ew", pady=2)

        ttk.Button(main_frame, text="Confirm", command=self._save_config).pack(pady=10)

    def _save_config(self):
        """
        Saves the configuration settings from the UI to the `config` module.
        Handles type conversion and provides user feedback.
        """
        updated_config = {}
        for key, var in self.config_entries.items():
            value = var.get()
            if key in ["CONF_THRESHOLD", "PAR_CONF_THRESHOLD"]:
                updated_config[key] = int(value)
            elif key == "OCR_FPS":
                updated_config[key] = float(value)
            elif key == "DEBUG_MODE":
                updated_config[key] = value.lower() == "true"
            else:
                updated_config[key] = value
        try:
            config.update_config_file(updated_config)
            logging.info("Configuration saved successfully!")
            messagebox.showinfo("Settings", "Configuration saved successfully!")
            self.destroy()
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def _on_closing(self):
        """
        Handles the window closing event by hiding the window instead of destroying it.
        This allows the window to be re-opened without re-initialization.
        """
        logging.info("Settings window is closing...")
        self.withdraw()
