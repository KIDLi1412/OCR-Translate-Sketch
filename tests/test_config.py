"""
This module contains unit tests for the `_Config` class and its related functionalities
within the `config` module. It covers configuration loading, file handling,
data type conversions, and dynamic updates via file watching.
"""

import os
import tempfile
import pytest
import yaml

from config import CONFIG_FILE, ConfigFileEventHandler, _Config


@pytest.fixture
def config_setup_teardown(mocker): # Added mocker fixture
    """
    Sets up the environment before each test method execution.
    Creates a temporary directory and file to simulate config.yaml.
    Mocks the `CONFIG_FILE` path to point to this temporary file.
    """
    test_dir = tempfile.mkdtemp()
    test_config_path = os.path.join(test_dir, CONFIG_FILE)

    # patcher = mock.patch('config.CONFIG_FILE', test_config_path) # Replaced with mocker.patch
    mocker.patch('config.CONFIG_FILE', test_config_path)
    # patcher.start() # Not needed with mocker

    yield test_config_path, test_dir  # Provide the path to the test config file and directory

    """
    Cleans up the environment after each test method execution.
    Deletes temporary directories and files and stops the mock patcher.
    """
    patcher.stop()
    if os.path.exists(test_config_path):
        os.remove(test_config_path)
    if os.path.exists(test_dir):
        os.rmdir(test_dir)


