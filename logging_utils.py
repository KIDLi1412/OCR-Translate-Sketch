"""
This module provides utilities for setting up and managing logging across multiple processes
using a multiprocessing queue. It supports configuring log levels, console output, and file output.
"""

import logging
import multiprocessing
import os
import time
from logging import INFO, FileHandler, Formatter, StreamHandler, getLogger
from logging.handlers import QueueHandler

# Directory for storing log files.
LOG_DIR = "log"

# Create the log directory if it does not exist.
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def get_log_level(level_str: str) -> int:
    """
    Converts a log level string to a logging level constant.

    Args:
        level_str (str): The log level string (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").

    Returns:
        int: The corresponding logging level constant. Defaults to INFO if the string is not recognized.
    """
    return getattr(logging, level_str.upper(), INFO)


def setup_logging(queue: multiprocessing.Queue, log_level: int) -> None:
    """
    Configures logging for worker processes to send log records to a multiprocessing queue.
    This allows multiple processes to log to the same set of handlers in the main process.

    Args:
        queue (multiprocessing.Queue): The multiprocessing queue to which log records will be sent.
        log_level (int): The minimum logging level for messages to be processed (e.g., logging.INFO).
    """
    logger = getLogger()
    logger.setLevel(log_level)

    # All log messages from this process will be put into the queue.
    queue_handler = QueueHandler(queue)
    logger.addHandler(queue_handler)


def setup_main_logging(log_level: int) -> multiprocessing.Queue:
    """
    Configures logging in the main process, setting up console and file handlers,
    and returns a multiprocessing queue for receiving log records from other processes.

    Args:
        log_level (int): The minimum logging level for messages to be processed (e.g., logging.INFO).

    Returns:
        multiprocessing.Queue: A queue to which worker processes can send their log records.
    """
    # Create a multiprocessing queue for inter-process logging communication.
    log_queue = multiprocessing.Queue(-1)

    # Configure console output.
    stream_handler = StreamHandler()
    # Configure file output with a unique timestamped filename.
    file_handler = FileHandler(
        os.path.join(LOG_DIR, f"{time.strftime('%Y%m%d_%H%M%S')}.log"),
        mode="w",
        encoding="utf-8",
    )

    # Define log message format.
    formatter = Formatter("%(asctime)s - %(processName)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger = getLogger()
    logger.setLevel(log_level)

    # Add handlers to the root logger to display messages on console and write to file.
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return log_queue
