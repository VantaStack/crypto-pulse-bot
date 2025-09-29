"""
config.py
---------
Environment-backed settings using Pydantic for validation.
"""

from pydantic import BaseModel, Field, ValidationError
import os


class Settings(BaseModel):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    default_lang: str = Field("en", alias="DEFAULT_LANG")
    cache_ttl: int = Field(60, alias="CACHE_TTL")
    allowed_chats: str = Field("", alias="ALLOWED_CHATS")

    def is_chat_allowed(self, chat_id: int) -> bool:
        """Check if a chat_id is allowed based on comma-separated ALLOWED_CHATS."""
        if not self.allowed_chats:
            return True
        try:
            allowed = {
                int(x.strip())
                for x in self.allowed_chats.split(",")
                if x.strip().isdigit()
            }
        except ValueError:
            return True
        return chat_id in allowed


def load_settings() -> Settings:
    env = {k: v for k, v in os.environ.items()}
    try:
        return Settings.model_validate(env)
    except ValidationError as e:
        raise RuntimeError(f"Invalid configuration: {e}") from e


SETTINGS = load_settings()
