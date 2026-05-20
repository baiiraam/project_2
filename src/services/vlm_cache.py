"""VLM cache with persistent storage."""

import hashlib
from typing import List, Optional, Any
from ai.schemas import Ingredient
from src.services.cache_factory import create_cache
from loguru import logger


class VLMCache:
    """Persistent VLM cache using configured backend."""

    def __init__(self, ttl_seconds: int = 86400):
        self.ttl = int(ttl_seconds)
        self._cache = create_cache()
        logger.info(f"VLMCache initialized with {self._cache.get_stats()['type']} backend")

    def _get_hash(self, image_path: str) -> str:
        """Generate SHA-256 hash of image content."""
        sha256 = hashlib.sha256()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def _get_hash_async(self, image_path: str) -> str:
        """Generate SHA-256 hash asynchronously."""
        import aiofiles
        sha256 = hashlib.sha256()
        async with aiofiles.open(image_path, "rb") as f:
            while chunk := await f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get(self, image_hash: str) -> Optional[List[Ingredient]]:
        """Get cached ingredients by image hash."""
        cached = self._cache.get(image_hash)
        if cached and isinstance(cached, dict) and "ingredients" in cached:
            logger.info(f"VLM cache HIT: {image_hash[:16]}...")
            return [Ingredient(**ing) for ing in cached["ingredients"]]
        logger.info(f"VLM cache MISS: {image_hash[:16]}...")
        return None

    def set(self, image_hash: str, ingredients: List[Ingredient]) -> None:
        """Cache ingredients by image hash."""
        # Store as dict with 'ingredients' key to satisfy type checker
        data: dict = {"ingredients": [ing.model_dump() for ing in ingredients]}
        self._cache.set(image_hash, data, self.ttl)
        logger.info(f"VLM cache SET: {image_hash[:16]}... ({len(ingredients)} ingredients)")

    def has(self, image_hash: str) -> bool:
        """Check if hash exists in cache."""
        return self.get(image_hash) is not None

    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
        logger.info("VLM cache cleared")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        return self._cache.get_stats()

    def get_hash(self, image_path: str) -> str:
        """Get hash for image (sync version)."""
        return self._get_hash(image_path)

    async def get_hash_async(self, image_path: str) -> str:
        """Get hash for image (async version)."""
        return await self._get_hash_async(image_path)