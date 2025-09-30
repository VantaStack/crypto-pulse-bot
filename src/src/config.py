# src/config.py
"""
Typed configuration using Pydantic BaseSettings.

Environment keys:
- BOT_TOKEN (required)
- CACHE_TTL (default: 60)
- HTTP_RETRIES (default: 3)
- HTTP_TIMEOUT (default: 10)
- PARSE_MODE (default: HTML)
- RATE_LIMIT_COOLDOWN (default: 0.7)
- LOG_LEVEL (default: INFO)
- ALLOWED_CHATS (comma-separated ints; empty=allow all)

Provides:
- Settings: typed access to env values
- is_chat_allowed(chat_id): safe check supporting negative/positive IDs
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    bot_token: str = Field(..., env="BOT_TOKEN")
    cache_ttl: int = Field(60, env="CACHE_TTL")
    http_retries: int = Field(3, env="HTTP_RETRIES")
    http_timeout: int = Field(10, env="HTTP_TIMEOUT")
    parse_mode: str = Field("HTML", env="PARSE_MODE")
    rate_limit_cooldown: float = Field(0.7, env="RATE_LIMIT_COOLDOWN")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    allowed_chats_raw: Optional[str] = Field(None, env="ALLOWED_CHATS")

    # normalized list (ints) built from allowed_chats_raw
    allowed_chats: List[int] = Field(default_factory=list)

    @validator("allowed_chats", pre=True, always=True)
    def _normalize_allowed(cls, v, values):
        raw = values.get("allowed_chats_raw")
        if not raw:
            return []
        items = [s.strip() for s in raw.split(",") if s.strip()]
        out: List[int] = []
        for s in items:
            try:
                # support negative IDs (groups/supergroups) and positives (users/chats)
                out.append(int(s))
            except ValueError:
                # skip invalid entries silently
                continue
        return out

    def is_chat_allowed(self, chat_id: int) -> bool:
        # empty list means allow all
        if not self.allowed_chats:
            return True
        try:
            return int(chat_id) in self.allowed_chats
        except Exception:
            return False

    class Config:
        env_file = ".env"
        case_sensitive = False        Accepts values like: "123,-456, 789" and returns "123,-456,789".
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
