import pytest

from src.config import Settings



def test_llm_provider_anthropic_requires_key():
    with pytest.raises(ValueError):
        Settings(LLM_PROVIDER="anthropic")


def test_7():
    settings = Settings()
    assert settings.LOG_LEVEL == "INFO"


def test_8():
    settings = Settings()
    assert isinstance(settings.DATABASE_URL, str)


def test_9():
    settings = Settings()
    assert settings.NUTRITION_CACHE_TTL_SECONDS == 86400


def test_10():
    settings = Settings()
    assert isinstance(settings.MAX_IMAGE_SIZE_MB, int)


def test_11():
    settings = Settings()
    assert settings.HTTP_PORT == 8000
