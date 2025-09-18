import logging
import os
import threading
from typing import ClassVar

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# 配置文件路径
CONFIG_FILE = "config.yaml"


class Config:
    _instance = None
    _lock = threading.Lock()

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

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance._load_config()
                cls._instance._start_watcher()  # 启动文件观察器
        return cls._instance

    def _load_config(self):
        """
        加载配置文件。
        """
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
                if config_data is not None:  # 检查 config_data 是否为 None
                    for key, value in config_data.items():
                        if key in self._config_types:
                            expected_type = self._config_types[key]
                            if expected_type is bool:
                                setattr(self, key, str(value).lower() == "true")
                            else:
                                setattr(self, key, expected_type(value))
                        else:
                            setattr(self, key, value)
                    logging.info(f"配置已从 {CONFIG_FILE} 重新加载。")
                else:
                    logging.info(f"配置文件 {CONFIG_FILE} 为空或不包含任何配置。")
        except (FileNotFoundError, yaml.YAMLError) as e:
            logging.error(f"加载配置文件时出错: {e}")

    def _start_watcher(self):
        """
        启动文件系统观察器, 监听 config.yaml 的变化。
        """
        event_handler = ConfigFileEventHandler(self)
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(CONFIG_FILE) or ".", recursive=False)
        observer.start()
        logging.info(f"正在监听 {CONFIG_FILE} 的变化...")  # 使用 logging.info

    def update_config_file(self, new_config: dict) -> None:
        """
        更新配置并将其写入配置文件。

        Args:
            new_config (dict): 包含要更新的配置项的字典。
        """
        with self._lock:
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


class ConfigFileEventHandler(FileSystemEventHandler):
    """
    处理配置文件变化的事件。
    """

    def __init__(self, config_instance):
        super().__init__()
        self.config_instance = config_instance

    def on_modified(self, event):
        """
        当配置文件被修改时重新加载配置。
        """
        if not event.is_directory and os.path.basename(event.src_path) == CONFIG_FILE:
            logging.info(f"检测到 {CONFIG_FILE} 发生变化, 正在重新加载配置...")  # 使用 logging.info
            self.config_instance._load_config()
