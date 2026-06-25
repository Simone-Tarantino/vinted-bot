from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    database_url: str = Field(
        default="sqlite:///./vinted_bot.db",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")

    vinted_session_encryption_key: str = Field(
        default="change-me-to-32-byte-secret-key!!",
        alias="VINTED_SESSION_ENCRYPTION_KEY",
    )
    vinted_session_file: str = Field(
        default="/data/vinted_session.enc",
        alias="VINTED_SESSION_FILE",
    )

    scan_interval_minutes: int = Field(default=15, alias="SCAN_INTERVAL_MINUTES")
    notification_cooldown_hours: int = Field(default=24, alias="NOTIFICATION_COOLDOWN_HOURS")
    max_ai_evaluations_per_search: int = Field(
        default=25, alias="MAX_AI_EVALUATIONS_PER_SEARCH"
    )
    ebay_benchmark_enabled: bool = Field(default=True, alias="EBAY_BENCHMARK_ENABLED")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    disable_scheduler: bool = Field(default=False, alias="DISABLE_SCHEDULER")

    @field_validator("gemini_api_key")
    @classmethod
    def validate_gemini_key_not_empty_when_checked(cls, value: str) -> str:
        return value.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
