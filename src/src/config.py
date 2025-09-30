"""
Application settings loader.

- Pydantic BaseSettings for strong-typed ENV loading
- Normalizes and validates allowed chat IDs (accepts negative IDs)
- Exposes helper methods: get_allowed_chats, is_chat_allowed
- Keeps defaults sane for local dev and CI
"""
from __future__ import annotations

from typing import Optional, Set
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    # Required
    bot_token: str = Field(..., env="BOT_TOKEN")

    # Optional controls
    allowed_chats: Optional[str] = Field(None, env="ALLOWED_CHATS")
    cache_ttl: int = Field(30, env="CACHE_TTL")
    http_retries: int = Field(3, env="HTTP_RETRIES")
    http_timeout: int = Field(10, env="HTTP_TIMEOUT")
    parse_mode: str = Field("MarkdownV2", env="PARSE_MODE")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    rate_limit_cooldown: float = Field(0.7, env="RATE_LIMIT_COOLDOWN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        validate_assignment = True

    @validator("allowed_chats", pre=True)
    def _normalize_allowed_chats(cls, v: Optional[str]) -> Optional[str]:
        """
        Normalize comma-separated input into a clean comma-separated string of ints.
        Accepts values like: "123,-456, 789" and returns "123,-456,789".
        Non-integer parts are ignored.
        """
        if v is None:
            return None
        parts = [p.strip() for p in str(v).split(",") if p.strip()]
        cleaned: list[str] = []
        for p in parts:
            try:
                cleaned.append(str(int(p)))
            except ValueError:
                # ignore non-integer token
                continue
        return ",".join(cleaned) if cleaned else None

    def get_allowed_chats(self) -> Set[int]:
        """
        Return a set of allowed chat IDs. Empty set means "allow all".
        """
        if not self.allowed_chats:
            return set()
        return {int(x) for x in self.allowed_chats.split(",")}

    def is_chat_allowed(self, chat_id: int) -> bool:
        """
        Check whether a chat_id is allowed. If allowed_chats is empty, permit all.
        """
        allowed = self.get_allowed_chats()
        if not allowed:
            return True
        return chat_id in allowed
