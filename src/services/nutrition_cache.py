"""Nutrition cache with persistent storage."""

from loguru import logger

from ai import NutritionFacts, NutritionProvider
from ai.providers.base import ProviderError
from src.services.cache_factory import create_cache


class CachedNutritionProvider(NutritionProvider):
    """Nutrition provider with persistent cache."""

    def __init__(
        self,
        inner_provider: NutritionProvider,
        ttl_seconds: float = 86400.0,
        maxsize: int = 128,
    ):
        self._inner = inner_provider
        self.ttl = ttl_seconds
        self._cache = create_cache()
        logger.info(
            f"Nutrition cache initialized with {self._cache.get_stats()['type']} backend"
        )

    def _normalize_key(self, name: str) -> str:
        return f"nutrition:{name.lower().strip()}"

    def lookup(self, ingredient_name: str) -> NutritionFacts:
        """Look up nutrition facts with persistent caching."""
        key = self._normalize_key(ingredient_name)

        # Try cache first
        cached = self._cache.get(key)
        if cached:
            logger.info(f"Nutrition cache HIT: {ingredient_name}")
            return NutritionFacts(
                name=cached["name"],
                kcal_per_100g=cached["kcal_per_100g"],
                protein_g_per_100g=cached["protein_g_per_100g"],
                carbs_g_per_100g=cached["carbs_g_per_100g"],
                fat_g_per_100g=cached["fat_g_per_100g"],
                source=cached.get("source", "cached"),
            )

        # Cache miss - call API
        logger.info(f"Nutrition cache MISS: {ingredient_name}")
        try:
            facts = self._inner.lookup(ingredient_name)

            # Store in cache
            self._cache.set(
                key,
                {
                    "name": facts.name,
                    "kcal_per_100g": facts.kcal_per_100g,
                    "protein_g_per_100g": facts.protein_g_per_100g,
                    "carbs_g_per_100g": facts.carbs_g_per_100g,
                    "fat_g_per_100g": facts.fat_g_per_100g,
                    "source": facts.source,
                },
                self.ttl,
            )

            return facts
        except ProviderError as e:
            logger.error(f"Failed to fetch nutrition for {ingredient_name}: {e}")
            raise

    async def async_lookup(self, ingredient_name: str) -> NutritionFacts:
        """Async version with persistent caching."""
        key = self._normalize_key(ingredient_name)

        # Try cache first
        cached = self._cache.get(key)
        if cached:
            logger.info(f"Nutrition cache HIT: {ingredient_name}")
            return NutritionFacts(
                name=cached["name"],
                kcal_per_100g=cached["kcal_per_100g"],
                protein_g_per_100g=cached["protein_g_per_100g"],
                carbs_g_per_100g=cached["carbs_g_per_100g"],
                fat_g_per_100g=cached["fat_g_per_100g"],
                source=cached.get("source", "cached"),
            )

        # Cache miss - call API
        logger.info(f"Nutrition cache MISS: {ingredient_name}")
        try:
            import asyncio

            facts = await asyncio.to_thread(self._inner.lookup, ingredient_name)

            # Store in cache
            self._cache.set(
                key,
                {
                    "name": facts.name,
                    "kcal_per_100g": facts.kcal_per_100g,
                    "protein_g_per_100g": facts.protein_g_per_100g,
                    "carbs_g_per_100g": facts.carbs_g_per_100g,
                    "fat_g_per_100g": facts.fat_g_per_100g,
                    "source": facts.source,
                },
                self.ttl,
            )

            return facts
        except ProviderError as e:
            logger.error(f"Failed to fetch nutrition for {ingredient_name}: {e}")
            return NutritionFacts(
                name=ingredient_name,
                kcal_per_100g=0,
                protein_g_per_100g=0,
                carbs_g_per_100g=0,
                fat_g_per_100g=0,
                source="error",
            )

    def clear_cache(self):
        """Clear entire cache."""
        self._cache.clear()
        logger.info("Nutrition cache cleared")

    def get_stats(self):
        """Get cache statistics."""
        return self._cache.get_stats()
