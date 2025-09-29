from __future__ import annotations
from pydantic import BaseSettings, Field, validator
from typing import Optional

class Settings(BaseSettings):
    bot_token: str = Field(..., env="BOT_TOKEN")
    allowed_chats: Optional[str] = Field(None, env="ALLOWED_CHATS")
    cache_ttl: int = Field(30, env="CACHE_TTL")
    http_retries: int = Field(3, env="HTTP_RETRIES")
    http_timeout: int = Field(10, env="HTTP_TIMEOUT")
    parse_mode: str = Field("MarkdownV2", env="PARSE_MODE")

    @validator("allowed_chats", pre=True)
    def normalize_allowed_chats(cls, v):
        if v is None:
            return None
        return ",".join(part.strip() for part in str(v).split(",") if part.strip())

    def is_chat_allowed(self, chat_id: int) -> bool:
        if not self.allowed_chats:
            return True
        allowed = set()
        for part in self.allowed_chats.split(","):
            try:
                allowed.add(int(part))
            except ValueError:
                continue
        return chat_id in allowed
