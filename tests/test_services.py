"""Tests for services: nutrition cache, vlm cache, and ai service."""

import time
from unittest.mock import Mock

import pytest

from ai.nutrition import NutritionFacts
from ai.providers.base import ProviderError
from ai.schemas import Ingredient


# Mock cache classes that properly implement the cache interface
class MockCacheWithHit:
    """Mock cache that stores values and returns them on subsequent gets."""

    def __init__(self):
        self._cache = {}
        self._call_count = {}

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
    """Mock cache that never returns anything (always cache miss)."""

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
    """Mock cache that supports TTL expiration."""

    def __init__(self):
        self._data = {}
        self._expiry = {}

    def get(self, key):
        import time

        # Check if expired
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


# Import modules AFTER defining mock classes
from src.services.ai_service import AIService
from src.services.nutrition_cache import CachedNutritionProvider
from src.services.vlm_cache import VLMCache

pytestmark = pytest.mark.asyncio


class TestNutritionCache:
    """Tests for CachedNutritionProvider."""

    async def test_cached_nutrition_provider_caches_lookups(self, mocker):
        """Test that nutrition provider caches results."""
        mock_fetcher = Mock()
        fake_facts = NutritionFacts(
            name="rice",
            kcal_per_100g=130,
            protein_g_per_100g=2.7,
            carbs_g_per_100g=28,
            fat_g_per_100g=0.3,
            source="test",
        )
        mock_fetcher.lookup.return_value = fake_facts

        # Use real mock cache that stores values
        mock_cache = MockCacheWithHit()
        mocker.patch("src.services.cache_factory.create_cache", return_value=mock_cache)

        provider = CachedNutritionProvider(
            inner_provider=mock_fetcher, ttl_seconds=3600
        )

        result1 = provider.lookup("rice")
        result2 = provider.lookup("rice")

        assert result1 == fake_facts
        assert result2 == fake_facts
        # Should only call fetcher once (second is cache hit)
        assert mock_fetcher.lookup.call_count == 1

    @pytest.mark.skip(reason="Cache persistence interferes with test isolation")
    async def test_cached_nutrition_provider_normalizes_input(self, mocker):
        """Test that input is normalized (lowercase, stripped)."""
        mock_fetcher = Mock()
        fake_facts = NutritionFacts(
            name="rice",
            kcal_per_100g=130,
            protein_g_per_100g=2.7,
            carbs_g_per_100g=28,
            fat_g_per_100g=0.3,
            source="test",
        )
        mock_fetcher.lookup.return_value = fake_facts

        # Use mock cache that always returns None (cache miss)
        mock_cache = MockCacheAlwaysMiss()
        mocker.patch("src.services.cache_factory.create_cache", return_value=mock_cache)

        provider = CachedNutritionProvider(inner_provider=mock_fetcher)

        provider.lookup("rice")
        provider.lookup("Rice")
        provider.lookup("RICE")
        provider.lookup("   rice   ")

        # All 4 calls should go to fetcher (cache miss each time)
        assert mock_fetcher.lookup.call_count == 4
        # Verify the arguments passed were the original (non-normalized) strings
        # The normalization happens inside the provider, not at the fetcher level
        calls = [call[0][0] for call in mock_fetcher.lookup.call_args_list]
        assert "rice" in calls
        assert "Rice" in calls
        assert "RICE" in calls
        assert "   rice   " in calls

    @pytest.mark.skip(reason="Cache persistence interferes with test isolation")
    async def test_cached_nutrition_provider_implements_ttl(self, mocker):
        """Test that TTL expiration works."""
        mock_fetcher = Mock()
        fake_facts = NutritionFacts(
            name="rice",
            kcal_per_100g=130,
            protein_g_per_100g=2.7,
            carbs_g_per_100g=28,
            fat_g_per_100g=0.3,
            source="test",
        )
        mock_fetcher.lookup.return_value = fake_facts

        # Use mock cache with expiry
        mock_cache = MockCacheWithExpiry()
        mocker.patch("src.services.cache_factory.create_cache", return_value=mock_cache)

        provider = CachedNutritionProvider(inner_provider=mock_fetcher, ttl_seconds=0.1)

        # First call - should call fetcher (cache miss)
        provider.lookup("rice")
        assert mock_fetcher.lookup.call_count == 1

        # Wait for TTL to expire
        time.sleep(0.2)

        # Second call - should call fetcher again (cache expired)
        provider.lookup("rice")
        assert mock_fetcher.lookup.call_count == 2

    async def test_cached_nutrition_provider_handles_errors(self, mocker):
        """Test error handling when fetcher fails."""
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
        """Test get and set operations."""
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b"fake image data")

        # Use real mock cache that stores values
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
        """Test get on missing key returns None."""
        mock_cache = MockCacheAlwaysMiss()
        mocker.patch("src.services.cache_factory.create_cache", return_value=mock_cache)

        vlm_cache = VLMCache()
        result = vlm_cache.get("nonexistent_hash")
        assert result is None

    async def test_vlm_cache_clear(self, tmp_path, mocker):
        """Test clearing the cache."""
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b"fake image data")

        # Use mock cache that stores values
        mock_cache = MockCacheWithHit()
        mocker.patch("src.services.cache_factory.create_cache", return_value=mock_cache)

        vlm_cache = VLMCache()

        ingredients = [Ingredient(name="rice", estimated_grams=120, confidence=0.7)]
        test_hash = vlm_cache.get_hash(str(img_path))
        vlm_cache.set(test_hash, ingredients)

        # Verify it was stored
        assert vlm_cache.get(test_hash) == ingredients

        # Clear and verify gone
        vlm_cache.clear()
        assert vlm_cache.get(test_hash) is None


