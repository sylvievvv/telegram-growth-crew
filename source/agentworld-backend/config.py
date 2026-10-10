"""All settings come from environment variables (or a .env file next to this one).

Never put tokens in code or in the dashboard page. Keep them in .env on the server.
"""
import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass


def _int(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    return int(value) if value else default


@dataclass(frozen=True)
class Settings:
    # Telegram: the NEW "Agent World" bot that talks to the owner (not the existing posting bot)
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    owner_chat_id: int = _int("OWNER_CHAT_ID", 0)

    # TGStat API (https://api.tgstat.ru) for finding channels and their numbers
    tgstat_token: str = os.getenv("TGSTAT_TOKEN", "")
    tgstat_country: str = os.getenv("TGSTAT_COUNTRY", "")
    tgstat_language: str = os.getenv("TGSTAT_LANGUAGE", "")
    tgstat_category: str = os.getenv("TGSTAT_CATEGORY", "")

    # Claude writes the messages to channel admins
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")

    # About the owner's channel, used in the messages to admins
    my_channel: str = os.getenv("MY_CHANNEL", "@your_channel")
    my_channel_pitch: str = os.getenv(
        "MY_CHANNEL_PITCH",
        "a crypto education channel: explainers, polls, no trading signals",
    )
    my_name: str = os.getenv("MY_NAME", "")

    # Which channels the Scout keeps
    min_subscribers: int = _int("MIN_SUBSCRIBERS", 3000)
    max_subscribers: int = _int("MAX_SUBSCRIBERS", 300000)

    db_path: str = os.getenv("DB_PATH", "agentworld.db")


settings = Settings()
