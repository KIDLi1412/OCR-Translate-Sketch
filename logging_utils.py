import logging
import multiprocessing
import os
import time
from logging import INFO, FileHandler, Formatter, StreamHandler, getLogger
from logging.handlers import QueueHandler

LOG_DIR = "log"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def get_log_level(level_str: str) -> int:
    """
    将日志级别字符串转换为 logging 级别常量。

    Args:
        level_str (str): 日志级别字符串 (例如, "DEBUG", "INFO", "WARNING")。

    Returns:
        int: 对应的 logging 级别常量。
    """
    return getattr(logging, level_str.upper(), INFO)


def setup_logging(queue: multiprocessing.Queue, log_level: int) -> None:
    """
    配置日志记录, 将日志发送到队列。

    Args:
        queue (multiprocessing.Queue): 用于日志记录的队列。
        log_level (int): 日志级别。
    """
    # 获取根日志记录器
    logger = getLogger()
    logger.setLevel(log_level)

    # 创建队列处理器
    queue_handler = QueueHandler(queue)

    # 为根日志记录器添加队列处理器
    logger.addHandler(queue_handler)


def setup_main_logging(log_level: int) -> multiprocessing.Queue:
    """
    在主进程中配置日志记录。

    Args:
        log_level (int): 日志级别。
    """
    # 创建一个队列
    log_queue = multiprocessing.Queue(-1)

    # 创建流处理器和文件处理器
    stream_handler = StreamHandler()
    file_handler = FileHandler(
        os.path.join(LOG_DIR, f"{time.strftime('%Y%m%d_%H%M%S')}.log"),
        mode="w",
        encoding="utf-8",
    )

    # 创建格式化器
    formatter = Formatter("%(asctime)s - %(processName)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 获取根日志记录器
    logger = getLogger()
    logger.setLevel(log_level)

    # 添加处理器
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return log_queue
