# from typing import Any, Optional

# from pydantic import Field, field_validator
# from pydantic_settings import BaseSettings, SettingsConfigDict


# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(env_file=".env")

#     LLM_PROVIDER: str = "offline"
#     LLM_MODEL: Optional[str] = None
#     ANTHROPIC_API_KEY: Optional[str] = None
#     OPENAI_API_KEY: Optional[str] = None
#     GOOGLE_API_KEY: Optional[str] = None

#     OPENAI_BASE_URL: Optional[str] = None

#     CACHE_BACKEND: Optional[str] = None  # redis, sqlite, or json

#     # For Redis
#     REDIS_URL: Optional[str] = None

#     # For SQLite
#     # SQLITE_CACHE_PATH=cache.db

#     # For JSON (existing)
#     JSON_CACHE_MAX_SIZE_MB: Optional[int] = 100
#     JSON_CACHE_BACKUP_COUNT: Optional[int] = 3

#     NUTRITION_PROVIDER: str = "usda"
#     USDA_API_KEY: Optional[str] = None
#     OPENFOODFACTS_USER_AGENT: str = "AI-Food-Analyzer/1.0 (default@example.com)"

#     HTTP_CACHE_ENABLED: bool = Field(default=True)
#     HTTP_CACHE_TTL_SECONDS: int = Field(default=86400, ge=60, le=86400)

#     LOG_LEVEL: str = "INFO"
#     DATABASE_URL: Optional[str] = None
#     NUTRITION_CACHE_TTL_SECONDS: int = Field(default=86400, ge=60, le=86400)
#     MAX_IMAGE_SIZE_MB: int = Field(default=5, ge=1, le=10)
#     HTTP_PORT: int = 8000

#     @field_validator("LOG_LEVEL")
#     @classmethod
#     def validate_log_level(cls, v: str) -> str:
#         valid_levels = ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]
#         if v.upper() not in valid_levels:
#             raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
#         return v.upper()

#     @field_validator("NUTRITION_PROVIDER")
#     @classmethod
#     def validate_nutrition_provider(cls, v: str) -> str:
#         valid_providers = ["usda", "openfoodfacts", "mock"]
#         if v.lower() not in valid_providers:
#             if len(valid_providers) == 1:
#                 raise ValueError(f"NUTRITION_PROVIDER must be {valid_providers[0]}")
#             else:
#                 raise ValueError(f"NUTRITION_PROVIDER must be one of {valid_providers}")
#         return v.lower()

#     @field_validator("DATABASE_URL")
#     @classmethod
#     def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
#         if v is None:
#             return v
#         prefixes = ["postgresql://", "sqlite:///"]
#         if not any(v.startswith(prefix) for prefix in prefixes):
#             raise ValueError(
#                 f"DATABASE_URL must start with one of prefixes: {prefixes}"
#             )
#         return v

#     def model_post_init(self, _: Any) -> None:
#         if self.LLM_PROVIDER == "offline" and (
#             self.ANTHROPIC_API_KEY or self.OPENAI_API_KEY or self.GOOGLE_API_KEY
#         ):
#             raise ValueError(
#                 "LLM_PROVIDER is set to offline but API keys are provided for models. You should either set LLM_PROVIDER to the appropriate model or remove the API keys."
#             )

#         if self.ANTHROPIC_API_KEY and self.LLM_PROVIDER != "anthropic":
#             raise ValueError(
#                 'API KEY is provided for a model that is not set as LLM_PROVIDER.\nMaybe you want to use "anthropic" as LLM_PROVIDER?'
#             )

#         if self.OPENAI_API_KEY and self.LLM_PROVIDER != "openai":
#             raise ValueError(
#                 'API KEY is provided for a model that is not set as LLM_PROVIDER.\nMaybe you want to use "openai" as LLM_PROVIDER?'
#             )

#         if self.GOOGLE_API_KEY and self.LLM_PROVIDER != "gemini":
#             raise ValueError(
#                 'API KEY is provided for a model that is not set as LLM_PROVIDER.\nMaybe you want to use "gemini" as LLM_PROVIDER?'
#             )

