import ctypes
import os
import sys
import threading
import tkinter as tk

from config import Config
from ocr_processor import OCRProcessor
from ui_manager import UIManager
from event_manager import EventManager


if "VIRTUAL_ENV" in os.environ:
    base_python_path = sys.base_prefix
    tcl_path = os.path.join(base_python_path, 'tcl', 'tcl8.6')
    tk_path = os.path.join(base_python_path, 'tcl', 'tk8.6')
    if os.path.exists(tcl_path) and os.path.exists(tk_path):
        os.environ['TCL_LIBRARY'] = tcl_path
        os.environ['TK_LIBRARY'] = tk_path


class RealTimeOCRApp:
    """
    RealTimeOCRApp 是应用程序的主类，负责初始化和协调各个模块。
    """

    def __init__(self, root):
        """
        初始化 RealTimeOCRApp。

        Args:
            root (tk.Tk): Tkinter 的根窗口。
        """
        self.root = root
        self.running = True

        self.ocr_processor = OCRProcessor()
        self.ui_manager = UIManager(root, self.ocr_processor)
        self.event_manager = EventManager(self.on_exit)

    def on_exit(self):
        """
        程序退出时的处理函数，停止所有线程并销毁窗口。
        """
        print("Hotkey pressed. Initiating shutdown...")
        self.running = False
        self.ocr_processor.stop()
        self.ui_manager.stop()
        self.event_manager.stop()
        self.root.after(0, self.root.destroy)

    def start(self):
        """
        启动 RealTimeOCR 应用程序。
        """
        self.event_manager.start_notification()

        # 启动键盘监听线程
        keyboard_thread = threading.Thread(
            target=self.event_manager.start_keyboard_listener, daemon=True
        )
        keyboard_thread.start()

        # 启动 OCR 线程
        ocr_thread = threading.Thread(target=self.ocr_processor.ocr_thread, daemon=True)
        ocr_thread.start()

        # 启动 UI 更新
        self.ui_manager.start()
        self.root.mainloop()


def main():
    """
    应用程序的入口点。
    初始化 Tkinter 窗口并启动 RealTimeOCRApp。
    """
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass

    root = tk.Tk()
    root.overrideredirect(True)
    root.wm_attributes("-topmost", True)
    root.wm_attributes("-transparentcolor", "white")
    root.attributes("-alpha", 0.8)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")

    app = RealTimeOCRApp(root)
    app.start()


if __name__ == "__main__":
    main()


