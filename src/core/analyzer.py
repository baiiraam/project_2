# # src/core/analyzer.py

# from typing import Dict, Optional

# from loguru import logger

# from ai import compute_totals
# from ai.nutrition import NutritionProvider, get_nutrition_provider
# from src.concurrency.pipeline import fetch_all_nutrition_async
# from src.config import get_settings
# from src.services.ai_service import AIService
# from src.services.mock_nutrition_provider import MockNutritionProvider
# from src.services.nutrition_cache import CachedNutritionProvider
# from src.services.openfoodfacts_provider import OpenFoodFactsProvider
# from src.services.vlm_cache import VLMCache
# from src.storage.database import Database


# class FoodAnalyzer:
#     def __init__(
#         self,
#         ai_service: Optional[AIService] = None,
#         vlm_cache: Optional[VLMCache] = None,
#         nutrition_provider: Optional[CachedNutritionProvider] = None,
#     ):
#         settings = get_settings()
#         ttl_seconds_from_settings = settings.NUTRITION_CACHE_TTL_SECONDS
#         self.ai_service = ai_service if ai_service is not None else AIService()
#         self.vlm_cache = (
#             vlm_cache
#             if vlm_cache is not None
#             else VLMCache(ttl_seconds=ttl_seconds_from_settings)
#         )

#         if nutrition_provider is not None:
#             self.cached_nutrition_provider = nutrition_provider
#         else:
#             # Get nutrition provider from settings (handles failover automatically)
#             # Pass inner_provider=None so CachedNutritionProvider gets it from settings
#             self.cached_nutrition_provider = CachedNutritionProvider(
#                 inner_provider=None,  # ← This tells it to use settings.get_nutrition_provider()
#                 ttl_seconds=int(settings.NUTRITION_CACHE_TTL_SECONDS),
#                 maxsize=128,
#             )

#         logger.info("FoodAnalyzer initialized")

#     # Add a method to get cache (lazy initialization)
#     def _get_cache(self):
#         """Lazy initialization of Redis cache."""
#         if not hasattr(self, "_cache"):
#             from src.services.cache_factory import create_cache

#             self._cache = create_cache()
#         return self._cache

#     def analyze(self, image_path: str) -> Dict:
#         image_hash = self.vlm_cache.get_hash(image_path)
#         res = self.vlm_cache.get(image_hash)
#         if res is None:
#             ingredients = self.ai_service.service_identify_ingredients(image_path)
#             self.vlm_cache.set(image_hash, ingredients)
#         else:
#             ingredients = res
#         facts_by_name = {}
#         for ingredient in ingredients:
#             facts = self.cached_nutrition_provider.lookup(ingredient.name)
#             facts_by_name[ingredient.name] = facts
#         totals = compute_totals(ingredients=ingredients, facts_by_name=facts_by_name)
#         return {
#             "ingredients": ingredients,
#             "nutrition_per_ingredient": facts_by_name,
#             "totals": totals,
#         }

#     async def analyze_async(self, image_path: str) -> Dict:
#         image_hash = await self.vlm_cache.get_hash_async(image_path)
#         res = self.vlm_cache.get(image_hash)
#         if res is None:
#             ingredients = await self.ai_service.service_identify_ingredients_async(
#                 image_path
#             )
#             self.vlm_cache.set(image_hash, ingredients)
#         else:
#             ingredients = res

#         facts_by_name = await fetch_all_nutrition_async(
#             ingredients, self.cached_nutrition_provider
#         )

#         totals = compute_totals(ingredients=ingredients, facts_by_name=facts_by_name)

#         # Run sync database save in thread pool to avoid blocking
#         try:
#             await Database.save(
#                 image_path,
#                 [ing.model_dump() for ing in ingredients],
#                 totals.model_dump(),
#                 len(ingredients) > 0,
#             )
#         except Exception as e:
#             logger.warning(f"Database save failed: {e}")

#         return {
#             "ingredients": ingredients,
#             "nutrition_per_ingredient": facts_by_name,
#             "totals": totals,
#         }









































# src/core/analyzer.py

from typing import Dict, Optional

from loguru import logger

from ai import compute_totals
from src.concurrency.pipeline import fetch_all_nutrition_async
from src.config import get_settings
from src.services.ai_service import AIService
from src.services.nutrition_cache import CachedNutritionProvider
from src.services.vlm_cache import VLMCache
from src.storage.database import Database


class FoodAnalyzer:
    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        vlm_cache: Optional[VLMCache] = None,
        nutrition_provider: Optional[CachedNutritionProvider] = None,
    ):
        settings = get_settings()
        ttl_seconds_from_settings = settings.NUTRITION_CACHE_TTL_SECONDS
        self.ai_service = ai_service if ai_service is not None else AIService()
        self.vlm_cache = (
            vlm_cache
            if vlm_cache is not None
            else VLMCache(ttl_seconds=ttl_seconds_from_settings)
        )

        if nutrition_provider is not None:
            self.cached_nutrition_provider = nutrition_provider
        else:
            # Get nutrition provider from settings (handles failover automatically)
            # Pass inner_provider=None so CachedNutritionProvider gets it from settings
            self.cached_nutrition_provider = CachedNutritionProvider(
                inner_provider=None,  # ← Tells it to use settings.get_nutrition_provider()
                ttl_seconds=int(settings.NUTRITION_CACHE_TTL_SECONDS),
                maxsize=128,
            )

        logger.info("FoodAnalyzer initialized")

    # Add a method to get cache (lazy initialization)
    def _get_cache(self):
        """Lazy initialization of Redis cache."""
        if not hasattr(self, "_cache"):
            from src.services.cache_factory import create_cache

            self._cache = create_cache()
        return self._cache

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

    async def analyze_async(self, image_path: str) -> Dict:
        image_hash = await self.vlm_cache.get_hash_async(image_path)
        res = self.vlm_cache.get(image_hash)
        if res is None:
            ingredients = await self.ai_service.service_identify_ingredients_async(
                image_path
            )
            self.vlm_cache.set(image_hash, ingredients)
        else:
            ingredients = res

        facts_by_name = await fetch_all_nutrition_async(
            ingredients, self.cached_nutrition_provider
        )

        totals = compute_totals(ingredients=ingredients, facts_by_name=facts_by_name)

        # Run sync database save in thread pool to avoid blocking
        try:
            await Database.save(
                image_path,
                [ing.model_dump() for ing in ingredients],
                totals.model_dump(),
                len(ingredients) > 0,
            )
        except Exception as e:
            logger.warning(f"Database save failed: {e}")

        return {
            "ingredients": ingredients,
            "nutrition_per_ingredient": facts_by_name,
            "totals": totals,
        }
