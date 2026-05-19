import json
import os
import asyncio
import logging
from cachetools import TTLCache
from ai import NutritionFacts, NutritionProvider
from ai.providers.base import ProviderError
from datetime import datetime

logger = logging.getLogger(__name__)


class CachedNutritionProvider(NutritionProvider):
    """Nutrition provider with both memory and disk persistence."""

    def __init__(
        self,
        inner_provider: NutritionProvider,
        ttl_seconds: float = 86400.0,
        cache_file: str = "nutrition_cache.json",
        maxsize: int = 128,
    ):
        self._inner = inner_provider
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self.cache_file = cache_file
        self.logger = logging.getLogger(__name__)

        # Load existing cache from disk
        self._load_from_disk()

    def _load_from_disk(self):
        """Load cached entries from JSON file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)

                    # Check for expired entries based on timestamp
                    current_time = datetime.now().timestamp()
                    loaded_count = 0

                    for key, value in data.items():
                        # Check if entry has timestamp and isn't expired
                        if "timestamp" in value:
                            age = current_time - value["timestamp"]
                            if age <= self._cache.ttl:
                                # Reconstruct NutritionFacts from dict
                                facts = NutritionFacts(
                                    name=value["name"],
                                    kcal_per_100g=value["kcal_per_100g"],
                                    protein_g_per_100g=value["protein_g_per_100g"],
                                    carbs_g_per_100g=value["carbs_g_per_100g"],
                                    fat_g_per_100g=value["fat_g_per_100g"],
                                    source=value.get("source", "cached"),
                                )
                                self._cache[key] = facts
                                loaded_count += 1
                        else:
                            # Old format without timestamp - load anyway
                            facts = NutritionFacts(
                                name=value["name"],
                                kcal_per_100g=value["kcal_per_100g"],
                                protein_g_per_100g=value["protein_g_per_100g"],
                                carbs_g_per_100g=value["carbs_g_per_100g"],
                                fat_g_per_100g=value["fat_g_per_100g"],
                                source=value.get("source", "cached"),
                            )
                            self._cache[key] = facts
                            loaded_count += 1

                    self.logger.info(
                        f"Loaded {loaded_count} entries from {self.cache_file}"
                    )

            except Exception as e:
                self.logger.warning(f"Failed to load cache from {self.cache_file}: {e}")

    def _save_to_disk(self):
        """Save cache entries to JSON file with timestamps."""
        try:
            data = {}
            current_time = datetime.now().timestamp()

            for key, facts in self._cache.items():
                data[key] = {
                    "name": facts.name,
                    "kcal_per_100g": facts.kcal_per_100g,
                    "protein_g_per_100g": facts.protein_g_per_100g,
                    "carbs_g_per_100g": facts.carbs_g_per_100g,
                    "fat_g_per_100g": facts.fat_g_per_100g,
                    "source": facts.source,
                    "timestamp": current_time,  # Add timestamp for expiration checking
                }

            # Write atomically using temp file
            temp_file = f"{self.cache_file}.tmp"
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)

            # Replace original with temp file
            os.replace(temp_file, self.cache_file)

            self.logger.debug(f"Saved {len(self._cache)} entries to {self.cache_file}")

        except Exception as e:
            self.logger.warning(f"Failed to save cache to {self.cache_file}: {e}")

    def lookup(self, ingredient_name: str) -> NutritionFacts:
        """Look up nutrition facts with memory + disk caching."""
        normalized = ingredient_name.lower().strip()

        # Check memory cache first
        if normalized in self._cache:
            self.logger.info(f"CACHE HIT (memory): {ingredient_name}")
            return self._cache[normalized]

        # Cache miss - call inner provider with normalized name
        self.logger.info(f"CACHE MISS: {ingredient_name} - calling API")

        try:
            # FIX: Use normalized name here
            facts = self._inner.lookup(normalized)  # Changed from ingredient_name

            # Store in memory cache
            self._cache[normalized] = facts

            # Persist to disk
            self._save_to_disk()

            return facts

        except ProviderError as e:
            self.logger.error(f"Failed to fetch nutrition for {ingredient_name}: {e}")
            raise

    async def async_lookup(self, ingredient_name: str) -> NutritionFacts:
        """Async version with memory + disk caching."""
        normalized = ingredient_name.lower().strip()

        # Check memory cache first
        if normalized in self._cache:
            self.logger.info(f"CACHE HIT (memory): {ingredient_name}")
            return self._cache[normalized]

        # Cache miss - call inner provider
        self.logger.info(f"CACHE MISS: {ingredient_name} - calling API")

        try:
            # FIX: Use normalized name here too
            facts = await asyncio.to_thread(self._inner.lookup, normalized)  # Changed

            # Store in memory cache
            self._cache[normalized] = facts

            # Persist to disk (run in thread to avoid blocking)
            await asyncio.to_thread(self._save_to_disk)

            return facts

        except ProviderError as e:
            self.logger.error(f"Failed to fetch nutrition for {ingredient_name}: {e}")
            # Return zero facts as fallback instead of crashing
            return NutritionFacts(
                name=ingredient_name,
                kcal_per_100g=0,
                protein_g_per_100g=0,
                carbs_g_per_100g=0,
                fat_g_per_100g=0,
                source="error",
            )

    def clear_cache(self):
        """Clear both memory and disk cache."""
        self._cache.clear()
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
            self.logger.info(f"Cleared cache file: {self.cache_file}")
        self.logger.info("Nutrition cache cleared")

    def get_cache_stats(self):
        """Get cache statistics."""
        return {
            "memory_cache_size": len(self._cache),
            "memory_cache_maxsize": self._cache.maxsize,
            "disk_cache_file": self.cache_file,
            "disk_cache_exists": os.path.exists(self.cache_file),
            "ttl_seconds": self._cache.ttl,
        }
