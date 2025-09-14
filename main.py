import ctypes
import os
import sys
import threading
import tkinter as tk

import mouse
import pandas as pd
import pystray
import pytesseract
from PIL import Image, ImageGrab
from pynput import keyboard
from win10toast_persist import ToastNotifier

from config import Config

if "VIRTUAL_ENV" in os.environ:
    base_python_path = sys.base_prefix
    tcl_path = os.path.join(base_python_path, 'tcl', 'tcl8.6')
    tk_path = os.path.join(base_python_path, 'tcl', 'tk8.6')
    if os.path.exists(tcl_path) and os.path.exists(tk_path):
        os.environ['TCL_LIBRARY'] = tcl_path
        os.environ['TK_LIBRARY'] = tk_path


class RealTimeOCR:

    def __init__(self, root):
        self.root = root
        self.running = True
        self.ocr_data = pd.DataFrame()
        self.debug_mode = Config.DEBUG_MODE
        self.listener = None

        self.canvas = tk.Canvas(root, bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.setup_tray_icon()

    def setup_tray_icon(self):
        """
        设置任务栏图标和菜单。
        """
        image = Image.open("icon.png")
        menu = (pystray.MenuItem('退出', self.on_exit),)
        self.icon = pystray.Icon("RealTimeOCR", image, "RealTimeOCR", menu)
        self.icon.run_detached()

    def ocr_thread(self):
        while self.running:
            img = ImageGrab.grab()
            custom_config = r'--oem 1'
            data = pytesseract.image_to_data(
                img,
                lang=Config.OCR_LANGUAGE,
                output_type=pytesseract.Output.DATAFRAME,
                config=custom_config
            )
            self.ocr_data = data[(data['conf'] > Config.CONF_THRESHOLD) & (data['text'].str.strip() != '')]

    def on_exit(self):
        """
        程序退出时的处理函数，停止所有线程并销毁窗口。
        """
        print("Hotkey pressed. Initiating shutdown...")
        self.running = False
        if self.listener:
            self.listener.stop()
        if self.icon:
            self.icon.stop()
        self.root.after(0, self.root.destroy)

    def start_keyboard_listener(self):
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(Config.STOP_HOTKEY),
            self.on_exit
        )

        def on_press(key):
            hotkey.press(listener.canonical(key))

        def on_release(key):
            hotkey.release(listener.canonical(key))

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            self.listener = listener
            listener.join()

    def update_ui(self):
        self.canvas.delete("all")
        x, y = mouse.get_position()

        for _index, row in self.ocr_data.iterrows():
            left, top, width, height = row['left'], row['top'], row['width'], row['height']

            if left <= x <= left + width and top <= y <= top + height:
                self.canvas.create_rectangle(left, top, left + width, top + height, outline='red', width=2)
                self.canvas.create_text(
                    left,
                    top + height + 10,
                    text=row['text'],
                    fill='red',
                    anchor='nw',
                    font=("Arial", 12, "bold")
                )
            elif self.debug_mode:
                self.canvas.create_rectangle(left, top, left + width, top + height, outline='blue', width=1)

        if self.running:
            self.root.after(100, self.update_ui)
        else:
            self.root.quit()

    def start(self):
        show_notification()
        keyboard_thread = threading.Thread(target=self.start_keyboard_listener, daemon=True)
        keyboard_thread.start()

        ocr_proc = threading.Thread(target=self.ocr_thread, daemon=True)
        ocr_proc.start()

        self.update_ui()
        self.root.mainloop()


def show_notification():
    toaster = ToastNotifier()
    toaster.show_toast("RealTimeOCR", "程序已启动，按 " + Config.STOP_HOTKEY + " 停止", duration=5, threaded=True)

def main():
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

    app = RealTimeOCR(root)
    app.start()


if __name__ == "__main__":
    main()
