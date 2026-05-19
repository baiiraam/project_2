from src.config import Settings
import pytest


# def test_llm_provider_default_is_present():
#     settings = Settings()
#     assert settings.LLM_PROVIDER == "offline"


def test_llm_provider_offline_rejects_api_keys():
    with pytest.raises(
        ValueError,
        match="LLM_PROVIDER is set to offline but API keys are provided for models. You should either set LLM_PROVIDER to the appropriate model or remove the API keys.",
    ):
        Settings(LLM_PROVIDER="offline", ANTHROPIC_API_KEY="test-key")


def test_llm_provider_anthropic_requires_key():
    with pytest.raises(ValueError):
        Settings(LLM_PROVIDER="anthropic")


# def test_1():
#     settings = Settings()
#     assert settings.LLM_MODEL is None


# def test_2():
#     settings = Settings()
#     assert settings.ANTHROPIC_API_KEY is None


# def test_3():
#     settings = Settings()
#     assert settings.OPENAI_API_KEY is None


# def test_4():
#     settings = Settings()
#     assert settings.GOOGLE_API_KEY is None


# def test_5():
#     settings = Settings()
#     assert settings.NUTRITION_PROVIDER == "usda"


# needs review
# def test_6():
#     settings = Settings()
#     assert isinstance(settings., str)


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