#         if self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
#             raise ValueError(
#                 "LLM_PROVIDER is set but no API key is provided for that model"
#             )
#         if self.LLM_PROVIDER == "gemini" and not self.GOOGLE_API_KEY:
#             raise ValueError(
#                 "LLM_PROVIDER is set but no API key is provided for that model"
#             )
#         if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
#             raise ValueError(
#                 "LLM_PROVIDER is set but no API key is provided for that model"
#             )

#         if self.NUTRITION_PROVIDER == "usda" and not self.USDA_API_KEY:
#             raise ValueError("NUTRITION_PROVIDER is set but no API key is provided")

#         if (
#             self.NUTRITION_PROVIDER == "openfoodfacts"
#             and not self.OPENFOODFACTS_USER_AGENT
#         ):
#             raise ValueError(
#                 "OPENFOODFACTS_USER_AGENT required when NUTRITION_PROVIDER='openfoodfacts'"
#             )


# _settings_instance = None


# def get_settings() -> Settings:
#     global _settings_instance
#     if _settings_instance is None:
#         _settings_instance = Settings()
#     return _settings_instance






































































# from typing import Any, List, Optional
# from pathlib import Path

# from pydantic import Field, field_validator
# from pydantic_settings import BaseSettings, SettingsConfigDict

# import logging
# from src.services.failover_provider import FailoverVLM




# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(env_file=".env")

#     LLM_PROVIDER: str = "offline"
#     LLM_MODEL: Optional[str] = None
#     ANTHROPIC_API_KEY: Optional[str] = None
#     OPENAI_API_KEY: Optional[str] = None
#     GOOGLE_API_KEY: Optional[str] = None

#     OPENAI_BASE_URL: Optional[str] = None

#     # ========== NEW: Provider-specific models (add these) ==========
#     OPENAI_MODEL: Optional[str] = None
#     ANTHROPIC_MODEL: Optional[str] = None
#     GEMINI_MODEL: Optional[str] = None

#     # ========== NEW: Failover toggle (add this) ==========
#     FAILOVER_ENABLED: bool = Field(default=False)

#     CACHE_BACKEND: Optional[str] = None  # redis, sqlite, or json

#     # For Redis
#     REDIS_URL: Optional[str] = None

#     # For SQLite
#     # SQLITE_CACHE_PATH=cache.db

#     # For JSON (existing)
#     JSON_CACHE_MAX_SIZE_MB: Optional[int] = 100
#     JSON_CACHE_BACKUP_COUNT: Optional[int] = 3

#     NUTRITION_PROVIDER: str = "usda"
#     USDA_API_KEY: Optional[str] = None
#     OPENFOODFACTS_USER_AGENT: str = "AI-Food-Analyzer/1.0 (default@example.com)"

#     HTTP_CACHE_ENABLED: bool = Field(default=True)
#     HTTP_CACHE_TTL_SECONDS: int = Field(default=86400, ge=60, le=86400)

#     LOG_LEVEL: str = "INFO"
#     DATABASE_URL: Optional[str] = None
#     NUTRITION_CACHE_TTL_SECONDS: int = Field(default=86400, ge=60, le=86400)
#     MAX_IMAGE_SIZE_MB: int = Field(default=5, ge=1, le=10)
#     HTTP_PORT: int = 8000

#     @field_validator("LOG_LEVEL")
#     @classmethod
#     def validate_log_level(cls, v: str) -> str:
#         valid_levels = ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]
#         if v.upper() not in valid_levels:
#             raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
#         return v.upper()

#     @field_validator("NUTRITION_PROVIDER")
#     @classmethod
#     def validate_nutrition_provider(cls, v: str) -> str:
#         valid_providers = ["usda", "openfoodfacts", "mock"]
#         if v.lower() not in valid_providers:
#             if len(valid_providers) == 1:
#                 raise ValueError(f"NUTRITION_PROVIDER must be {valid_providers[0]}")
#             else:
#                 raise ValueError(f"NUTRITION_PROVIDER must be one of {valid_providers}")
#         return v.lower()

#     @field_validator("DATABASE_URL")
#     @classmethod
#     def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
#         if v is None:
#             return v
#         prefixes = ["postgresql://", "sqlite:///"]
#         if not any(v.startswith(prefix) for prefix in prefixes):
#             raise ValueError(
#                 f"DATABASE_URL must start with one of prefixes: {prefixes}"
#             )
#         return v

