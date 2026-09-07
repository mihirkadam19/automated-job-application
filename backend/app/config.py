import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        key = os.environ["SESSION_ENCRYPTION_KEY"]
        self.session_encryption_key: bytes = key.encode()
        self.anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")


@lru_cache
def get_settings() -> Settings:
    return Settings()
