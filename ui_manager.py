import logging  # 导入 logging 模块
import tkinter as tk

import mouse
import pandas as pd

from config import Config
from ocr_processor import OCR_EVENT


class UIManager:
    """
    UIManager 类负责管理应用程序的用户界面。
    它处理 Tkinter 窗口的创建、OCR 结果的绘制以及调试模式下的可视化。
    """

    def __init__(self, root: tk.Tk, ocr_data_provider):
        """
        初始化 UIManager。

        Args:
            root (tk.Tk): Tkinter 的根窗口。
            ocr_data_provider: 提供 OCR 数据的对象, 通常是 OCRProcessor 实例。
        """
        self.root = root
        self.ocr_data_provider = ocr_data_provider
        self.debug_mode = Config().DEBUG_MODE
        self.running = True
        self.ocr_data = pd.DataFrame()

        self.canvas = tk.Canvas(root, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.root.bind(OCR_EVENT, self.on_ocr_complete)

    def on_ocr_complete(self, _event):
        """
        处理 OCR 完成事件, 更新 OCR 数据。
        """
        self.ocr_data = self.ocr_data_provider.get_merged_ocr_data()

    def update_ui(self):
        """
        更新用户界面, 绘制 OCR 识别结果。
        """
        self.canvas.delete("all")
        x, y = mouse.get_position()

        if not self.ocr_data.empty:
            # 绘制 OCR 识别结果
            for _index, row in self.ocr_data.iterrows():
                left, top, width, height = row["left"], row["top"], row["width"], row["height"]

                if left <= x <= left + width and top <= y <= top + height:
                    self.canvas.create_rectangle(
                        left,
                        top,
                        left + width,
                        top + height,
                        outline=Config().HIGHLIGHT_RECT_OUTLINE_COLOR,
                        width=Config().HIGHLIGHT_RECT_OUTLINE_WIDTH,
                    )
                    self.canvas.create_text(
                        left, top + height + 10, text=row["text"], fill="red", anchor="nw", font=("Arial", 12, "bold")
                    )
                elif self.debug_mode:
                    self.canvas.create_rectangle(
                        left,
                        top,
                        left + width,
                        top + height,
                        outline=Config().DEBUG_RECT_OUTLINE_COLOR,
                        width=Config().DEBUG_RECT_OUTLINE_WIDTH,
                    )

        if self.running:
            self.root.after(Config().UI_UPDATE_INTERVAL, self.update_ui)
        else:
            self.root.quit()

    def start(self):
        """
        启动 UI 更新循环。
        """
        self.running = True
        self.update_ui()

    def stop(self):
        """
        停止 UI 更新循环。
        """
        logging.info("停止 UI 更新循环...")  # 使用 logging.info
        self.running = False