#     def model_post_init(self, _: Any) -> None:
#         logger = logging.getLogger(__name__)

#         # Check 1: Offline mode with API keys
#         if self.LLM_PROVIDER == "offline" and (
#             self.ANTHROPIC_API_KEY or self.OPENAI_API_KEY or self.GOOGLE_API_KEY
#         ):
#             raise ValueError(
#                 "LLM_PROVIDER is set to offline but API keys are provided. "
#                 "Either set LLM_PROVIDER to 'openai', 'anthropic', or 'gemini', "
#                 "or remove the API keys."
#             )

#         # Check 2: Primary provider must have its API key
#         if self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
#             raise ValueError("LLM_PROVIDER='anthropic' but ANTHROPIC_API_KEY is not set")
#         if self.LLM_PROVIDER == "gemini" and not self.GOOGLE_API_KEY:
#             raise ValueError("LLM_PROVIDER='gemini' but GOOGLE_API_KEY is not set")
#         if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
#             raise ValueError("LLM_PROVIDER='openai' but OPENAI_API_KEY is not set")

#         # Check 3: Extra API keys (for failover) - warn but don't error
#         if self.ANTHROPIC_API_KEY and self.LLM_PROVIDER != "anthropic":
#             if self.FAILOVER_ENABLED:
#                 logger.info("Anthropic API key present for failover")
#             else:
#                 raise ValueError(
#                     "Anthropic API key provided but LLM_PROVIDER is not 'anthropic'. "
#                     "Set FAILOVER_ENABLED=true to use it for failover, or remove the key."
#                 )

#         if self.OPENAI_API_KEY and self.LLM_PROVIDER != "openai":
#             if self.FAILOVER_ENABLED:
#                 logger.info("OpenAI API key present for failover")
#             else:
#                 raise ValueError(
#                     "OpenAI API key provided but LLM_PROVIDER is not 'openai'. "
#                     "Set FAILOVER_ENABLED=true to use it for failover, or remove the key."
#                 )

#         if self.GOOGLE_API_KEY and self.LLM_PROVIDER != "gemini":
#             if self.FAILOVER_ENABLED:
#                 logger.info("Google API key present for failover")
#             else:
#                 raise ValueError(
#                     "Google API key provided but LLM_PROVIDER is not 'gemini'. "
#                     "Set FAILOVER_ENABLED=true to use it for failover, or remove the key."
#                 )

#         # Check 4: Nutrition provider validation
#         if self.NUTRITION_PROVIDER == "usda" and not self.USDA_API_KEY:
#             raise ValueError("NUTRITION_PROVIDER='usda' but USDA_API_KEY is not set")

#         if self.NUTRITION_PROVIDER == "openfoodfacts" and not self.OPENFOODFACTS_USER_AGENT:
#             raise ValueError(
#                 "OPENFOODFACTS_USER_AGENT required when NUTRITION_PROVIDER='openfoodfacts'"
#             )

#     # ========== NEW METHODS (add these after model_post_init) ==========

#     def get_available_providers(self) -> List[str]:
#         """Return list of VLM providers that have API keys configured."""
#         providers = []
#         if self.OPENAI_API_KEY:
#             providers.append("openai")
#         if self.ANTHROPIC_API_KEY:
#             providers.append("anthropic")
#         if self.GOOGLE_API_KEY:
#             providers.append("gemini")
#         return providers

#     def get_model_for_provider(self, provider: str) -> str:
#         """Get the model name for a specific provider.

#         Priority:
#         1. Provider-specific env var (e.g., OPENAI_MODEL)
#         2. Global LLM_MODEL
#         3. Provider default
#         """
#         provider_models = {
#             "openai": self.OPENAI_MODEL,
#             "anthropic": self.ANTHROPIC_MODEL,
#             "gemini": self.GEMINI_MODEL,
#         }

#         provider_defaults = {
#             "openai": "gpt-4o-mini",
#             "anthropic": "claude-3-5-sonnet-20241022",
#             "gemini": "gemini-2.0-flash",
#         }

