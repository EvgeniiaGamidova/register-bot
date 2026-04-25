import os

from env import load_env

load_env()

def _get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _get_optional_int(name: str) -> int | None:
    raw_value = _get_env(name)
    return int(raw_value) if raw_value else None

BOT_TOKEN = _get_env("BOT_TOKEN")
GROUP_CHAT_ID = _get_optional_int("GROUP_CHAT_ID")
GROUP_TOPIC_ID = _get_optional_int("GROUP_TOPIC_ID")
LOG_LEVEL = _get_env("LOG_LEVEL", "INFO").upper()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден. Укажите его в файле .env")
