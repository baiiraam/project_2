# import pytest
# from unittest.mock import Mock, MagicMock
from ai.schemas import Ingredient, NutritionFacts
from src.core.analyzer import FoodAnalyzer

# testing core/analyzer.py
# when image is cached, analyzer doesn't call AI Service.


def test_analyzer_doesnt_call_ai_service_when_image_is_cached(mocker):
    fake_ingredients = [
        Ingredient(name="rice", estimated_grams=100.0, confidence=0.7),
        Ingredient(name="chicken", estimated_grams=110.0, confidence=0.7),
    ]
    fake_facts_rice = NutritionFacts(
        name="rice",
        kcal_per_100g=130,
        protein_g_per_100g=2.7,
        carbs_g_per_100g=28,
        fat_g_per_100g=0.3,
        source="test",
    )
    fake_facts_chicken = NutritionFacts(
        name="chicken",
        kcal_per_100g=165,
        protein_g_per_100g=31,
        carbs_g_per_100g=0,
        fat_g_per_100g=3.6,
        source="test",
    )
    mock_cache = mocker.Mock()
    mock_cache.get.return_value = fake_ingredients
    mock_cache.get_hash.return_value = "test_hash_123"
    mock_ai_service = mocker.Mock()
    mock_nutrition = mocker.Mock()
    mock_nutrition.lookup.side_effect = lambda name: {
        "rice": fake_facts_rice,
        "chicken": fake_facts_chicken,
    }[name]
    analyzer = FoodAnalyzer(
        ai_service=mock_ai_service,
        vlm_cache=mock_cache,
        nutrition_provider=mock_nutrition,
    )
    res = analyzer.analyze("test.jpg")

    # Assertions
    mock_ai_service.service_identify_ingredients.assert_not_called()
    mock_cache.get_hash.assert_called_once_with("test.jpg")
    mock_cache.get.assert_called_once_with("test_hash_123")  # Uses hash, not path
    assert mock_nutrition.lookup.call_count == 2
    assert res["ingredients"] == fake_ingredients


def test_analyzer_calls_ai_service_when_image_is_not_cached_and_then_caches_the_image(
    mocker,
):
    fake_ingredients = [
        Ingredient(name="rice", estimated_grams=100.0, confidence=0.7),
        Ingredient(name="chicken", estimated_grams=110.0, confidence=0.7),
    ]
    fake_facts_rice = NutritionFacts(
        name="rice",
        kcal_per_100g=130,
        protein_g_per_100g=2.7,
        carbs_g_per_100g=28,
        fat_g_per_100g=0.3,
        source="test",
    )
    fake_facts_chicken = NutritionFacts(
        name="chicken",
        kcal_per_100g=165,
        protein_g_per_100g=31,
        carbs_g_per_100g=0,
        fat_g_per_100g=3.6,
        source="test",
    )
    mock_cache = mocker.Mock()
    mock_cache.get.return_value = None
    mock_cache.get_hash.return_value = "test_hash_123"
    mock_ai_service = mocker.Mock()
    mock_ai_service.service_identify_ingredients.return_value = fake_ingredients
    mock_nutrition = mocker.Mock()
    mock_nutrition.lookup.side_effect = lambda name: {
        "rice": fake_facts_rice,
        "chicken": fake_facts_chicken,
    }[name]
    analyzer = FoodAnalyzer(
        ai_service=mock_ai_service,
        vlm_cache=mock_cache,
        nutrition_provider=mock_nutrition,
    )
    res = analyzer.analyze("test.jpg")

    # Assertions
    mock_ai_service.service_identify_ingredients.assert_called_once_with("test.jpg")
    mock_cache.get_hash.assert_called_once_with("test.jpg")
    mock_cache.get.assert_called_once_with("test_hash_123")
    mock_cache.set.assert_called_once_with(
        "test_hash_123", fake_ingredients
    )  # Uses hash
    assert mock_nutrition.lookup.call_count == 2
    assert res["ingredients"] == fake_ingredients


def test_analyzer_handles_empty_meal_result(mocker):
    fake_ingredients = []
    mock_cache = mocker.Mock()
    mock_cache.get.return_value = None
    mock_cache.get_hash.return_value = "test_hash_123"
    mock_ai_service = mocker.Mock()
    mock_ai_service.service_identify_ingredients.return_value = fake_ingredients
    mock_nutrition_provider = mocker.Mock()
    analyzer = FoodAnalyzer(
        ai_service=mock_ai_service,
        vlm_cache=mock_cache,
        nutrition_provider=mock_nutrition_provider,
    )
    res = analyzer.analyze("test.jpg")

    # Assertions
    mock_ai_service.service_identify_ingredients.assert_called_once_with("test.jpg")
    mock_cache.get_hash.assert_called_once_with("test.jpg")
    mock_cache.get.assert_called_once_with("test_hash_123")
    mock_cache.set.assert_called_once_with("test_hash_123", [])
    mock_nutrition_provider.lookup.assert_not_called()
    assert res["ingredients"] == []
    assert res["totals"].kcal == 0
    assert res["totals"].protein_g == 0
    assert res["totals"].carbs_g == 0
    assert res["totals"].fat_g == 0