#         return (
#             provider_models.get(provider) or
#             self.LLM_MODEL or
#             provider_defaults.get(provider, "unknown")
#         )

#     def _create_single_provider(self, provider_name: str):
#         """Create a single VLM provider instance."""
#         model = self.get_model_for_provider(provider_name)

#         if provider_name == "openai":
#             from ai.providers.openai import OpenAIVLM
#             return OpenAIVLM(model=model)
#         elif provider_name == "anthropic":
#             from ai.providers.anthropic import AnthropicVLM
#             return AnthropicVLM(model=model)
#         elif provider_name == "gemini":
#             from ai.providers.google import GeminiVLM
#             return GeminiVLM(model=model)
#         else:
#             raise ValueError(f"Unknown provider: {provider_name}")

#     def get_vlm_provider(self):
#         """Create and return VLM provider with optional failover."""
#         available = self.get_available_providers()

#         if not available:
#             return None

#         if not self.FAILOVER_ENABLED:
#             logger.info("Failover disabled - using default single provider")
#             return None

#         if len(available) == 1:
#             logger.info(f"Failover enabled but only 1 provider available: {available[0]}")
#             return self._create_single_provider(available[0])

#         # Multiple providers - create all and wrap
#         providers = []
#         for provider_name in available:
#             try:
#                 providers.append(self._create_single_provider(provider_name))
#                 logger.info(f"Added {provider_name} to failover list")
#             except Exception as e:
#                 logger.warning(f"Failed to create {provider_name} provider: {e}")

#         if not providers:
#             return None

#         if len(providers) == 1:
#             return providers[0]

#         logger.info(f"Creating FailoverVLM with {len(providers)} providers: {available}")

#     return FailoverVLM(providers)
#     def get_failover_status_message(self) -> str:
#         """Get a human-readable status message about failover configuration."""
#         available = self.get_available_providers()

#         if not available:
#             return "⚠️ No VLM providers configured. Set at least one API key."

#         if self.FAILOVER_ENABLED:
#             if len(available) >= 2:
#                 models = [f"{p} ({self.get_model_for_provider(p)})" for p in available]
#                 return f"✅ FAILOVER ENABLED - Providers: {', '.join(models)}"
#             else:
#                 return f"⚠️ FAILOVER ENABLED but only 1 provider: {available[0]} (add more API keys for true failover)"
#         else:
#             if len(available) >= 2:
#                 return f"ℹ️ FAILOVER DISABLED - {len(available)} providers available. Set FAILOVER_ENABLED=true to enable."
#             else:
#                 return f"ℹ️ FAILOVER DISABLED - Using single provider: {available[0]}"


# _settings_instance = None


# def get_settings() -> Settings:
#     global _settings_instance
#     if _settings_instance is None:
#         _settings_instance = Settings()

#         # Log failover status
#         import logging
#         logger = logging.getLogger(__name__)
#         logger.info(_settings_instance.get_failover_status_message())

#     return _settings_instance

































from typing import Any, List, Optional

