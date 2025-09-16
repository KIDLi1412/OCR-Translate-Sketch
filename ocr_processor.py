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

        if self.ocr_data.empty:
            return pd.DataFrame()
        # 定义合并函数
        def aggregate_block_info(group):
            # 按阅读顺序排序并合并文本
            sorted_group = group.sort_values(by=['line_num', 'word_num'])
            merged_text = ' '.join(sorted_group['text'].astype(str))
            
            # 计算块的边界框
            block_left = group['left'].min()
            block_top = group['top'].min()
            
            # 计算右边界和下边界
            right_max = (group['left'] + group['width']).max()
            bottom_max = (group['top'] + group['height']).max()
            
            # 计算块的宽度和高度
            block_width = right_max - block_left
            block_height = bottom_max - block_top

            block_conf = group['conf'].mean()
            
            # 返回一个包含所有信息的Series
            return pd.Series({
                'text': merged_text,
                'left': block_left,
                'top': block_top,
                'width': block_width,
                'height': block_height,
                'conf': block_conf
            })

        # 分组并应用合并函数
        merged_blocks = self.ocr_data.groupby(['page_num', 'block_num', 'par_num']).apply(aggregate_block_info)
        ocr_blocks_df = merged_blocks.reset_index()
        ocr_blocks_df = ocr_blocks_df[ocr_blocks_df['conf'] > 50]

        ocr_blocks_df.to_csv('merge.csv', index=False)
        return ocr_blocks_df
