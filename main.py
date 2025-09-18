import contextlib
import ctypes
import logging
import multiprocessing
import os
import sys
import threading
import tkinter as tk
from logging.handlers import QueueListener

from config import Config
from event_manager import EventManager
from logging_utils import get_log_level, setup_main_logging
from ocr_processor import OCRProcessor
from ui_manager import UIManager

if "VIRTUAL_ENV" in os.environ:
    base_python_path = sys.base_prefix
    tcl_path = os.path.join(base_python_path, "tcl", "tcl8.6")
    tk_path = os.path.join(base_python_path, "tcl", "tk8.6")
    if os.path.exists(tcl_path) and os.path.exists(tk_path):
        os.environ["TCL_LIBRARY"] = tcl_path
        os.environ["TK_LIBRARY"] = tk_path


class App:
    """
    App 是应用程序的主类, 负责初始化和协调各个模块。
    """

    def __init__(self, root: tk.Tk, log_queue: multiprocessing.Queue, log_level: int):
        """
        初始化 App。

        Args:
            root (tk.Tk): Tkinter 的根窗口。
            log_queue (multiprocessing.Queue): 日志队列。
            log_level (int): 日志级别。
        """
        self.root = root
        self.running = True

        self.ocr_processor = OCRProcessor(self.root, log_queue, log_level)
        self.ui_manager = UIManager(root, self.ocr_processor)
        self.event_manager = EventManager(self.on_exit)

    def on_exit(self):
        """
        程序退出时的处理函数, 停止所有线程并销毁窗口。
        """
        logging.info("Initiating shutdown...")  # 使用 logging.info
        self.running = False
        self.ocr_processor.stop()
        self.ui_manager.stop()
        self.event_manager.stop()
        self.root.after(0, self.root.destroy)

    def start(self):
        """
        启动应用程序。
        """
        self.event_manager.start_tray_icon()
        self.event_manager.start_notification()

        # 启动键盘监听线程
        keyboard_thread = threading.Thread(target=self.event_manager.start_keyboard_listener, daemon=True)
        keyboard_thread.start()

        # 启动 OCR 进程
        self.ocr_processor.start()

        # 启动 UI 更新
        self.ui_manager.start()
        self.root.mainloop()


def main():
    """
    应用程序的入口点。
    初始化 Tkinter 窗口并启动 App。
    """
    config = Config()
    log_level = get_log_level(config.LOG_LEVEL)
    log_queue = setup_main_logging(log_level)
    # 从队列中获取日志记录的监听器
    log_listener = QueueListener(log_queue, *logging.getLogger().handlers)
    log_listener.start()

    with contextlib.suppress(AttributeError, OSError):
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # 设置 DPI 感知

    root = tk.Tk()
    root.overrideredirect(True)  # 隐藏窗口边框
    root.wm_attributes("-topmost", True)  # 窗口置顶
    root.wm_attributes("-transparentcolor", "white")  # 透明颜色
    root.attributes("-alpha", 0.8)  # 窗口透明度

    screen_width = root.winfo_screenwidth()  # 获取屏幕宽度
    screen_height = root.winfo_screenheight()  # 获取屏幕高度
    root.geometry(f"{screen_width}x{screen_height}+0+0")  # 窗口大小和位置

    app = App(root, log_queue, log_level)
    app.start()

    # 停止日志监听器
    log_listener.stop()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
