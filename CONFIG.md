# Configuration Instructions

- **TESSERACT_CMD**: Path to the Tesseract executable. Example: C:\Program Files\Tesseract-OCR\tesseract.exe
- **OCR_LANGUAGE**: Language used by Tesseract OCR. Can be 'eng' (English), 'chi_sim' (Simplified Chinese), or 'eng+chi_sim' (both).
- **CONF_THRESHOLD**: Confidence threshold for OCR results. Only text with confidence higher than this value will be displayed.
- **PAR_CONF_THRESHOLD**: Paragraph confidence threshold. Only paragraphs with confidence higher than this value will be displayed.
- **OCR_FPS**: Frame rate for OCR recognition. How many screenshots and text recognitions are performed per second.
- **DEBUG_MODE**: Whether to enable debug mode. In debug mode, all detected text boxes will show borders.
- **STOP_HOTKEY**: Hotkey to stop the program. Example: '<ctrl>+<alt>+c'
- **UI_UPDATE_INTERVAL**: UI update interval near the mouse (milliseconds).
- **HIGHLIGHT_RECT_OUTLINE_COLOR**: Highlight rectangle border color.
- **HIGHLIGHT_RECT_OUTLINE_WIDTH**: Highlight rectangle border width.
- **DEBUG_RECT_OUTLINE_COLOR**: Debug mode rectangle border color.
- **DEBUG_RECT_OUTLINE_WIDTH**: Debug mode rectangle border width.
- **LOG_LEVEL**: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)