import pandas as pd
import pytesseract
from PIL import ImageGrab

from config import Config


class OCRProcessor:
    """
    OCRProcessor 类负责执行屏幕截图的 OCR 识别。
    它在一个单独的线程中运行，持续捕获屏幕并进行文本识别。
    """

    def __init__(self):
        """
        初始化 OCRProcessor。
        """
        self.ocr_data = pd.DataFrame()
        self.running = True

    def ocr_thread(self):
        """
        OCR 识别线程的主循环。
        持续捕获屏幕，使用 Tesseract 进行 OCR 识别，并存储结果。
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
            self.ocr_data = data[(data['conf'] > Config.CONF_THRESHOLD) & (data['text'].str.strip() != '')]

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
        return self.ocr_data