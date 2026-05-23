"""Failover provider for nutrition lookups."""

from typing import List, Optional

from loguru import logger

from ai import NutritionFacts, NutritionProvider
from ai.providers.base import ProviderError


class FailoverNutritionProvider(NutritionProvider):
    """Wraps multiple nutrition providers and fails over to the next on error."""

    def __init__(self, providers: List[NutritionProvider]) -> None:
        if not providers:
            raise ValueError("At least one provider required")
        self.providers = providers
        self._active_index = 0
        logger.info(f"FailoverNutritionProvider initialized with {len(providers)} providers")

    def lookup(self, ingredient_name: str) -> NutritionFacts:
        """Try each provider in order until one succeeds."""
        last_error: Optional[Exception] = None

        for i, provider in enumerate(self.providers):
            try:
                logger.info(
                    f"🔄 Trying nutrition provider {i + 1}/{len(self.providers)}: "
                    f"{type(provider).__name__} for '{ingredient_name}'"
                )
                result = provider.lookup(ingredient_name)
                self._active_index = i
                logger.info(
                    f"✅ Success with nutrition provider: {type(provider).__name__} "
                    f"for '{ingredient_name}' ({result.kcal_per_100g} kcal/100g)"
                )
                return result
            except (ProviderError, ConnectionError, TimeoutError, ValueError) as e:
                logger.warning(
                    f"❌ Nutrition provider {type(provider).__name__} failed for "
                    f"'{ingredient_name}': {str(e)}"
                )
                last_error = e
                continue

        # If all providers fail, return zero-value NutritionFacts as fallback
        logger.error(
            f"All nutrition providers failed for '{ingredient_name}'. "
            f"Last error: {last_error}. Returning zero-value facts."
        )
        return NutritionFacts(
            name=ingredient_name,
            kcal_per_100g=0.0,
            protein_g_per_100g=0.0,
            carbs_g_per_100g=0.0,
            fat_g_per_100g=0.0,
            source="failover_fallback",
        )

    async def async_lookup(self, ingredient_name: str) -> NutritionFacts:
        """Async version - runs sync lookup in executor."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.lookup, ingredient_name)
