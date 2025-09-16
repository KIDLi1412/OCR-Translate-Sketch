import threading
import tkinter as tk

import pandas as pd
import pytesseract
from PIL import ImageGrab

from config import Config

OCR_EVENT = "<<OCRComplete>>"


class OCRProcessor:
    """
    OCRProcessor 类负责执行屏幕截图的 OCR 识别。
    它在一个单独的线程中运行, 持续捕获屏幕并进行文本识别。
    """

    def __init__(self, root: tk.Tk):
        """
        初始化 OCRProcessor。

        Args:
            root (tk.Tk): Tkinter 的根窗口。
        """
        self.root = root
        self.ocr_data = pd.DataFrame()
        self.running = True
        self.lock = threading.Lock()

    @staticmethod
    def _aggregate_par_info(group: pd.DataFrame) -> pd.Series:
        """
        聚合一个段落分组内的所有单词信息。
        """
        # 按阅读顺序排序并合并文本
        sorted_group = group.sort_values(by=['line_num', 'word_num'])
        merged_text = ' '.join(sorted_group['text'].astype(str))

        # 计算块的边界框
        par_left = group['left'].min()
        par_top = group['top'].min()

        # 计算右边界和下边界
        right_max = (group['left'] + group['width']).max()
        bottom_max = (group['top'] + group['height']).max()

        # 计算块的宽度和高度
        par_width = right_max - par_left
        par_height = bottom_max - par_top

        # 计算平均置信度
        par_conf = group['conf'].mean()

        # 返回一个包含所有信息的Series
        return pd.Series({
            'text': merged_text,
            'left': par_left,
            'top': par_top,
            'width': par_width,
            'height': par_height,
            'conf': par_conf
        })

    @staticmethod
    def merge_ocr_data_to_paragraphs(ocr_df: pd.DataFrame, conf_threshold: int = Config.PAR_CONF_THRESHOLD) -> pd.DataFrame:
        """
        将原始的 OCR DataFrame (单词级别) 合并成段落级别的 DataFrame。

        Args:
            ocr_df (pd.DataFrame): 来自 pytesseract image_to_data 的原始 DataFrame。
            conf_threshold (int): 用于过滤最终段落的置信度阈值。

        Returns:
            pd.DataFrame: 包含合并后段落信息的 DataFrame。
        """
        if ocr_df.empty:
            return pd.DataFrame()

        # 分组并应用合并函数
        merged_pars = ocr_df.groupby(['page_num', 'block_num', 'par_num']).apply(OCRProcessor._aggregate_par_info)

        ocr_pars_df = merged_pars.reset_index()

        # 过滤掉低置信度的段落
        return ocr_pars_df[ocr_pars_df['conf'] > conf_threshold]

    def ocr_thread(self):
        """
        OCR 识别线程的主循环。
        持续捕获屏幕, 使用 Tesseract 进行 OCR 识别, 并存储结果。
        """
        while self.running:
            img = ImageGrab.grab()
            custom_config = r'--oem 1'
            data = pytesseract.image_to_data(
                img,
                lang=Config.OCR_LANGUAGE,
                output_type=pytesseract.Output.DATAFRAME,
                config=custom_config
            )
            # 仅保留带有文本且置信度高于阈值的数据
            ocr_result = data[(data['conf'] > Config.CONF_THRESHOLD) & (data['text'].str.strip() != '')]

            with self.lock:
                self.ocr_data = ocr_result
            # 生成 OCR 完成事件
            self.root.event_generate(OCR_EVENT)

    def stop(self):
        """
        停止 OCR 识别线程。
        """
        self.running = False

    def get_ocr_data(self):
        """
        获取当前的 OCR 识别数据。

        Returns:
            pd.DataFrame: 包含 OCR 识别结果的 DataFrame。
        """
        with self.lock:
            return self.ocr_data.copy()

    def get_merged_ocr_data(self):
        """
        获取合并后的 OCR 识别数据。

        Returns:
            pd.DataFrame: 包含合并后段落信息的 DataFrame。
        """
        with self.lock:
            return self.merge_ocr_data_to_paragraphs(self.ocr_data)
