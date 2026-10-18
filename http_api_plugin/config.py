import json
import os
from dataclasses import dataclass

from loguru import logger

DEFAULT_PORT = 8080


@dataclass
class Config:
    port: int = DEFAULT_PORT


def load_config(plugin_dir: str) -> Config:
    config_path = os.path.join(plugin_dir, "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"配置已加载：{config_path}")
            return Config(port=data.get("port", DEFAULT_PORT))
        else:
            logger.warning("找不到配置文件，创建一个默认配置")
            cfg = Config(port=DEFAULT_PORT)
            save_config(cfg, config_path)
            return cfg
    except Exception as e:
        logger.error(f"配置加载失败：{e}")
        return Config(port=DEFAULT_PORT)


def save_config(config: Config, config_path: str) -> None:
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump({"port": config.port}, f, indent=2, ensure_ascii=False)
    logger.info(f"默认配置已创建：{config_path}")
