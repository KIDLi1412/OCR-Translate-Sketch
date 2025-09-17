# 配置说明

- **TESSERACT_CMD**: Tesseract 可执行文件的路径。示例: C:\Program Files\Tesseract-OCR\tesseract.exe
- **OCR_LANGUAGE**: Tesseract OCR 使用的语言。可以是 'eng' (英语), 'chi_sim' (简体中文), 或 'eng+chi_sim' (两者)。
- **CONF_THRESHOLD**: OCR 结果的置信度阈值。只有置信度高于此值的文本才会被显示。
- **PAR_CONF_THRESHOLD**: 段落置信度阈值。只有段落置信度高于此值的段落才会被显示。
- **OCR_FPS**: OCR 识别的帧率。即每秒钟进行多少次屏幕截图和文字识别。
- **DEBUG_MODE**: 是否启用调试模式。在调试模式下, 所有检测到的文本框都会显示边框。
- **STOP_HOTKEY**: 停止程序的快捷键。示例: '<ctrl>+<alt>+c'
- **UI_UPDATE_INTERVAL**: 鼠标附近 UI 更新间隔 (毫秒)。
- **HIGHLIGHT_RECT_OUTLINE_COLOR**: 高亮矩形边框颜色。
- **HIGHLIGHT_RECT_OUTLINE_WIDTH**: 高亮矩形边框宽度。
- **DEBUG_RECT_OUTLINE_COLOR**: 调试模式下矩形边框颜色。
- **DEBUG_RECT_OUTLINE_WIDTH**: 调试模式下矩形边框宽度。
- **LOG_LEVEL**: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)