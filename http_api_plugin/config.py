import json
import os
from dataclasses import dataclass, field

from loguru import logger

DEFAULT_FIELDS = {
    "current_time": True,
    "current_day_of_week": True,
    "current_week": True,
    "current_week_of_cycle": True,
    "time_offset": True,
    "schedule_meta": True,
    "current_day_entries": True,
    "current_entry": True,
    "current_subject": True,
    "current_title": True,
    "next_entries": True,
    "current_status": True,
    "progress": True,
    "remaining_time": True,
}

DEFAULT_PORT = 8080


@dataclass
class Config:
    port: int = DEFAULT_PORT
    fields: dict = field(default_factory=dict)

    def is_field_enabled(self, key: str) -> bool:
        return self.fields.get(key, True)


def load_config(plugin_dir: str) -> Config:
    config_path = os.path.join(plugin_dir, "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"配置已加载：{config_path}")
            return Config(port=data.get("port", DEFAULT_PORT), fields=data.get("fields", {}))
        else:
            logger.warning("找不到配置文件，创建一个默认配置")
            cfg = Config(port=DEFAULT_PORT, fields=dict(DEFAULT_FIELDS))
            save_config(cfg, config_path)
            return cfg
    except Exception as e:
        logger.error(f"配置加载失败：{e}")
        return Config(port=DEFAULT_PORT, fields={})


def save_config(config: Config, config_path: str) -> None:
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump({"port": config.port, "fields": config.fields}, f, indent=2, ensure_ascii=False)
    logger.info(f"默认配置已创建：{config_path}")
