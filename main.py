import os
import sys
import tkinter as tk
import threading
from PIL import ImageGrab
import pytesseract
import pandas as pd
from pynput import keyboard
from win10toast_persist import ToastNotifier
import ctypes

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
        self.debug_mode = True
        self.pressed_keys = set()

        self.canvas = tk.Canvas(root, bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def ocr_thread(self):
        while self.running:
            img = ImageGrab.grab()
            data = pytesseract.image_to_data(img, lang='eng+chi_sim', output_type=pytesseract.Output.DATAFRAME)
            self.ocr_data = data[(data['conf'] > 25) & (data['text'].str.strip() != '')]

    def on_press(self, key):
        if key in {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}:
            self.pressed_keys.add(key)
        elif isinstance(key, keyboard.KeyCode) and key.char == 'c':
            if any(k in self.pressed_keys for k in {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}):
                self.running = False
                return False

    def on_release(self, key):
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)

    def start_keyboard_listener(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def update_ui(self):
        self.canvas.delete("all")
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()

        for index, row in self.ocr_data.iterrows():
            left, top, width, height = row['left'], row['top'], row['width'], row['height']

            if left <= x <= left + width and top <= y <= top + height:
                self.canvas.create_rectangle(left, top, left + width, top + height, outline='red', width=2)
                self.canvas.create_text(left, top + height + 10, text=row['text'], fill='red', anchor='nw', font=("Arial", 12, "bold"))
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
    toaster.show_toast("RealTimeOCR", "程序已启动，按 Ctrl+C 停止", duration=5, threaded=True)

def main():
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
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
