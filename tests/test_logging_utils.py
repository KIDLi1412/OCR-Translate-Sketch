"""
This module contains unit tests for the logging utility functions.
It ensures that log level retrieval and logging handler resets work as expected.
"""

import logging

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


@pytest.mark.parametrize(
    "level_str, expected_level",
    [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
        ("debug", logging.DEBUG),  # Case-insensitive test
        ("info", logging.INFO),    # Case-insensitive test
    ],
)
def test_get_log_level_valid_levels(level_str, expected_level):
    """
    Tests `get_log_level` for valid log level strings (case-insensitive).
    """
    assert get_log_level(level_str) == expected_level
