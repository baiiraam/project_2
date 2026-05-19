from src.services.ai_service import AIService
from src.services.vlm_cache import VLMCache
from src.services.nutrition_cache import CachedNutritionProvider
from src.config import Settings
from ai import compute_totals
from ai.nutrition import get_nutrition_provider
from typing import Optional, Dict
import logging
from src.concurrency.pipeline import fetch_all_nutrition_async
from src.storage.database import Database
from src.services.openfoodfacts_provider import OpenFoodFactsProvider
from src.services.mock_nutrition_provider import MockNutritionProvider


class FoodAnalyzer:
    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        vlm_cache: Optional[VLMCache] = None,
        nutrition_provider: Optional[CachedNutritionProvider] = None,
    ):
        settings = Settings()
        ttl_seconds_from_settings = settings.NUTRITION_CACHE_TTL_SECONDS
        self.logger = logging.getLogger(__name__)
        self.ai_service = ai_service if ai_service is not None else AIService()
        self.vlm_cache = (
            vlm_cache
            if vlm_cache is not None
            else VLMCache(
                ttl_seconds=ttl_seconds_from_settings, cache_file="vlm_cache.json"
            )
        )
        if nutrition_provider is not None:
            self.cached_nutrition_provider = nutrition_provider
        else:
            if settings.NUTRITION_PROVIDER == "mock":
                real_provider = MockNutritionProvider()
            elif settings.NUTRITION_PROVIDER == "openfoodfacts":
                real_provider = OpenFoodFactsProvider(
                    user_agent=settings.OPENFOODFACTS_USER_AGENT
                )
            else:
                real_provider = get_nutrition_provider()

            self.cached_nutrition_provider = CachedNutritionProvider(
                inner_provider=real_provider,
                ttl_seconds=settings.NUTRITION_CACHE_TTL_SECONDS,
                cache_file="nutrition_cache.json",  # Add disk persistence
                maxsize=128,
            )
        self.logger.info("FoodAnalyzer initialized")

    # Sync method (existing, unchanged)
    def analyze(self, image_path: str) -> Dict:
        image_hash = self.vlm_cache.get_hash(image_path)
        res = self.vlm_cache.get(image_hash)
        if res is None:
            ingredients = self.ai_service.service_identify_ingredients(image_path)
            self.vlm_cache.set(image_hash, ingredients)
        else:
            ingredients = res
        facts_by_name = {}
        for ingredient in ingredients:
            facts = self.cached_nutrition_provider.lookup(ingredient.name)
            facts_by_name[ingredient.name] = facts
        totals = compute_totals(ingredients=ingredients, facts_by_name=facts_by_name)
        return {
            "ingredients": ingredients,
            "nutrition_per_ingredient": facts_by_name,
            "totals": totals,
        }

    # Async method (new)
    async def analyze_async(self, image_path: str) -> Dict:
        image_hash = self.vlm_cache.get_hash(image_path)
        res = self.vlm_cache.get(image_hash)
        if res is None:
            ingredients = self.ai_service.service_identify_ingredients(image_path)
            self.vlm_cache.set(image_hash, ingredients)
        else:
            ingredients = res

        facts_by_name = await fetch_all_nutrition_async(
            ingredients, self.cached_nutrition_provider
        )

        totals = compute_totals(ingredients=ingredients, facts_by_name=facts_by_name)
        try:
            await Database.save(
                image_path=image_path,
                ingredients=[ing.model_dump() for ing in ingredients],
                totals=totals.model_dump(),
                meal_recognized=len(ingredients) > 0,
            )
        except Exception as e:
            self.logger.warning(f"Database save failed: {e}")

        return {
            "ingredients": ingredients,
            "nutrition_per_ingredient": facts_by_name,
            "totals": totals,
        }
