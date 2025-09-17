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

    def start_tray_icon(self):
        """
        设置任务栏图标和菜单。
        """
        image = Image.open("icon.png")
        menu = (pystray.MenuItem('退出', self.on_exit_callback),)
        self.icon = pystray.Icon("OCR-Translate-Sketch", image, "OCR-Translate-Sketch", menu)
        self.icon.run_detached()

    def start_keyboard_listener(self):
        """
        启动键盘监听器, 监听停止热键。
        """
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
        if self.listener:
            self.listener.stop()
        if self.icon:
            self.icon.stop()
