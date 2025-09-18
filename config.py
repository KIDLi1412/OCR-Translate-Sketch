import logging
import os
import threading
from typing import ClassVar, Any

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# 配置文件路径
CONFIG_FILE = "config.yaml"


class _Config:
    # 定义配置项及其预期类型
    _config_types: ClassVar[dict] = {
        "TESSERACT_CMD": str,
        "OCR_LANGUAGE": str,
        "CONF_THRESHOLD": int,
        "PAR_CONF_THRESHOLD": int,
        "OCR_FPS": float,
        "DEBUG_MODE": bool,
        "STOP_HOTKEY": str,
        "UI_UPDATE_INTERVAL": int,
        "HIGHLIGHT_RECT_OUTLINE_COLOR": str,
        "HIGHLIGHT_RECT_OUTLINE_WIDTH": int,
        "DEBUG_RECT_OUTLINE_COLOR": str,
        "DEBUG_RECT_OUTLINE_WIDTH": int,
        "LOG_LEVEL": str,
    }

    def __init__(self):
        """
        _Config 类的构造函数。
        初始化配置并启动文件观察器。
        """
        self._load_config()
        self._start_watcher()  # 启动文件观察器

    def _set_attribute(self, key: str, value: Any) -> None:
        """
        根据预期的类型验证、转换并设置属性。

        Args:
            key (str): 配置项的名称。
            value (Any): 配置项的值。
        """
        if key in self._config_types:
            expected_type = self._config_types[key]
            # 对布尔值进行特殊处理
            if expected_type is bool:
                converted_value = str(value).lower() == "true"
                setattr(self, key, converted_value)
            # 对其他类型进行转换
            else:
                try:
                    setattr(self, key, expected_type(value))
                except (ValueError, TypeError) as e:
                    logging.warning(
                        f"配置项 '{key}' 的值 '{value}' 无法转换为 {expected_type.__name__}, 将使用原始值。错误: {e}"
                    )
                    setattr(self, key, value)
        else:
            # 如果没有定义类型，直接设置
            setattr(self, key, value)

    def _load_config(self):
        """
        加载配置文件。
        """
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                logging.info(f"配置文件 {CONFIG_FILE} 为空或格式无效。")
                return

            for key, value in config_data.items():
                self._set_attribute(key, value)

            logging.info(f"配置已从 {CONFIG_FILE} 重新加载。")

        except FileNotFoundError:
            logging.warning(f"配置文件 {CONFIG_FILE} 未找到。将使用默认值（如果有）。")
        except yaml.YAMLError as e:
            logging.error(f"加载配置文件 {CONFIG_FILE} 时出错: {e}")

    def update_config_file(self, new_config: dict) -> None:
        """
        更新配置并将其写入配置文件。

        Args:
            new_config (dict): 包含要更新的配置项的字典。
        """
        # 更新当前配置并进行类型转换
        converted_config = {}
        for key, value in new_config.items():
            if key in self._config_types:
                expected_type = self._config_types[key]
                converted_value = str(value).lower() == "true" if expected_type is bool else expected_type(value)
                setattr(self, key, converted_value)
                converted_config[key] = converted_value
            else:
                setattr(self, key, value)
                converted_config[key] = value

        # 将更新后的配置写入文件
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.safe_dump(converted_config, f, allow_unicode=True)
            logging.info(f"配置已更新并保存到 {CONFIG_FILE}。")
        except Exception as e:
            logging.error(f"保存配置文件时出错: {e}")


    def _start_watcher(self):
        """
        启动文件系统观察器, 监听 config.yaml 的变化。
        """
        event_handler = ConfigFileEventHandler(self)
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(CONFIG_FILE) or ".", recursive=False)
        observer.start()
        logging.info(f"正在监听 {CONFIG_FILE} 的变化...")


class ConfigFileEventHandler(FileSystemEventHandler):
    """
    处理配置文件变化的事件。
    """

    def __init__(self, config_instance: _Config):
        """
        ConfigFileEventHandler 类的构造函数。

        Args:
            config_instance (_Config): _Config 类的实例。
        """
        super().__init__()
        self.config_instance = config_instance

    def on_modified(self, event):
        """
        当配置文件被修改时重新加载配置。
        """
        if not event.is_directory and os.path.basename(event.src_path) == CONFIG_FILE:
            logging.info(f"检测到 {CONFIG_FILE} 发生变化, 正在重新加载配置...")
            self.config_instance._load_config()


config = _Config()