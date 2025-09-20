"""
This module contains unit tests for the `_Config` class and its related functionalities
within the `config` module. It covers configuration loading, file handling,
data type conversions, and dynamic updates via file watching.
"""

import os
import tempfile
import unittest
from unittest import mock

import yaml

from config import CONFIG_FILE, ConfigFileEventHandler, _Config


class TestConfig(unittest.TestCase):
    """
    Tests the _Config class and its related functionalities.
    This includes testing configuration loading, file not found scenarios,
    empty or invalid YAML files, data type conversions, and dynamic updates
    via the file watcher.
    """

    def setUp(self):
        """
        Sets up the environment before each test method execution.
        Creates a temporary directory and file to simulate config.yaml.
        Mocks the `CONFIG_FILE` path to point to this temporary file.
        """
        self.test_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.test_dir, CONFIG_FILE)

        self.original_config_file = CONFIG_FILE
        self.patcher = mock.patch('config.CONFIG_FILE', self.test_config_path)
        self.patcher.start()

    def tearDown(self):
        """
        Cleans up the environment after each test method execution.
        Deletes temporary directories and files and stops the mock patcher.
        """
        self.patcher.stop()
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def _write_config_file(self, content: dict):
        """
        Helper method: Writes dictionary content to the simulated configuration file.

        Args:
            content (dict): A dictionary representing the configuration data to write.
        """
        with open(self.test_config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(content, f, allow_unicode=True)

    def test_load_config_success(self):
        """
        Tests successful configuration loading from a valid YAML file.
        Verifies that all defined configuration items, including an unknown one,
        are loaded correctly and have the expected data types.
        """
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
        self._write_config_file(test_data)

        config_instance = _Config()

        self.assertEqual(config_instance.TESSERACT_CMD, "tesseract_path")
        self.assertEqual(config_instance.OCR_LANGUAGE, "eng")
        self.assertEqual(config_instance.CONF_THRESHOLD, 70)
        self.assertEqual(config_instance.PAR_CONF_THRESHOLD, 80)
        self.assertEqual(config_instance.OCR_FPS, 1.5)
        self.assertTrue(config_instance.DEBUG_MODE)
        self.assertEqual(config_instance.STOP_HOTKEY, "ctrl+alt+s")
        self.assertEqual(config_instance.UI_UPDATE_INTERVAL, 100)
        self.assertEqual(config_instance.HIGHLIGHT_RECT_OUTLINE_COLOR, "#FF0000")
        self.assertEqual(config_instance.HIGHLIGHT_RECT_OUTLINE_WIDTH, 2)
        self.assertEqual(config_instance.DEBUG_RECT_OUTLINE_COLOR, "#00FF00")
        self.assertEqual(config_instance.DEBUG_RECT_OUTLINE_WIDTH, 1)
        self.assertEqual(config_instance.LOG_LEVEL, "INFO")
        self.assertEqual(config_instance.UNKNOWN_KEY, "unknown_value")

    def test_load_config_file_not_found(self):
        """
        Tests handling when the configuration file is not found.
        Ensures that a warning is logged when the file is absent.
        """
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)

        with self.assertLogs('root', level='WARNING') as cm:
            _Config()
            self.assertIn(f"Configuration file {self.test_config_path} not found.", cm.output[0])

    def test_load_config_empty_file(self):
        """
        Tests handling when the configuration file is empty.
        Ensures that an INFO message is logged indicating an empty or invalid file.
        """
        self.test_config_path = os.path.join(self.test_dir, CONFIG_FILE)
        self._write_config_file({})

        with self.assertLogs('root', level='INFO') as cm:
            _Config()
            self.assertIn(f"Configuration file {self.test_config_path} is empty or invalid.", cm.output[0])

    def test_load_config_invalid_yaml(self):
        """
        Tests handling when the configuration file has an incorrect YAML format.
        Ensures that an ERROR message is logged when the YAML is malformed.
        """
        with open(self.test_config_path, 'w', encoding='utf-8') as f:
            f.write("invalid yaml: - ")

        with self.assertLogs('root', level='ERROR') as cm:
            _Config()
            self.assertIn(f"Error loading configuration file {self.test_config_path}", cm.output[0])

    def test_data_type_conversion(self):
        """
        Tests the correctness of data type conversion, especially for boolean and numeric types.
        Verifies that string representations are correctly converted to their target types.
        """
        test_data = {
            "CONF_THRESHOLD": "90",
            "OCR_FPS": "2.5",
            "DEBUG_MODE": "False",
            "LOG_LEVEL": "DEBUG"
        }
        self._write_config_file(test_data)

        config_instance = _Config()

        self.assertEqual(config_instance.CONF_THRESHOLD, 90)
        self.assertEqual(config_instance.OCR_FPS, 2.5)
        self.assertFalse(config_instance.DEBUG_MODE)
        self.assertEqual(config_instance.LOG_LEVEL, "DEBUG")

    def test_update_config_file(self):
        """
        Tests the functionality of the update_config_file method.
        Verifies that instance attributes are correctly updated and that changes
        are written back to the configuration file.
        """
        initial_data = {
            "CONF_THRESHOLD": 70,
            "DEBUG_MODE": True
        }
        self._write_config_file(initial_data)

        config_instance = _Config()

        new_config = {
            "CONF_THRESHOLD": 85,
            "DEBUG_MODE": False,
            "NEW_SETTING": "test_value"
        }
        config_instance.update_config_file(new_config)

        self.assertEqual(config_instance.CONF_THRESHOLD, 85)
        self.assertFalse(config_instance.DEBUG_MODE)
        self.assertEqual(config_instance.NEW_SETTING, "test_value")

        with open(self.test_config_path, encoding='utf-8') as f:
            updated_data = yaml.safe_load(f)

        self.assertEqual(updated_data["CONF_THRESHOLD"], 85)
        self.assertFalse(updated_data["DEBUG_MODE"])
        self.assertEqual(updated_data["NEW_SETTING"], "test_value")

    @mock.patch('config.Observer')
    def test_file_monitoring(self, MockObserver):
        """
        Tests the file monitoring function.
        Verifies that the `on_modified` event correctly triggers configuration reloading
        when the configuration file is changed.
        """
        initial_data = {
            "CONF_THRESHOLD": 70
        }
        self._write_config_file(initial_data)

        config_instance = _Config()
        self.assertEqual(config_instance.CONF_THRESHOLD, 70)

        event_handler = ConfigFileEventHandler(config_instance)
        mock_event = mock.Mock()
        mock_event.is_directory = False
        mock_event.src_path = self.test_config_path

        updated_data = {
            "CONF_THRESHOLD": 99
        }
        self._write_config_file(updated_data)

        event_handler.on_modified(mock_event)

        self.assertEqual(config_instance.CONF_THRESHOLD, 99)


if __name__ == '__main__':
    unittest.main()
