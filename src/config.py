import json
import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str = ""
    admin_ids: list[int] = []
    remna_api_url: str = ""
    remna_api_token: str = ""
    monitor_user_uuid: str = ""
    singbox_bin: str = "/usr/local/bin/sing-box"
    db_path: str = "./data/bot.db"
    log_path: str = "./logs/bot.log"
    tz: str = "Europe/Moscow"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    @classmethod
    def load(cls) -> "Settings":
        if not Path(".env").exists():
            return cls()
        return cls()  # type: ignore

    def is_configured(self) -> bool:
        if not self.bot_token or "your_bot_token" in self.bot_token:
            return False
        if not self.admin_ids:
            return False
        if not self.remna_api_url or "example.com" in self.remna_api_url:
            return False
        if not self.remna_api_token or "your_jwt_token" in self.remna_api_token:
            return False
        if not self.monitor_user_uuid or self.monitor_user_uuid == "00000000-0000-0000-0000-000000000000":
            return False
        return True


settings = Settings.load()