def _write_config_file(test_config_path, content: dict):
    """
    Helper method: Writes dictionary content to the simulated configuration file.

    Args:
        test_config_path (str): The path to the temporary configuration file.
        content (dict): A dictionary representing the configuration data to write.
    """
    with open(test_config_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(content, f, allow_unicode=True)


def test_load_config_success(config_setup_teardown):
    """
    Tests successful configuration loading from a valid YAML file.
    Verifies that all defined configuration items, including an unknown one,
    are loaded correctly and have the expected data types.
    """
    test_config_path, _ = config_setup_teardown
    test_data = {
        "TESSERACT_CMD": "tesseract_path",
        "OCR_LANGUAGE": "eng",
        "CONF_THRESHOLD": 70,
        "PAR_CONF_THRESHOLD": 80,
        "OCR_FPS": 1.5,
        "DEBUG_MODE": True,
        "STOP_HOTKEY": "ctrl+alt+s",
        "UI_UPDATE_INTERVAL": 100,
        "HIGHLIGHT_RECT_OUTLINE_COLOR": "#FF0000",
        "HIGHLIGHT_RECT_OUTLINE_WIDTH": 2,
        "DEBUG_RECT_OUTLINE_COLOR": "#00FF00",
        "DEBUG_RECT_OUTLINE_WIDTH": 1,
        "LOG_LEVEL": "INFO",
        "UNKNOWN_KEY": "unknown_value"
    }
    _write_config_file(test_config_path, test_data)

    config_instance = _Config()

    assert config_instance.TESSERACT_CMD == "tesseract_path"
    assert config_instance.OCR_LANGUAGE == "eng"
    assert config_instance.CONF_THRESHOLD == 70
    assert config_instance.PAR_CONF_THRESHOLD == 80
    assert config_instance.OCR_FPS == 1.5
    assert config_instance.DEBUG_MODE is True
    assert config_instance.STOP_HOTKEY == "ctrl+alt+s"
    assert config_instance.UI_UPDATE_INTERVAL == 100
    assert config_instance.HIGHLIGHT_RECT_OUTLINE_COLOR == "#FF0000"
    assert config_instance.HIGHLIGHT_RECT_OUTLINE_WIDTH == 2
    assert config_instance.DEBUG_RECT_OUTLINE_COLOR == "#00FF00"
    assert config_instance.DEBUG_RECT_OUTLINE_WIDTH == 1
    assert config_instance.LOG_LEVEL == "INFO"
    assert config_instance.UNKNOWN_KEY == "unknown_value"


def test_load_config_file_not_found(config_setup_teardown, caplog):
    """
    Tests handling when the configuration file is not found.
    Ensures that a warning is logged when the file is absent.
    """
    test_config_path, _ = config_setup_teardown
    if os.path.exists(test_config_path):
        os.remove(test_config_path)

    with caplog.at_level('WARNING'):
        _Config()
    assert f"Configuration file {test_config_path} not found." in caplog.text


def test_load_config_empty_file(config_setup_teardown, caplog):
    """
    Tests handling when the configuration file is empty.
    Ensures that an INFO message is logged indicating an empty or invalid file.
    """
    test_config_path, test_dir = config_setup_teardown
    _write_config_file(test_config_path, {})

    with caplog.at_level('INFO'):
        _Config()
    assert f"Configuration file {test_config_path} is empty or invalid." in caplog.text


def test_load_config_invalid_yaml(config_setup_teardown, caplog):
    """
    Tests handling when the configuration file has an incorrect YAML format.
    Ensures that an ERROR message is logged when the YAML is malformed.
    """
    test_config_path, _ = config_setup_teardown
    with open(test_config_path, 'w', encoding='utf-8') as f:
        f.write("invalid yaml: - ")

    with caplog.at_level('ERROR'):
        _Config()
    assert f"Error loading configuration file {test_config_path}" in caplog.text


@pytest.mark.parametrize(
    "key, value, expected_type, expected_value",
    [
        ("CONF_THRESHOLD", "90", int, 90),
        ("OCR_FPS", "2.5", float, 2.5),
        ("DEBUG_MODE", "False", bool, False),
        ("DEBUG_MODE", "true", bool, True),  # Add case-insensitive test for bool
        ("LOG_LEVEL", "DEBUG", str, "DEBUG"),
    ],
)
def test_data_type_conversion(config_setup_teardown, key, value, expected_type, expected_value):
    """
    Tests the correctness of data type conversion for various configuration items.
    """
    test_config_path, _ = config_setup_teardown
    _write_config_file(test_config_path, {key: value})

    config_instance = _Config()

    actual_value = getattr(config_instance, key)
    assert actual_value == expected_value
    assert isinstance(actual_value, expected_type)


def test_set_attribute_type_conversion_warning(config_setup_teardown, caplog):
    """
    Tests that a warning is logged when a value cannot be converted to its expected type,
    and the original value is used instead.
    """
    test_config_path, _ = config_setup_teardown
    test_data = {"CONF_THRESHOLD": "not-an-int"}
    _write_config_file(test_config_path, test_data)

    with caplog.at_level('WARNING'):
        config_instance = _Config()

    assert "could not be converted to int" in caplog.text
    assert config_instance.CONF_THRESHOLD == "not-an-int"  # Confirm fallback to original value


def test_update_config_file(config_setup_teardown):
    """
    Tests the functionality of the update_config_file method.
    Verifies that instance attributes are correctly updated and that changes
    are written back to the configuration file.
    """
    test_config_path, _ = config_setup_teardown
    initial_data = {
        "CONF_THRESHOLD": 70,
        "DEBUG_MODE": True
    }
    _write_config_file(test_config_path, initial_data)

    config_instance = _Config()

    new_config = {
        "CONF_THRESHOLD": 85,
        "DEBUG_MODE": False,
        "NEW_SETTING": "test_value"
    }
    config_instance.update_config_file(new_config)

    assert config_instance.CONF_THRESHOLD == 85
    assert config_instance.DEBUG_MODE is False
    assert config_instance.NEW_SETTING == "test_value"

    with open(test_config_path, encoding='utf-8') as f:
        updated_data = yaml.safe_load(f)

    assert updated_data["CONF_THRESHOLD"] == 85
    assert updated_data["DEBUG_MODE"] is False
    assert updated_data["NEW_SETTING"] == "test_value"


# @mocker.patch('config.Observer') # Replaced mock.patch with mocker.patch
def test_file_monitoring(config_setup_teardown, mocker): # Removed MockObserver from arguments
    """
    Tests the file monitoring function.
    Verifies that the `on_modified` event correctly triggers configuration reloading
    when the configuration file is changed.
    """
    # Patch config.Observer inside the function
    mocker.patch('config.Observer')

    test_config_path, _ = config_setup_teardown
    initial_data = {
        "CONF_THRESHOLD": 70
    }
    _write_config_file(test_config_path, initial_data)

    config_instance = _Config()
    assert config_instance.CONF_THRESHOLD == 70

    event_handler = ConfigFileEventHandler(config_instance)
    # mock_event = mock.Mock() # Replaced with mocker.Mock()
    mock_event = mocker.Mock()
    mock_event.is_directory = False
    mock_event.src_path = test_config_path

    updated_data = {
        "CONF_THRESHOLD": 99
    }
    _write_config_file(test_config_path, updated_data)

    event_handler.on_modified(mock_event)

    assert config_instance.CONF_THRESHOLD == 99
