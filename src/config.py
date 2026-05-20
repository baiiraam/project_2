from typing import Any, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    LLM_PROVIDER: str = "offline"
    LLM_MODEL: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    OPENAI_BASE_URL: Optional[str] = None

    CACHE_BACKEND: Optional[str] = None  # redis, sqlite, or json

    # For Redis
    REDIS_URL: Optional[str] = None

    # For SQLite
    # SQLITE_CACHE_PATH=cache.db

    # For JSON (existing)
    JSON_CACHE_MAX_SIZE_MB: Optional[int] = 100
    JSON_CACHE_BACKUP_COUNT: Optional[int] = 3

    NUTRITION_PROVIDER: str = "usda"
    USDA_API_KEY: Optional[str] = None
    OPENFOODFACTS_USER_AGENT: str = "AI-Food-Analyzer/1.0 (default@example.com)"

    HTTP_CACHE_ENABLED: bool = Field(default=True)
    HTTP_CACHE_TTL_SECONDS: int = Field(default=86400, ge=60, le=86400)

    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = Field(..., description="Postgresql connection url")
    NUTRITION_CACHE_TTL_SECONDS: int = Field(default=86400, ge=60, le=86400)
    MAX_IMAGE_SIZE_MB: int = Field(default=5, ge=1, le=10)
    HTTP_PORT: int = 8000

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @field_validator("NUTRITION_PROVIDER")
    @classmethod
    def validate_nutrition_provider(cls, v: str) -> str:
        valid_providers = ["usda", "openfoodfacts", "mock"]
        if v.lower() not in valid_providers:
            if len(valid_providers) == 1:
                raise ValueError(f"NUTRITION_PROVIDER must be {valid_providers[0]}")
            else:
                raise ValueError(f"NUTRITION_PROVIDER must be one of {valid_providers}")
        return v.lower()

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        prefixes = ["postgresql://"]
        if not any(v.startswith(prefix) for prefix in prefixes):
            raise ValueError(
                f"DATABASE_URL must start with one of prefixes: {prefixes}"
            )
        return v

    def model_post_init(self, _: Any) -> None:
        if self.LLM_PROVIDER == "offline" and (
            self.ANTHROPIC_API_KEY or self.OPENAI_API_KEY or self.GOOGLE_API_KEY
        ):
            raise ValueError(
                "LLM_PROVIDER is set to offline but API keys are provided for models. You should either set LLM_PROVIDER to the appropriate model or remove the API keys."
            )

        if self.ANTHROPIC_API_KEY and self.LLM_PROVIDER != "anthropic":
            raise ValueError(
                'API KEY is provided for a model that is not set as LLM_PROVIDER.\nMaybe you want to use "anthropic" as LLM_PROVIDER?'
            )

        if self.OPENAI_API_KEY and self.LLM_PROVIDER != "openai":
            raise ValueError(
                'API KEY is provided for a model that is not set as LLM_PROVIDER.\nMaybe you want to use "openai" as LLM_PROVIDER?'
            )

        if self.GOOGLE_API_KEY and self.LLM_PROVIDER != "gemini":
            raise ValueError(
                'API KEY is provided for a model that is not set as LLM_PROVIDER.\nMaybe you want to use "gemini" as LLM_PROVIDER?'
            )

        if self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            raise ValueError(
                "LLM_PROVIDER is set but no API key is provided for that model"
            )
        if self.LLM_PROVIDER == "gemini" and not self.GOOGLE_API_KEY:
            raise ValueError(
                "LLM_PROVIDER is set but no API key is provided for that model"
            )
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError(
                "LLM_PROVIDER is set but no API key is provided for that model"
            )

        if self.NUTRITION_PROVIDER == "usda" and not self.USDA_API_KEY:
            raise ValueError("NUTRITION_PROVIDER is set but no API key is provided")

        if (
            self.NUTRITION_PROVIDER == "openfoodfacts"
            and not self.OPENFOODFACTS_USER_AGENT
        ):
            raise ValueError(
                "OPENFOODFACTS_USER_AGENT required when NUTRITION_PROVIDER='openfoodfacts'"
            )


_settings_instance = None


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
