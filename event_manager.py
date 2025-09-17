import logging
import tkinter as tk
from tkinter import messagebox, ttk

import pystray
from PIL import Image
from pynput import keyboard
from win10toast_persist import ToastNotifier

from config import Config


class EventManager:
    """
    EventManager 类负责处理应用程序的事件, 包括键盘监听和任务栏图标。
    它提供启动和停止这些事件监听的方法。
    """

    def __init__(self, on_exit_callback):
        """
        初始化 EventManager。

        Args:
            on_exit_callback (function): 当程序退出时调用的回调函数。
        """
        self.on_exit_callback = on_exit_callback
        self.listener = None
        self.icon = None
        self.settings_window = None

    def start_tray_icon(self):
        """
        设置任务栏图标和菜单。
        """
        logging.info("启动托盘图标...") # 使用 logging.info
        image = Image.open("icon.png")
        menu = (pystray.MenuItem('设置', self.open_settings),
                pystray.MenuItem('退出', self.on_exit_callback),)
        self.icon = pystray.Icon("OCR-Translate-Sketch", image, "OCR-Translate-Sketch", menu)
        self.icon.run_detached()

    def open_settings(self):
        """
        打开设置窗口。
        """
        logging.info("打开设置窗口...") # 使用 logging.info
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self.icon)
        self.settings_window.deiconify()
        self.settings_window.focus_force()

    def start_keyboard_listener(self):
        """
        启动键盘监听器, 监听停止热键。
        """
        logging.info(f"启动键盘监听器, 监听热键: {Config().STOP_HOTKEY}") # 使用 logging.info
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(Config().STOP_HOTKEY),
            self.on_exit_callback
        )

        def on_press(key):
            hotkey.press(self.listener.canonical(key))

        def on_release(key):
            hotkey.release(self.listener.canonical(key))

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            self.listener = listener
            listener.join()

    def start_notification(self):
        """
        显示程序启动通知。
        """
        toaster = ToastNotifier()
        toaster.show_toast(
            "OCR-Translate-Sketch",
            "程序已启动, 按 " + Config().STOP_HOTKEY + " 停止",
            duration=5,
            threaded=True,
        )

    def stop(self):
        """
        停止事件管理器, 包括键盘监听和任务栏图标。
        """
        logging.info("停止事件管理器...") # 使用 logging.info
        if self.listener:
            self.listener.stop()
            logging.info("键盘监听器已停止。") # 使用 logging.info
        if self.icon:
            self.icon.stop()
            logging.info("托盘图标已停止。") # 使用 logging.info
        if self.settings_window:
            self.settings_window.destroy()
            logging.info("设置窗口已销毁。") # 使用 logging.info


class SettingsWindow(tk.Toplevel):
    """
    设置窗口类, 用于显示和修改应用程序配置。
    """

    def __init__(self, tray_icon):
        """
        初始化设置窗口。

        Args:
            tray_icon (pystray.Icon): 任务栏图标实例。
        """
        super().__init__()
        self.tray_icon = tray_icon
        self.title("设置")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.config_entries = {}
        self._load_config_to_ui()
        self._create_widgets()
        logging.info("设置窗口已初始化。") # 使用 logging.info

    def _load_config_to_ui(self):
        """
        从 Config 类加载配置到 UI 界面。
        """
        config = Config()
        for key in dir(config):
            if not key.startswith('_') and key.isupper():
                value = getattr(config, key)
                self.config_entries[key] = tk.StringVar(value=str(value))

    def _create_widgets(self):
        """
        创建设置窗口的 UI 控件。
        """
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for row_idx, (key, var) in enumerate(self.config_entries.items()):
            ttk.Label(scrollable_frame, text=key + ":").grid(row=row_idx, column=0, sticky="w", pady=2)
            entry = ttk.Entry(scrollable_frame, textvariable=var, width=40)
            entry.grid(row=row_idx, column=1, sticky="ew", pady=2)

        ttk.Button(main_frame, text="确认", command=self._save_config).pack(pady=10)

    def _save_config(self):
        updated_config = {}
        for key, var in self.config_entries.items():
            value = var.get()
            if key in ['CONF_THRESHOLD', 'PAR_CONF_THRESHOLD']:
                updated_config[key] = int(value)
            elif key == 'OCR_FPS':
                updated_config[key] = float(value)
            elif key == 'DEBUG_MODE':
                updated_config[key] = value.lower() == 'true'
            else:
                updated_config[key] = value
        try:
            Config().update_config_file(updated_config)
            logging.info("配置已保存成功!")  # 使用 logging.info
            messagebox.showinfo("设置", "配置已保存成功!")
            self.destroy()
        except Exception as e:
            logging.error(f"保存配置失败: {e}") # 使用 logging.error
            messagebox.showerror("错误", f"保存配置失败: {e}")

    def _on_closing(self):
        """
        处理窗口关闭事件。
        """
        logging.info("设置窗口正在关闭...") # 使用 logging.info
        self.withdraw()
