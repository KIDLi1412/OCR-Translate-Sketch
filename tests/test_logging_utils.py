"""
This module contains unit tests for the logging utility functions.
It ensures that log level retrieval and logging handler resets work as expected.
"""

import logging
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING

import pytest

from logging_utils import get_log_level


@pytest.fixture(autouse=True)
def reset_logging_handlers():
    """
    Pytest fixture to reset logger handlers before and after each test.
    Ensures each test runs with a clean logging configuration.
    """
    loggers = [logging.getLogger()]
    loggers.extend(logging.Logger.manager.loggerDict.values())

    for logger in loggers:
        if isinstance(logger, logging.Logger):
            logger.handlers.clear()
            logger.propagate = True

    yield

    for logger in loggers:
        if isinstance(logger, logging.Logger):
            logger.handlers.clear()
            logger.propagate = True


def test_get_log_level_valid_levels():
    """
    Tests `get_log_level` for valid log level strings.
    Verifies correct conversion to logging module constants.
    """
    assert get_log_level("DEBUG") == DEBUG
    assert get_log_level("INFO") == INFO
    assert get_log_level("WARNING") == WARNING
    assert get_log_level("ERROR") == ERROR
    assert get_log_level("CRITICAL") == CRITICAL


def test_get_log_level_invalid_level():
    """
    Tests `get_log_level` for invalid log level strings.
    Ensures fallback to `logging.INFO` for unrecognized levels.
    """
    assert get_log_level("INVALID") == INFO


def test_get_log_level_case_insensitivity():
    """
    Tests `get_log_level` for case-insensitivity.
    Verifies correct handling of mixed-case log level strings.
    """
    assert get_log_level("debug") == DEBUG
    assert get_log_level("info") == INFO
