import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        key = os.environ["SESSION_ENCRYPTION_KEY"]
        self.session_encryption_key: bytes = key.encode()
        self.login_wait_timeout_seconds: float = float(
            os.getenv("LOGIN_WAIT_TIMEOUT_SECONDS", "600")
        )
        self.login_poll_interval_seconds: float = float(
            os.getenv("LOGIN_POLL_INTERVAL_SECONDS", "2")
        )
        self.anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")


@lru_cache
def get_settings() -> Settings:
    return Settings()
