import logging
import multiprocessing
import time
import tkinter as tk
from queue import Empty

import pandas as pd
import pytesseract
from PIL import ImageGrab

from config import Config, setup_logging

OCR_EVENT = "<<OCRComplete>>"


def ocr_process(
    data_queue: multiprocessing.Queue,
    running_flag: multiprocessing.Value,
    log_queue: multiprocessing.Queue,
    log_level: int,
):
    """
    OCR 识别进程的主循环。
    持续捕获屏幕, 使用 Tesseract 进行 OCR 识别, 并将结果放入队列。
    """
    setup_logging(log_queue, log_level)
    config = Config()
    TARGET_INTERVAL = 1.0 / config.OCR_FPS

    while running_flag.value:
        start_time = time.perf_counter()

        img = ImageGrab.grab().convert("L")
        custom_config = r"--oem 1"
        data = pytesseract.image_to_data(
            img, lang=config.OCR_LANGUAGE, output_type=pytesseract.Output.DATAFRAME, config=custom_config
        )
        # 仅保留带有文本且置信度高于阈值的数据
        ocr_result = data[(data["conf"] > config.CONF_THRESHOLD) & (data["text"].str.strip() != "")]

        # 清空队列并将新数据放入
        while not data_queue.empty():
            try:
                data_queue.get_nowait()
            except Empty:
                break
        data_queue.put(ocr_result)

        # 计算实际耗时
        actual_interval = time.perf_counter() - start_time

        if config.DEBUG_MODE:
            logging.info(f"OCR识别耗时: {actual_interval:.4f} 秒")  # 使用 logging.info
        # 等待目标间隔时间
        if actual_interval < TARGET_INTERVAL:
            time.sleep(TARGET_INTERVAL - actual_interval)
        else:
            logging.warning(f"OCR识别耗时过长: {actual_interval:.4f} 秒")  # 使用 logging.warning


class OCRProcessor:
    """
    OCRProcessor 类负责执行屏幕截图的 OCR 识别。
    它在一个单独的进程中运行, 持续捕获屏幕并进行文本识别。
    """

    def __init__(self, root: tk.Tk, log_queue: multiprocessing.Queue, log_level: int):
        """
        初始化 OCRProcessor。

        Args:
            root (tk.Tk): Tkinter 的根窗口。
            log_queue (multiprocessing.Queue): 日志队列。
            log_level (int): 日志级别。
        """
        self.root = root
        self.ocr_data = pd.DataFrame()
        self.data_queue = multiprocessing.Queue()
        self.running_flag = multiprocessing.Value("b", True)
        self.process = multiprocessing.Process(
            target=ocr_process, args=(self.data_queue, self.running_flag, log_queue, log_level)
        )
        self.process.daemon = True

    def start(self):
        """
        启动 OCR 识别进程。
        """
        self.process.start()
        self.root.after(100, self.check_queue)

    def check_queue(self):
        """
        检查队列中是否有新的 OCR 数据。
        """
        try:
            ocr_result = self.data_queue.get_nowait()
            if not ocr_result.equals(self.ocr_data):
                self.ocr_data = ocr_result
                self.root.event_generate(OCR_EVENT)
        except Empty:
            pass
        finally:
            if self.running_flag.value:
                self.root.after(100, self.check_queue)

    @staticmethod
    def _aggregate_par_info(group: pd.DataFrame) -> pd.Series:
        """
        聚合一个段落分组内的所有单词信息。
        """
        # 按阅读顺序排序并合并文本
        sorted_group = group.sort_values(by=["line_num", "word_num"])
        merged_text = " ".join(sorted_group["text"].astype(str))

        # 计算块的边界框
        par_left = group["left"].min()
        par_top = group["top"].min()

        # 计算右边界和下边界
        right_max = (group["left"] + group["width"]).max()
        bottom_max = (group["top"] + group["height"]).max()

        # 计算块的宽度和高度
        par_width = right_max - par_left
        par_height = bottom_max - par_top

        # 计算平均置信度
        par_conf = group["conf"].mean()

        # 返回一个包含所有信息的Series
        return pd.Series(
            {
                "text": merged_text,
                "left": par_left,
                "top": par_top,
                "width": par_width,
                "height": par_height,
                "conf": par_conf,
            }
        )

    @staticmethod
    def merge_ocr_data_to_paragraphs(ocr_df: pd.DataFrame) -> pd.DataFrame:
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
        merged_pars = ocr_df.groupby(["page_num", "block_num", "par_num"]).apply(
            OCRProcessor._aggregate_par_info, include_groups=False
        )

        ocr_pars_df = merged_pars.reset_index()

        # 过滤掉低置信度的段落
        return ocr_pars_df[ocr_pars_df["conf"] > Config().PAR_CONF_THRESHOLD]

    def stop(self):
        """
        停止 OCR 识别进程。
        """
        logging.info("停止 OCR 识别进程...")  # 使用 logging.info
        self.running_flag.value = False
        self.process.join(timeout=1)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join()
            logging.warning("OCR 进程被强制终止。")  # 使用 logging.warning

    def get_ocr_data(self) -> pd.DataFrame:
        """
        获取当前的 OCR 识别数据。

        Returns:
            pd.DataFrame: 包含 OCR 识别结果的 DataFrame。
        """
        return self.ocr_data.copy()

    def get_merged_ocr_data(self) -> pd.DataFrame:
        """
        获取合并后的 OCR 识别数据。

        Returns:
            pd.DataFrame: 包含合并后段落信息的 DataFrame。
        """
        return self.merge_ocr_data_to_paragraphs(self.ocr_data)
