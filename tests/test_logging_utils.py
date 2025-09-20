import logging
import multiprocessing
import os
import shutil
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from unittest.mock import MagicMock, patch, create_autospec

import pytest

from logging_utils import get_log_level, setup_logging, setup_main_logging, LOG_DIR


@pytest.fixture(autouse=True)
def cleanup_log_dir():
    """
    Pytest fixture, 用于在每次测试前后清理日志目录。
    """
    if os.path.exists(LOG_DIR):
        shutil.rmtree(LOG_DIR)
    os.makedirs(LOG_DIR)
    yield
    if os.path.exists(LOG_DIR):
        shutil.rmtree(LOG_DIR)


@pytest.fixture(autouse=True)
def reset_logging_handlers():
    """
    Pytest fixture, 用于在每次测试前后重置日志记录器的处理程序，以防止测试间的干扰。
    """
    yield
    # Remove all handlers from the root logger
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    # Reset the logging level
    logging.root.setLevel(logging.WARNING)


def test_get_log_level_valid_levels():
    """
    测试 get_log_level 函数，验证标准日志级别字符串能正确转换为对应的 logging 模块常量。
    """
    assert get_log_level("DEBUG") == DEBUG
    assert get_log_level("INFO") == INFO
    assert get_log_level("WARNING") == WARNING
    assert get_log_level("ERROR") == ERROR
    assert get_log_level("CRITICAL") == CRITICAL


def test_get_log_level_invalid_level():
    """
    测试 get_log_level 函数，验证输入无效级别字符串时是否回退到默认值 logging.INFO。
    """
    assert get_log_level("INVALID") == INFO
    assert get_log_level("UNKNOWN") == INFO


def test_get_log_level_case_insensitivity():
    """
    测试 get_log_level 函数，验证输入小写级别字符串时是否能正确处理。
    """
    assert get_log_level("debug") == DEBUG
    assert get_log_level("info") == INFO
    assert get_log_level("warning") == WARNING
