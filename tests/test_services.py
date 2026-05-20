"""Tests for services: nutrition cache, vlm cache, and ai service."""

import time
from unittest.mock import Mock

import pytest

from ai.nutrition import NutritionFacts
from ai.providers.base import ProviderError
from ai.schemas import Ingredient
from src.services.ai_service import AIService
from src.services.nutrition_cache import CachedNutritionProvider
from src.services.vlm_cache import VLMCache

pytestmark = pytest.mark.asyncio


# Mock cache classes
class MockCacheWithHit:
    def __init__(self):
        self._cache = {}

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value, ttl=None):
        self._cache[key] = value

    def delete(self, key):
        self._cache.pop(key, None)

    def clear(self):
        self._cache.clear()

    def get_stats(self):
        return {"type": "mock", "total_keys": len(self._cache)}


class MockCacheAlwaysMiss:
    def get(self, key):
        return None

    def set(self, key, value, ttl=None):
        pass

    def delete(self, key):
        pass

    def clear(self):
        pass

    def get_stats(self):
        return {"type": "mock", "total_keys": 0}


class MockCacheWithExpiry:
    def __init__(self):
        self._data = {}
        self._expiry = {}

    def get(self, key):
        import time
        if key in self._expiry and time.time() > self._expiry[key]:
            del self._data[key]
            del self._expiry[key]
            return None
        return self._data.get(key)

    def set(self, key, value, ttl=None):
        import time
        self._data[key] = value
        if ttl:
            self._expiry[key] = time.time() + ttl

    def delete(self, key):
        self._data.pop(key, None)
        self._expiry.pop(key, None)

    def clear(self):
        self._data.clear()
        self._expiry.clear()

    def get_stats(self):
        return {"type": "mock", "total_keys": len(self._data)}


class TestNutritionCache:
    """Tests for CachedNutritionProvider."""

    async def test_cached_nutrition_provider_caches_lookups(self, mocker):
        mock_fetcher = Mock()
        fake_facts = NutritionFacts(
            name="rice", kcal_per_100g=130, protein_g_per_100g=2.7,
            carbs_g_per_100g=28, fat_g_per_100g=0.3, source="test"
        )
        mock_fetcher.lookup.return_value = fake_facts

        mock_cache = MockCacheWithHit()
        mocker.patch("src.services.cache_factory.create_cache", return_value=mock_cache)

        provider = CachedNutritionProvider(inner_provider=mock_fetcher, ttl_seconds=3600)

        result1 = provider.lookup("rice")
        result2 = provider.lookup("rice")

        assert result1 == fake_facts
        assert result2 == fake_facts
        assert mock_fetcher.lookup.call_count == 1

    async def test_cached_nutrition_provider_normalizes_input(self, mocker):
        mock_fetcher = Mock()
        fake_facts = NutritionFacts(
            name="rice", kcal_per_100g=130, protein_g_per_100g=2.7,
            carbs_g_per_100g=28, fat_g_per_100g=0.3, source="test"
        )
        mock_fetcher.lookup.return_value = fake_facts

        mock_cache = MockCacheAlwaysMiss()
        mocker.patch("src.services.cache_factory.create_cache", return_value=mock_cache)

        provider = CachedNutritionProvider(inner_provider=mock_fetcher)

        provider.lookup("rice")
        provider.lookup("Rice")
        provider.lookup("RICE")
        provider.lookup("   rice   ")

        assert mock_fetcher.lookup.call_count == 4

    async def test_cached_nutrition_provider_implements_ttl(self, mocker):
        mock_fetcher = Mock()
        fake_facts = NutritionFacts(
            name="rice", kcal_per_100g=130, protein_g_per_100g=2.7,
            carbs_g_per_100g=28, fat_g_per_100g=0.3, source="test"
        )
        mock_fetcher.lookup.return_value = fake_facts

        mock_cache = MockCacheWithExpiry()
        mocker.patch("src.services.cache_factory.create_cache", return_value=mock_cache)

        provider = CachedNutritionProvider(inner_provider=mock_fetcher, ttl_seconds=0.1)

        provider.lookup("rice")
        assert mock_fetcher.lookup.call_count == 1

        time.sleep(0.2)

        provider.lookup("rice")
        assert mock_fetcher.lookup.call_count == 2

    async def test_cached_nutrition_provider_handles_errors(self, mocker):
        mock_fetcher = Mock()
        mock_fetcher.lookup.side_effect = ProviderError("API Error")

        mock_cache = MockCacheAlwaysMiss()
        mocker.patch("src.services.cache_factory.create_cache", return_value=mock_cache)

        provider = CachedNutritionProvider(inner_provider=mock_fetcher)

        with pytest.raises(ProviderError):
            provider.lookup("unknown")


