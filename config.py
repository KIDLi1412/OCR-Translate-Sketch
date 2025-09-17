"""
config.py

此文件包含 OCR-Translate-Sketch 应用程序的所有配置参数。
通过修改此文件, 可以调整应用程序的行为, 而无需更改主程序逻辑。
"""

import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import threading

# NOTE: 配置文件路径
CONFIG_FILE = 'config.yaml'

class Config:
    """
    应用程序配置类。
    从 config.yaml 加载配置, 并支持热加载。
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Config, cls).__new__(cls)
                    cls._instance._load_config()
                    cls._instance._start_watcher()
        return cls._instance

    def _load_config(self):
        """
        从 config.yaml 文件加载配置。
        """
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                for key, value in config_data.items():
                    setattr(self, key, value)
            print(f"配置已从 {CONFIG_FILE} 重新加载。")
        except FileNotFoundError:
            print(f"错误: 配置文件 {CONFIG_FILE} 未找到。")
        except Exception as e:
            print(f"加载配置文件时发生错误: {e}")

    def update_config_file(self, updated_config):
        """
        更新 config.yaml 文件中的配置。

        Args:
            updated_config (dict): 包含要更新的配置项的字典。
        """
        try:
            # 读取现有配置以保留未修改的项
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f)
            
            if current_config is None:
                current_config = {}

            # 更新配置
            for key, value in updated_config.items():
                # 尝试将字符串值转换回原始类型 (例如, int, bool)
                if isinstance(value, str):
                    if value.lower() == 'true':
                        current_config[key] = True
                    elif value.lower() == 'false':
                        current_config[key] = False
                    elif value.isdigit():
                        current_config[key] = int(value)
                    else:
                        current_config[key] = value
                else:
                    current_config[key] = value

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                yaml.safe_dump(current_config, f, allow_unicode=True)
            print(f"配置已成功保存到 {CONFIG_FILE}。")
            self._load_config()  # 重新加载配置到当前实例
        except Exception as e:
            print(f"保存配置文件时发生错误: {e}")

    def _start_watcher(self):
        """
        启动文件系统观察器, 监听 config.yaml 的变化。
        """
        event_handler = ConfigFileEventHandler(self)
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(CONFIG_FILE) or '.', recursive=False)
        observer.start()
        print(f"正在监听 {CONFIG_FILE} 的变化...")

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
            print(f"检测到 {CONFIG_FILE} 发生变化, 正在重新加载配置...")
            self.config_instance._load_config()

