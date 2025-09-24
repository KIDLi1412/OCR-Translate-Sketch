"""
This module manages the application's user interface, including drawing OCR results
and handling UI updates based on OCR data. It visualizes detected text and provides
debugging functionalities.
"""

import logging
import tkinter as tk
from typing import Optional

import mouse
import pandas as pd

from config import config
from ocr_processor import OCR_EVENT


class UIManager:
    """
    Manages the application's user interface.
    Handles the creation of the Tkinter window, drawing of OCR results, and visualization
    in debug mode. It also manages UI updates and interactions.
    """

    def __init__(self, root: tk.Tk, ocr_data_provider, translator=None):
        """
        Initializes the UIManager.

        Args:
            root (tk.Tk): The root Tkinter window for the application.
            ocr_data_provider: An object that provides OCR data, typically an OCRProcessor instance.
                               This object should have a `get_merged_ocr_data` method.
            translator: Optional translation processor for translating OCR text.
        """
        self.root = root
        self.ocr_data_provider = ocr_data_provider
        self.translator = translator
        self.debug_mode = config.DEBUG_MODE
        self.running = True
        self.ocr_data = pd.DataFrame()
        self.translated_texts: dict = {}  # Cache for translated texts
        self.show_translation = getattr(config, "TRANSLATION_ENABLED", False)

        self.canvas = tk.Canvas(root, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.root.bind(OCR_EVENT, self.on_ocr_complete)

    def on_ocr_complete(self, _event):
        """
        Event handler for when new OCR data is available.
        Retrieves the merged OCR data from the provider and stores it.

        Args:
            _event: The Tkinter event object (not used).
        """
        self.ocr_data = self.ocr_data_provider.get_merged_ocr_data()
        # Clear translated texts cache when new OCR data arrives
        self.translated_texts.clear()

    def get_translated_text(self, original_text: str) -> Optional[str]:
        """
        Get translated text for the given original text.
        Uses cache to avoid repeated translations.

        Args:
            original_text (str): The original text to translate.

        Returns:
            Optional[str]: The translated text if translation is available, None otherwise.
        """
        if not self.show_translation or not self.translator or not original_text.strip():
            return None

        if original_text in self.translated_texts:
            return self.translated_texts[original_text]

        try:
            translated = self.translator.translate_ocr_data(original_text)
            self.translated_texts[original_text] = translated
            return translated
        except Exception as e:
            logging.warning(f"Translation failed for text '{original_text[:50]}...': {e}")
            return None

    def toggle_translation_display(self):
        """
        Toggle the translation display mode.
        """
        self.show_translation = not self.show_translation
        logging.info(f"Translation display toggled: {'ON' if self.show_translation else 'OFF'}")

    def update_ui(self):
        """
        Periodically updates the user interface.
        Clears the canvas, draws bounding boxes and text for OCR results,
        and highlights text under the mouse cursor. Handles debug mode visualization.
        """
        self.canvas.delete("all")
        x, y = mouse.get_position()

        if not self.ocr_data.empty:
            for _index, row in self.ocr_data.iterrows():
                left, top, width, height = row["left"], row["top"], row["width"], row["height"]

                if left <= x <= left + width and top <= y <= top + height:
                    self.canvas.create_rectangle(
                        left,
                        top,
                        left + width,
                        top + height,
                        outline=config.HIGHLIGHT_RECT_OUTLINE_COLOR,
                        width=config.HIGHLIGHT_RECT_OUTLINE_WIDTH,
                    )
                    
                    # Display original text
                    self.canvas.create_text(
                        left, top + height + 10, text=row["text"], fill="red", anchor="nw", font=("Arial", 12, "bold")
                    )
                    
                    # Display translated text if available
                    if self.show_translation:
                        translated_text = self.get_translated_text(row["text"])
                        if translated_text:
                            self.canvas.create_text(
                                left, top + height + 35, text=translated_text, fill="blue", 
                                anchor="nw", font=("Arial", 12, "bold")
                            )
                elif self.debug_mode:
                    self.canvas.create_rectangle(
                        left,
                        top,
                        left + width,
                        top + height,
                        outline=config.DEBUG_RECT_OUTLINE_COLOR,
                        width=config.DEBUG_RECT_OUTLINE_WIDTH,
                    )

        if self.running:
            self.root.after(config.UI_UPDATE_INTERVAL, self.update_ui)
        else:
            self.root.quit()

    def start(self):
        """
        Starts the UI update loop.
        Sets the running flag to True and initiates the first UI update.
        """
        self.running = True
        self.update_ui()

    def stop(self):
        """
        Stops the UI update loop.
        Sets the running flag to False, which will cause the `update_ui` method
        to exit the Tkinter main loop on its next iteration.
        """
        logging.info("Stopping UI update loop...")
        self.running = False