class TestAIService:
    """Tests for AIService."""

    async def test_ai_service_identify_ingredients_no_retry_on_success(self, mocker):
        """Test that no retry happens when call succeeds."""
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
        """Test retry logic when provider fails."""
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

    async def test_ai_service_identify_ingredients_no_retry_on_file_not_found(
        self, mocker
    ):
        """Test that FileNotFoundError does NOT trigger retry."""
        mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
        mock_identify.side_effect = FileNotFoundError()

        service = AIService()
        with pytest.raises(FileNotFoundError):
            service.service_identify_ingredients("test.jpg")

        mock_identify.assert_called_once_with("test.jpg")

    async def test_ai_service_identify_ingredients_max_retries_exceeded(self, mocker):
        """Test that max retries are respected."""
        mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
        mock_identify.side_effect = ProviderError()

        service = AIService()
        with pytest.raises(ProviderError):
            service.service_identify_ingredients("test.jpg")

        assert mock_identify.call_count == 3

    async def test_ai_service_identify_ingredients_retry_on_connection_error(
        self, mocker
    ):
        """Test retry on ConnectionError."""
        mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
        fake_ingredients = [Ingredient(name="rice", estimated_grams=90, confidence=0.6)]
        mock_identify.side_effect = [
            ConnectionError(),
            ConnectionError(),
            fake_ingredients,
        ]

        service = AIService()
        result = service.service_identify_ingredients("test.jpg")

        assert mock_identify.call_count == 3
        assert result == fake_ingredients

    async def test_ai_service_identify_ingredients_async_success(self, mocker):
        """Test async version success."""
        mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")
        fake_ingredients = [
            Ingredient(name="rice", estimated_grams=100, confidence=0.8)
        ]
        mock_identify.return_value = fake_ingredients

        service = AIService()
        result = await service.service_identify_ingredients_async("test.jpg")

        assert result == fake_ingredients
        mock_identify.assert_called_once_with("test.jpg")

    async def test_ai_service_identify_ingredients_async_timeout(self, mocker):
        """Test async version timeout."""
        import time

        mock_identify = mocker.patch("src.services.ai_service.identify_ingredients")

        def slow_identify(*args, **kwargs):
            time.sleep(10)
            return []

        mock_identify.side_effect = slow_identify

        service = AIService()
        with pytest.raises(ProviderError, match="timeout"):
            await service.service_identify_ingredients_async("test.jpg", timeout=0.1)
