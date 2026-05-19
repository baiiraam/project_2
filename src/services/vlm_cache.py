import json
import os
from cachetools import TTLCache
from typing import List, Optional
from ai.schemas import Ingredient
import hashlib


class VLMCache:
    def __init__(
        self,
        ttl_seconds: int = 3600,
        maxsize: int = 100,
        cache_file: str = "vlm_cache.json",
    ):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self.cache_file = cache_file
        self._load_from_disk()

    def _load_from_disk(self):
        """Load cached entries from JSON file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        # Convert stored dict back to Ingredient objects
                        ingredients = [Ingredient(**ing) for ing in value]
                        self._cache[key] = ingredients
                print(f"Loaded {len(self._cache)} entries from {self.cache_file}")
            except Exception as e:
                print(f"Failed to load cache: {e}")

    def _save_to_disk(self):
        """Save cache entries to JSON file."""
        try:
            data = {}
            for key, ingredients in self._cache.items():
                # Convert Ingredient objects to dicts
                data[key] = [ing.model_dump() for ing in ingredients]
            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save cache: {e}")

    def get(self, image_path: str) -> Optional[List[Ingredient]]:
        result = self._cache.get(image_path)
        print(f"VLM Cache get({image_path}) -> {result is not None}")
        return result

    def set(self, image_path: str, ingredients: List[Ingredient]) -> None:
        print(f"VLM Cache set({image_path}) storing {len(ingredients)} ingredients")
        self._cache[image_path] = ingredients
        self._save_to_disk()

    def has(self, image_path: str) -> bool:
        return image_path in self._cache

    def clear(self) -> None:
        self._cache.clear()
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    def get_hash(self, image_path: str) -> str:
        """Generate SHA-256 hash of image content."""
        with open(image_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
