# nutrition cache, vlm cache, and ai service
import pytest

import time

from src.services.nutrition_cache import CachedNutritionProvider
from src.services.vlm_cache import VLMCache
from src.services.ai_service import AIService

from ai.nutrition import NutritionFacts
from ai.schemas import Ingredient
from ai.providers.base import ProviderError

# Also check that AIService retries when network-related or some exceptions are raised


# nutrition cache
def test_CachedNutritionProvider_caches_lookups(mocker):
    # Mock file operations to prevent loading from disk
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("builtins.open", mocker.mock_open())

    mock_fetcher = mocker.Mock()
    fake_facts = NutritionFacts(
        name="rice",
        kcal_per_100g=10.0,
        protein_g_per_100g=10.0,
        carbs_g_per_100g=10.0,
        fat_g_per_100g=10.0,
    )
    mock_fetcher.lookup.return_value = fake_facts
    cnp = CachedNutritionProvider(inner_provider=mock_fetcher)

    res1 = cnp.lookup("rice")
    res2 = cnp.lookup("rice")

    assert res1 == res2 == fake_facts
    assert mock_fetcher.lookup.call_count == 1


def test_CachedNutritionProvider_normalizes_input(mocker):
    # Mock file operations to prevent loading from disk
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("builtins.open", mocker.mock_open())

    mock_fetcher = mocker.Mock()
    fake_facts = NutritionFacts(
        name="rice",
        kcal_per_100g=10.0,
        protein_g_per_100g=10.0,
        carbs_g_per_100g=10.0,
        fat_g_per_100g=10.0,
    )
    mock_fetcher.lookup.return_value = fake_facts
    cnp = CachedNutritionProvider(inner_provider=mock_fetcher)

    cnp.lookup("rice")
    cnp.lookup("Rice")
    cnp.lookup("RICE")
    cnp.lookup("   rice   ")

    mock_fetcher.lookup.assert_called_once_with("rice")


def test_CachedNutritionProvider_implements_ttl(mocker):
    mock_fetcher = mocker.Mock()
    fake_facts = NutritionFacts(
        name="rice",
        kcal_per_100g=10.0,
        protein_g_per_100g=10.0,
        carbs_g_per_100g=10.0,
        fat_g_per_100g=10.0,
    )
    mock_fetcher.lookup.return_value = fake_facts
    cnp = CachedNutritionProvider(inner_provider=mock_fetcher, ttl_seconds=0.1)
    res1 = cnp.lookup("rice")
    time.sleep(0.2)
    res2 = cnp.lookup("rice")
    assert mock_fetcher.lookup.call_count == 2
    assert res1 == res2 == fake_facts


def test_VLMCache_get_and_set():
    ingredient_list = [
        Ingredient(name="rice", estimated_grams=120.0, confidence=0.7),
        Ingredient(name="chicken", estimated_grams=150.0, confidence=0.8),
    ]
    vlm_cache = VLMCache()
    vlm_cache.set(image_path="test.jpg", ingredients=ingredient_list)
    res = vlm_cache.get(image_path="test.jpg")
    assert res == ingredient_list


def test_VLMCache_get_missing():
    ingredient_list = [
        Ingredient(name="rice", estimated_grams=120.0, confidence=0.7),
        Ingredient(name="chicken", estimated_grams=150.0, confidence=0.8),
    ]
    vlm_cache = VLMCache()
    vlm_cache.set(image_path="test.jpg", ingredients=ingredient_list)
    assert vlm_cache.get("abab.jpg") is None


def test_VLMCache_has():
    ingredient_list = [
        Ingredient(name="rice", estimated_grams=120.0, confidence=0.7),
        Ingredient(name="chicken", estimated_grams=150.0, confidence=0.8),
    ]
    vlm_cache = VLMCache()
    vlm_cache.set(image_path="test.jpg", ingredients=ingredient_list)
    assert vlm_cache.has("test.jpg")
    assert vlm_cache.has("abab.jpg") is False


def test_VLMCache_clear():
    ingredient_list = [
        Ingredient(name="rice", estimated_grams=120.0, confidence=0.7),
        Ingredient(name="chicken", estimated_grams=150.0, confidence=0.8),
    ]
    vlm_cache = VLMCache()
    vlm_cache.set(image_path="test.jpg", ingredients=ingredient_list)
    vlm_cache.clear()
    assert vlm_cache.has("test.jpg") is False


def test_AIService__service_identify_ingredients_no_retry_when_call_succeeds(mocker):
    mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
    fake_facts = [
        Ingredient(name="rice", estimated_grams=100.0, confidence=0.8),
        Ingredient(name="chicken", estimated_grams=110.0, confidence=0.7),
    ]
    mock_identify.return_value = fake_facts
    smth = AIService()
    res = smth.service_identify_ingredients("test.jpg")
    mock_identify.assert_called_once_with("test.jpg")
    assert res == fake_facts


def test_AIService__service_identify_ingredients_retries_on_failure(mocker):
    mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
    fake_facts = [
        Ingredient(name="rice", estimated_grams=100.0, confidence=0.8),
        Ingredient(name="chicken", estimated_grams=110.0, confidence=0.7),
    ]
    mock_identify.side_effect = [ProviderError(), ProviderError(), fake_facts]
    smth = AIService()
    res = smth.service_identify_ingredients("test.jpg")
    assert mock_identify.call_count == 3
    assert res == fake_facts


def test_AIService__service_identify_ingredients_no_retry_for_FileNotFoundError(mocker):
    mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
    mock_identify.side_effect = FileNotFoundError()
    smth = AIService()
    with pytest.raises(FileNotFoundError):
        smth.service_identify_ingredients("test.jpg")
    mock_identify.assert_called_once_with("test.jpg")


def test_AIService__service_identify_ingredients_max_retries_exceeded(mocker):
    mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
    mock_identify.side_effect = ProviderError()
    smth = AIService()
    with pytest.raises(ProviderError):
        smth.service_identify_ingredients("test.jpg")
    assert mock_identify.call_count == 3


def test_AIService__service_identify_ingredients_retry_on_ConnectionError(mocker):
    mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
    fake_facts = [
        Ingredient(name="rice", estimated_grams=90.0, confidence=0.6),
        Ingredient(name="chicken", estimated_grams=100.0, confidence=0.7),
    ]
    mock_identify.side_effect = [ConnectionError(), ConnectionError(), fake_facts]
    smth = AIService()
    res = smth.service_identify_ingredients("test.jpg")
    assert mock_identify.call_count == 3
    assert res == fake_facts
