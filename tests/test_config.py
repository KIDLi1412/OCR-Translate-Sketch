import unittest
import os
import yaml
import tempfile
from unittest import mock

from config import _Config, CONFIG_FILE, ConfigFileEventHandler

class TestConfig(unittest.TestCase):
    """
    测试 _Config 类及其相关功能。
    """

    def setUp(self):
        """
        在每个测试方法执行前设置环境。
        创建临时目录和文件，以模拟 config.yaml。
        """
        self.test_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.test_dir, CONFIG_FILE)

        # 模拟 CONFIG_FILE 路径
        self.original_config_file = CONFIG_FILE
        # 使用 mock.patch 替换 CONFIG_FILE 变量
        self.patcher = mock.patch('config.CONFIG_FILE', self.test_config_path)
        self.patcher.start()

    def tearDown(self):
        """
        在每个测试方法执行后清理环境。
        删除临时目录和文件。
        """
        self.patcher.stop()
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def _write_config_file(self, content: dict):
        """
        辅助方法：将字典内容写入模拟的配置文件。
        """
        with open(self.test_config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(content, f, allow_unicode=True)

    def test_load_config_success(self):
        """
        测试从有效的 YAML 文件成功加载配置。
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
            "UNKNOWN_KEY": "unknown_value" # 测试未知配置项
        }
        self._write_config_file(test_data)

        # 实例化 _Config 类，这将触发配置加载
        config_instance = _Config()

        # 验证配置项是否正确加载
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
        self.assertEqual(config_instance.UNKNOWN_KEY, "unknown_value") # 验证未知配置项

    def test_load_config_file_not_found(self):
        """
        测试配置文件不存在时的处理。
        """
        # 确保配置文件不存在
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)

        with self.assertLogs('root', level='WARNING') as cm:
            _Config()
            self.assertIn(f"配置文件 {self.test_config_path} 未找到。", cm.output[0])

    def test_load_config_empty_file(self):
        """
        测试配置文件为空时的处理。
        """
        self._write_config_file({}) # 写入空配置

        with self.assertLogs('root', level='INFO') as cm:
            _Config()
            self.assertIn(f"配置文件 {self.test_config_path} 为空或格式无效。", cm.output[0])

    def test_load_config_invalid_yaml(self):
        """
        测试配置文件格式错误时的处理。
        """
        with open(self.test_config_path, 'w', encoding='utf-8') as f:
            f.write("invalid yaml: - ") # 写入无效 YAML 格式

        with self.assertLogs('root', level='ERROR') as cm:
            _Config()
            self.assertIn(f"加载配置文件 {self.test_config_path} 时出错", cm.output[0])

    def test_data_type_conversion(self):
        """
        测试数据类型转换的正确性，特别是布尔值和数字类型。
        """
        test_data = {
            "CONF_THRESHOLD": "90", # 字符串数字
            "OCR_FPS": "2.5", # 字符串浮点数
            "DEBUG_MODE": "False", # 字符串布尔值
            "LOG_LEVEL": "DEBUG" # 字符串，不需转换
        }
        self._write_config_file(test_data)

        config_instance = _Config()

        self.assertEqual(config_instance.CONF_THRESHOLD, 90)
        self.assertEqual(config_instance.OCR_FPS, 2.5)
        self.assertFalse(config_instance.DEBUG_MODE)
        self.assertEqual(config_instance.LOG_LEVEL, "DEBUG")

    def test_update_config_file(self):
        """
        测试 update_config_file 方法的功能：正确更新实例属性并将变更回写到文件。
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

        # 验证实例属性是否更新
        self.assertEqual(config_instance.CONF_THRESHOLD, 85)
        self.assertFalse(config_instance.DEBUG_MODE)
        self.assertEqual(config_instance.NEW_SETTING, "test_value")

        # 验证文件内容是否更新
        with open(self.test_config_path, 'r', encoding='utf-8') as f:
            updated_data = yaml.safe_load(f)

        self.assertEqual(updated_data["CONF_THRESHOLD"], 85)
        self.assertFalse(updated_data["DEBUG_MODE"])
        self.assertEqual(updated_data["NEW_SETTING"], "test_value")

    @mock.patch('config.Observer')
    def test_file_monitoring(self, MockObserver):
        """
        测试文件监控功能：验证 on_modified 事件能正确触发配置重载。
        """
        # 初始配置
        initial_data = {
            "CONF_THRESHOLD": 70
        }
        self._write_config_file(initial_data)

        config_instance = _Config()
        self.assertEqual(config_instance.CONF_THRESHOLD, 70)

        # 模拟文件修改事件
        event_handler = ConfigFileEventHandler(config_instance)
        mock_event = mock.Mock()
        mock_event.is_directory = False
        mock_event.src_path = self.test_config_path

        # 修改配置文件内容
        updated_data = {
            "CONF_THRESHOLD": 99
        }
        self._write_config_file(updated_data)

        # 触发 on_modified 事件
        event_handler.on_modified(mock_event)

        # 验证配置是否重新加载
        self.assertEqual(config_instance.CONF_THRESHOLD, 99)


if __name__ == '__main__':
    unittest.main()