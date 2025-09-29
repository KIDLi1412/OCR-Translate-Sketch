"""
This module provides functionalities for OCR (Optical Character Recognition) processing.
It includes a multiprocessing-based OCR engine that captures screenshots, performs text recognition,
and aggregates results. It also handles logging and inter-process communication for OCR data.
"""

import logging
import multiprocessing
import time
import tkinter as tk
from queue import Empty

import pandas as pd
import pytesseract
from PIL import ImageGrab

from config import config
from logging_utils import setup_logging

# Custom event name for OCR completion, used to notify the UI thread.
OCR_EVENT = "<<OCRComplete>>"


def ocr_process(
    data_queue: multiprocessing.Queue,
    running_flag: multiprocessing.Value,
    log_queue: multiprocessing.Queue,
    log_level: int,
):
    """
    The main function for the OCR recognition process, designed to run in a separate process.
    It continuously captures screenshots, performs OCR using Tesseract, and places the results
    into a shared queue for other processes to consume.

    Args:
        data_queue (multiprocessing.Queue): A queue to put the OCR results into.
        running_flag (multiprocessing.Value): A shared flag to control the execution of the OCR loop.
        log_queue (multiprocessing.Queue): A queue for logging messages from this process.
        log_level (int): The logging level for this process.
    """
    setup_logging(log_queue, log_level)
    TARGET_INTERVAL = 1.0 / config.OCR_FPS

    while running_flag.value:
        start_time = time.perf_counter()

        # Capture the screen and convert it to grayscale.
        img = ImageGrab.grab().convert("L")
        # Custom Tesseract configuration.
        custom_config = r"--oem 1"
        # Perform OCR and get detailed word-level data.
        data = pytesseract.image_to_data(
            img, lang=config.OCR_LANGUAGE, output_type=pytesseract.Output.DATAFRAME, config=custom_config
        )
        # Filter OCR results based on confidence threshold and non-empty text.
        ocr_result = data[(data["conf"] > config.CONF_THRESHOLD) & (data["text"].str.strip() != "")]

        # Clear the queue to ensure only the latest results are available.
        while not data_queue.empty():
            try:
                data_queue.get_nowait()
            except Empty:
                break
        # Put the new OCR results into the queue.
        data_queue.put(ocr_result)

        actual_interval = time.perf_counter() - start_time

        # Log OCR recognition time if debug mode is enabled.
        if config.DEBUG_MODE:
            logging.info(f"OCR recognition time: {actual_interval:.4f} seconds")
        # Pause to maintain the target frame rate.
        if actual_interval < TARGET_INTERVAL:
            time.sleep(TARGET_INTERVAL - actual_interval)
        else:
            # Log a warning if OCR took longer than the target interval.
            logging.warning(f"OCR recognition took too long: {actual_interval:.4f} seconds")


class OCRProcessor:
    """
    Manages the OCR recognition process in a separate multiprocessing.Process.
    Handles starting, stopping, and retrieving OCR results.
    """

    def __init__(self, root: tk.Tk, log_queue: multiprocessing.Queue, log_level: int):
        """
        Initializes the OCRProcessor.

        Args:
            root (tk.Tk): The root Tkinter window for event generation.
            log_queue (multiprocessing.Queue): Queue for sending log messages to the main process.
            log_level (int): The logging level for the OCR process.
        """
        self.root = root
        self.ocr_data = pd.DataFrame()
        self.data_queue = multiprocessing.Queue()
        self.running_flag = multiprocessing.Value("b", True)
        # Initialize the OCR process as a daemon.
        self.process = multiprocessing.Process(
            target=ocr_process, args=(self.data_queue, self.running_flag, log_queue, log_level)
        )
        self.process.daemon = True

    def start(self):
        """
        Starts the OCR recognition process and initiates periodic checks for new OCR data.
        """
        self.process.start()
        self.root.after(100, self.check_queue)

    def check_queue(self):
        """
        Periodically checks `data_queue` for new OCR results.
        Updates `self.ocr_data` and generates `OCR_EVENT` if new data is available and different.
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
        Aggregates word-level OCR information within a paragraph group into a single paragraph entry.
        Merges text, calculates a combined bounding box, and averages confidence.

        Args:
            group (pd.DataFrame): DataFrame of word-level OCR results for a single paragraph.

        Returns:
            pd.Series: Aggregated paragraph information.
        """
        sorted_group = group.sort_values(by=["line_num", "word_num"])
        merged_text = " ".join(sorted_group["text"].astype(str))

        par_left = group["left"].min()
        par_top = group["top"].min()

        right_max = (group["left"] + group["width"]).max()
        bottom_max = (group["top"] + group["height"]).max()

        par_width = right_max - par_left
        par_height = bottom_max - par_top

        par_conf = group["conf"].mean()

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
        Transforms raw word-level OCR data into paragraph-level data.
        Groups words into paragraphs and aggregates their information.

        Args:
            ocr_df (pd.DataFrame): Raw DataFrame from pytesseract image_to_data.

        Returns:
            pd.DataFrame: DataFrame of aggregated paragraph information.
        """
        if ocr_df.empty:
            return pd.DataFrame()

        merged_pars = ocr_df.groupby(["page_num", "block_num", "par_num"]).apply(
            OCRProcessor._aggregate_par_info, include_groups=False
        )

        ocr_pars_df = merged_pars.reset_index()

        # Filter paragraphs by minimum confidence threshold.
        return ocr_pars_df[ocr_pars_df["conf"] > config.PAR_CONF_THRESHOLD]

    def stop(self):
        """
        Stops the OCR recognition process.
        Signals the child process to terminate and waits for it to join.
        Forcefully terminates if the process does not stop gracefully.
        """
        logging.info("Stopping OCR recognition process...")
        self.running_flag.value = False
        self.process.join(timeout=1)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join()
            logging.warning("OCR process was forcibly terminated.")

    def get_ocr_data(self) -> pd.DataFrame:
        """
        Retrieves the most recently processed raw word-level OCR data.

        Returns:
            pd.DataFrame: A copy of the DataFrame containing raw OCR results.
        """
        return self.ocr_data.copy()

    def get_merged_ocr_data(self) -> pd.DataFrame:
        """
        Retrieves the most recently processed OCR data, merged into paragraph-level entries.

        Returns:
            pd.DataFrame: DataFrame containing information about the merged paragraphs.
        """
        return self.merge_ocr_data_to_paragraphs(self.ocr_data)
