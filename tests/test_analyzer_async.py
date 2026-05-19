import pytest
from src.core.analyzer import FoodAnalyzer
from ai.schemas import Ingredient, NutritionFacts

pytestmark = pytest.mark.asyncio


class TestFoodAnalyzerAsync:
    async def test_analyze_async_cache_hit(self, mocker):
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
        mock_ai_service = mocker.Mock()
        mock_nutrition = mocker.Mock()
        mock_nutrition.async_lookup = mocker.AsyncMock()
        mock_nutrition.async_lookup.side_effect = lambda name: {
            "rice": fake_facts_rice,
            "chicken": fake_facts_chicken,
        }[name]

        analyzer = FoodAnalyzer(
            ai_service=mock_ai_service,
            vlm_cache=mock_cache,
            nutrition_provider=mock_nutrition,
        )

        result = await analyzer.analyze_async("test.jpg")

        mock_ai_service.service_identify_ingredients.assert_not_called()
        assert result["ingredients"] == fake_ingredients
        assert mock_nutrition.async_lookup.call_count == 2

    async def test_analyze_async_cache_miss(self, mocker):
        fake_ingredients = [
            Ingredient(name="rice", estimated_grams=100.0, confidence=0.7),
        ]
        fake_facts_rice = NutritionFacts(
            name="rice",
            kcal_per_100g=130,
            protein_g_per_100g=2.7,
            carbs_g_per_100g=28,
            fat_g_per_100g=0.3,
            source="test",
        )

        mock_cache = mocker.Mock()
        mock_cache.get.return_value = None
        mock_ai_service = mocker.Mock()
        mock_ai_service.service_identify_ingredients.return_value = fake_ingredients
        mock_nutrition = mocker.Mock()
        mock_nutrition.async_lookup = mocker.AsyncMock()
        mock_nutrition.async_lookup.return_value = fake_facts_rice

        analyzer = FoodAnalyzer(
            ai_service=mock_ai_service,
            vlm_cache=mock_cache,
            nutrition_provider=mock_nutrition,
        )

        result = await analyzer.analyze_async("test.jpg")

        mock_ai_service.service_identify_ingredients.assert_called_once_with("test.jpg")
        mock_cache.set.assert_called_once()
        assert result["ingredients"] == fake_ingredients