from loguru import logger
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

    # ========== Provider-specific models ==========
    OPENAI_MODEL: Optional[str] = None
    ANTHROPIC_MODEL: Optional[str] = None
    GEMINI_MODEL: Optional[str] = None

    # ========== Failover toggle ==========
    FAILOVER_ENABLED: bool = Field(default=False)

    # Add after FAILOVER_ENABLED
    NUTRITION_FAILOVER_ENABLED: bool = Field(default=False)

    COST_TELEMETRY_ENABLED: bool = Field(default=True)
    COST_STORAGE_PATH: str = "costs.db"

    # Provider-specific settings
    OPENFOODFACTS_USER_AGENT: str = "AI-Food-Analyzer/1.0 (default@example.com)"

    CACHE_BACKEND: Optional[str] = None

    # For Redis
    REDIS_URL: Optional[str] = None

    # For JSON (existing)
    JSON_CACHE_MAX_SIZE_MB: Optional[int] = 100
    JSON_CACHE_BACKUP_COUNT: Optional[int] = 3

    NUTRITION_PROVIDER: str = "usda"
    USDA_API_KEY: Optional[str] = None
    OPENFOODFACTS_USER_AGENT: str = "AI-Food-Analyzer/1.0 (default@example.com)"

    HTTP_CACHE_ENABLED: bool = Field(default=True)
    HTTP_CACHE_TTL_SECONDS: int = Field(default=86400, ge=60, le=86400)

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    DATABASE_URL: Optional[str] = None
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
            raise ValueError(f"NUTRITION_PROVIDER must be one of {valid_providers}")
        return v.lower()

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        prefixes = ["postgresql://", "sqlite:///"]
        if not any(v.startswith(prefix) for prefix in prefixes):
            raise ValueError(f"DATABASE_URL must start with one of prefixes: {prefixes}")
        return v

    def model_post_init(self, _: Any) -> None:
        # Check 1: Offline mode with API keys
        if self.LLM_PROVIDER == "offline" and (
            self.ANTHROPIC_API_KEY or self.OPENAI_API_KEY or self.GOOGLE_API_KEY
        ):
            raise ValueError(
                "LLM_PROVIDER is set to offline but API keys are provided. "
                "Either set LLM_PROVIDER to 'openai', 'anthropic', or 'gemini', "
                "or remove the API keys."
            )

        # Check 2: Primary provider must have its API key
        if self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            raise ValueError("LLM_PROVIDER='anthropic' but ANTHROPIC_API_KEY is not set")
        if self.LLM_PROVIDER == "gemini" and not self.GOOGLE_API_KEY:
            raise ValueError("LLM_PROVIDER='gemini' but GOOGLE_API_KEY is not set")
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("LLM_PROVIDER='openai' but OPENAI_API_KEY is not set")

        # Check 3: Extra API keys (for failover) - warn but don't error
        if self.ANTHROPIC_API_KEY and self.LLM_PROVIDER != "anthropic":
            if self.FAILOVER_ENABLED:
                logger.info("Anthropic API key present for failover")
            else:
                raise ValueError(
                    "Anthropic API key provided but LLM_PROVIDER is not 'anthropic'. "
                    "Set FAILOVER_ENABLED=true to use it for failover, or remove the key."
                )

        if self.OPENAI_API_KEY and self.LLM_PROVIDER != "openai":
            if self.FAILOVER_ENABLED:
                logger.info("OpenAI API key present for failover")
            else:
                raise ValueError(
                    "OpenAI API key provided but LLM_PROVIDER is not 'openai'. "
                    "Set FAILOVER_ENABLED=true to use it for failover, or remove the key."
                )

        if self.GOOGLE_API_KEY and self.LLM_PROVIDER != "gemini":
            if self.FAILOVER_ENABLED:
                logger.info("Google API key present for failover")
            else:
                raise ValueError(
                    "Google API key provided but LLM_PROVIDER is not 'gemini'. "
                    "Set FAILOVER_ENABLED=true to use it for failover, or remove the key."
                )

        # Check 4: Nutrition provider validation
        if self.NUTRITION_PROVIDER == "usda" and not self.USDA_API_KEY:
            raise ValueError("NUTRITION_PROVIDER='usda' but USDA_API_KEY is not set")

        if self.NUTRITION_PROVIDER == "openfoodfacts" and not self.OPENFOODFACTS_USER_AGENT:
            raise ValueError(
                "OPENFOODFACTS_USER_AGENT required when NUTRITION_PROVIDER='openfoodfacts'"
            )

    # ========== FAILOVER METHODS ==========

    def get_available_providers(self) -> List[str]:
        """Return list of VLM providers that have API keys configured."""
        providers = []
        if self.OPENAI_API_KEY:
            providers.append("openai")
        if self.ANTHROPIC_API_KEY:
            providers.append("anthropic")
        if self.GOOGLE_API_KEY:
            providers.append("gemini")
        return providers

    def get_model_for_provider(self, provider: str) -> str:
        """Get the model name for a specific provider."""
        provider_models = {
            "openai": self.OPENAI_MODEL,
            "anthropic": self.ANTHROPIC_MODEL,
            "gemini": self.GEMINI_MODEL,
        }

        provider_defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-sonnet-20241022",
            "gemini": "gemini-2.0-flash",
        }

        return (
            provider_models.get(provider) or
            self.LLM_MODEL or
            provider_defaults.get(provider, "unknown")
        )

    def _create_single_provider(self, provider_name: str):
        """Create a single VLM provider instance."""
        model = self.get_model_for_provider(provider_name)

        if provider_name == "openai":
            from ai.providers.openai import OpenAIVLM
            return OpenAIVLM(model=model)
        elif provider_name == "anthropic":
            from ai.providers.anthropic import AnthropicVLM
            return AnthropicVLM(model=model)
        elif provider_name == "gemini":
            from ai.providers.google import GeminiVLM
            return GeminiVLM(model=model)
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

    def get_vlm_provider(self):
        """Create and return VLM provider with optional failover."""
        from src.services.failover_provider import FailoverVLM

        available = self.get_available_providers()

        if not available:
            return None

        if not self.FAILOVER_ENABLED:
            logger.info("Failover disabled - using default single provider")
            return None

        if len(available) == 1:
            logger.info(f"Failover enabled but only 1 provider available: {available[0]}")
            return self._create_single_provider(available[0])

        # Multiple providers - create all and wrap
        providers = []
        for provider_name in available:
            try:
                providers.append(self._create_single_provider(provider_name))
                logger.info(f"Added {provider_name} to failover list")
            except Exception as e:
                logger.warning(f"Failed to create {provider_name} provider: {e}")

        if not providers:
            return None

        if len(providers) == 1:
            return providers[0]

        logger.info(f"Creating FailoverVLM with {len(providers)} providers: {available}")
        return FailoverVLM(providers)

    def get_failover_status_message(self) -> str:
        """Get a human-readable status message about failover configuration."""
        available = self.get_available_providers()

        if not available:
            return "⚠️ No VLM providers configured. Set at least one API key."

        if self.FAILOVER_ENABLED:
            if len(available) >= 2:
                models = [f"{p} ({self.get_model_for_provider(p)})" for p in available]
                return f"✅ FAILOVER ENABLED - Providers: {', '.join(models)}"
            else:
                return f"⚠️ FAILOVER ENABLED but only 1 provider: {available[0]} (add more API keys for true failover)"
        else:
            if len(available) >= 2:
                return f"ℹ️ FAILOVER DISABLED - {len(available)} providers available. Set FAILOVER_ENABLED=true to enable."
            else:
                return f"ℹ️ FAILOVER DISABLED - Using single provider: {available[0]}"

    def get_available_nutrition_providers(self) -> List[str]:
        """Return list of nutrition providers that are configured."""
        providers = []
        if self.USDA_API_KEY:
            providers.append("usda")
        if self.OPENFOODFACTS_USER_AGENT:
            providers.append("openfoodfacts")
        return providers

    def get_nutrition_provider(self):
        """Create and return nutrition provider with optional failover."""
        from ai.nutrition import USDAProvider
        from src.services.failover_nutrition_provider import FailoverNutritionProvider
        from src.services.openfoodfacts_provider import OpenFoodFactsProvider

        available = self.get_available_nutrition_providers()

        if not available:
            raise ValueError("No nutrition providers configured")

        # Create individual providers
        providers = []
        for provider_name in available:
            try:
                if provider_name == "usda":
                    provider = USDAProvider(api_key=self.USDA_API_KEY)
                    providers.append(provider)
                    logger.info("Added USDA nutrition provider")
                elif provider_name == "openfoodfacts":
                    provider = OpenFoodFactsProvider(
                        user_agent=self.OPENFOODFACTS_USER_AGENT,
                        timeout=10.0
                    )
                    providers.append(provider)
                    logger.info("Added OpenFoodFacts nutrition provider")
            except Exception as e:
                logger.warning(f"Failed to create {provider_name} provider: {e}")

        if not providers:
            raise ValueError("No nutrition providers could be created")

        # If only one provider or failover disabled, return single provider
        if len(providers) == 1 or not self.NUTRITION_FAILOVER_ENABLED:
            logger.info(f"Using single nutrition provider: {type(providers[0]).__name__}")
            return providers[0]

        # Wrap with failover
        logger.info(f"Creating FailoverNutritionProvider with {len(providers)} providers")
        return FailoverNutritionProvider(providers)


_settings_instance = None


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
        logger.info(_settings_instance.get_failover_status_message())

    return _settings_instance
