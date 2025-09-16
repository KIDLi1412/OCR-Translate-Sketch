"""
config.py

此文件包含 OCR-Translate-Sketch 应用程序的所有配置参数。
通过修改此文件, 可以调整应用程序的行为, 而无需更改主程序逻辑。
"""

class Config:
    """
    应用程序配置类。
    """
    # Tesseract 可执行文件的路径。
    # 示例: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSERACT_CMD: str = r'D:\Program Files\Tesseract-OCR\tesseract.exe'

    # Tesseract OCR 使用的语言。
    # 可以是 'eng' (英语), 'chi_sim' (简体中文), 或 'eng+chi_sim' (两者)。
    OCR_LANGUAGE: str = 'eng'

    # OCR 结果的置信度阈值。
    # 只有置信度高于此值的文本才会被显示。
    CONF_THRESHOLD: int = 25

    PAR_CONF_THRESHOLD: int = 50

    # OCR 识别的帧率。
    # 即每秒钟进行多少次屏幕截图和文字识别。
    OCR_FPS: int = 2

    # 是否启用调试模式。
    # 在调试模式下, 所有检测到的文本框都会显示蓝色边框。
    DEBUG_MODE: bool = True

    # 停止程序的快捷键。
    # 示例: '<ctrl>+c'
    STOP_HOTKEY: str = '<ctrl>+c'

    # UI 更新间隔 (毫秒)。
    UI_UPDATE_INTERVAL: int = 100

    # 高亮矩形边框颜色和宽度。
    HIGHLIGHT_RECT_OUTLINE_COLOR: str = 'red'
    HIGHLIGHT_RECT_OUTLINE_WIDTH: int = 2

    # 调试模式下矩形边框颜色和宽度。
    DEBUG_RECT_OUTLINE_COLOR: str = 'blue'
    DEBUG_RECT_OUTLINE_WIDTH: int = 1