class TestVLMCache:
    """Tests for VLMCache."""

    async def test_vlm_cache_get_and_set(self, tmp_path, mocker):
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b"fake image data")

        mock_cache = MockCacheWithHit()
        mocker.patch("src.services.cache_factory.create_cache", return_value=mock_cache)

        vlm_cache = VLMCache(ttl_seconds=3600)

        ingredients = [
            Ingredient(name="rice", estimated_grams=120, confidence=0.7),
            Ingredient(name="chicken", estimated_grams=150, confidence=0.8),
        ]

        test_hash = vlm_cache.get_hash(str(img_path))
        vlm_cache.set(test_hash, ingredients)

        result = vlm_cache.get(test_hash)
        assert result == ingredients

    async def test_vlm_cache_get_missing(self, tmp_path, mocker):
        mock_cache = MockCacheAlwaysMiss()
        mocker.patch("src.services.cache_factory.create_cache", return_value=mock_cache)

        vlm_cache = VLMCache()
        result = vlm_cache.get("nonexistent_hash")
        assert result is None

    async def test_vlm_cache_clear(self, tmp_path, mocker):
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b"fake image data")

        mock_cache = MockCacheWithHit()
        mocker.patch("src.services.cache_factory.create_cache", return_value=mock_cache)

        vlm_cache = VLMCache()

        ingredients = [Ingredient(name="rice", estimated_grams=120, confidence=0.7)]
        test_hash = vlm_cache.get_hash(str(img_path))
        vlm_cache.set(test_hash, ingredients)

        assert vlm_cache.get(test_hash) == ingredients

        vlm_cache.clear()
        assert vlm_cache.get(test_hash) is None


class TestAIService:
    """Tests for AIService."""

    async def test_ai_service_identify_ingredients_no_retry_on_success(self, mocker):
        mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
        fake_ingredients = [
            Ingredient(name="rice", estimated_grams=100, confidence=0.8),
            Ingredient(name="chicken", estimated_grams=110, confidence=0.7),
        ]
        mock_identify.return_value = fake_ingredients

        service = AIService()
        result = service.service_identify_ingredients("test.jpg")

        mock_identify.assert_called_once_with("test.jpg")
        assert result == fake_ingredients

    async def test_ai_service_identify_ingredients_retries_on_failure(self, mocker):
        mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
        fake_ingredients = [
            Ingredient(name="rice", estimated_grams=100, confidence=0.8),
            Ingredient(name="chicken", estimated_grams=110, confidence=0.7),
        ]
        mock_identify.side_effect = [ProviderError(), ProviderError(), fake_ingredients]

        service = AIService()
        result = service.service_identify_ingredients("test.jpg")

        assert mock_identify.call_count == 3
        assert result == fake_ingredients

    async def test_ai_service_identify_ingredients_no_retry_on_file_not_found(self, mocker):
        mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
        mock_identify.side_effect = FileNotFoundError()

        service = AIService()
        with pytest.raises(FileNotFoundError):
            service.service_identify_ingredients("test.jpg")

        mock_identify.assert_called_once_with("test.jpg")

    async def test_ai_service_identify_ingredients_max_retries_exceeded(self, mocker):
        mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
        mock_identify.side_effect = ProviderError()

        service = AIService()
        with pytest.raises(ProviderError):
            service.service_identify_ingredients("test.jpg")

        assert mock_identify.call_count == 3

    async def test_ai_service_identify_ingredients_retry_on_connection_error(self, mocker):
        mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
        fake_ingredients = [Ingredient(name="rice", estimated_grams=90, confidence=0.6)]
        mock_identify.side_effect = [ConnectionError(), ConnectionError(), fake_ingredients]

        service = AIService()
        result = service.service_identify_ingredients("test.jpg")

        assert mock_identify.call_count == 3
        assert result == fake_ingredients

    async def test_ai_service_identify_ingredients_async_success(self, mocker):
        mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
        fake_ingredients = [Ingredient(name="rice", estimated_grams=100, confidence=0.8)]
        mock_identify.return_value = fake_ingredients

        service = AIService()
        result = await service.service_identify_ingredients_async("test.jpg")

        assert result == fake_ingredients
        mock_identify.assert_called_once_with("test.jpg")

    async def test_ai_service_identify_ingredients_async_timeout(self, mocker):
        import time

        mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")

        def slow_identify(*args, **kwargs):
            time.sleep(10)
            return []

        mock_identify.side_effect = slow_identify

        service = AIService()
        with pytest.raises(ProviderError, match="timeout"):
            await service.service_identify_ingredients_async("test.jpg", timeout=0.1)
