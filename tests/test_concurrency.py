"""Tests for concurrent nutrition lookups."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from ai.schemas import Ingredient, NutritionFacts
from src.concurrency.pipeline import fetch_all_nutrition_async, fetch_all_nutrition_sync


class TestAsyncConcurrency:
    """Test async concurrent nutrition lookups."""

    @pytest.mark.asyncio
    async def test_fetch_all_nutrition_async_basic(self):
        """Test basic async fetching for multiple ingredients."""
        ingredients = [
            Ingredient(name="rice", estimated_grams=100, confidence=0.9),
            Ingredient(name="chicken", estimated_grams=150, confidence=0.85),
            Ingredient(name="broccoli", estimated_grams=80, confidence=0.8),
        ]

        mock_provider = Mock()

        async def mock_async_lookup(name):
            await asyncio.sleep(0.01)
            return NutritionFacts(
                name=name,
                kcal_per_100g=100,
                protein_g_per_100g=10,
                carbs_g_per_100g=20,
                fat_g_per_100g=5,
                source="test",
            )

        mock_provider.async_lookup = AsyncMock(side_effect=mock_async_lookup)

        results = await fetch_all_nutrition_async(ingredients, mock_provider)

        assert len(results) == 3
        assert "rice" in results
        assert "chicken" in results
        assert "broccoli" in results

    @pytest.mark.asyncio
    async def test_fetch_all_nutrition_async_with_errors(self):
        """Test error handling when one lookup fails - errors propagate."""
        ingredients = [
            Ingredient(name="rice", estimated_grams=100, confidence=0.9),
            Ingredient(name="fail", estimated_grams=100, confidence=0.9),
            Ingredient(name="chicken", estimated_grams=150, confidence=0.85),
        ]

        mock_provider = Mock()

        async def mock_async_lookup(name):
            if name == "fail":
                raise Exception("Lookup failed")
            return NutritionFacts(
                name=name,
                kcal_per_100g=100,
                protein_g_per_100g=10,
                carbs_g_per_100g=20,
                fat_g_per_100g=5,
                source="test",
            )

        mock_provider.async_lookup = AsyncMock(side_effect=mock_async_lookup)

        with pytest.raises(Exception, match="Lookup failed"):
            await fetch_all_nutrition_async(ingredients, mock_provider)

    @pytest.mark.asyncio
    async def test_fetch_all_nutrition_async_semaphore(self):
        """Test that semaphore limits concurrent requests."""
        ingredients = [
            Ingredient(name=f"item{i}", estimated_grams=100, confidence=0.9)
            for i in range(20)
        ]

        concurrent_count = 0
        max_concurrent = 0

        async def mock_async_lookup(name):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.02)
            concurrent_count -= 1
            return NutritionFacts(
                name=name,
                kcal_per_100g=100,
                protein_g_per_100g=10,
                carbs_g_per_100g=20,
                fat_g_per_100g=5,
                source="test",
            )

        mock_provider = Mock()
        mock_provider.async_lookup = AsyncMock(side_effect=mock_async_lookup)

        await fetch_all_nutrition_async(ingredients, mock_provider, max_concurrent=5)

        assert max_concurrent <= 5

    @pytest.mark.asyncio
    async def test_fetch_all_nutrition_async_empty_list(self):
        """Test fetching with empty ingredient list."""
        results = await fetch_all_nutrition_async([], Mock())
        assert results == {}


class TestSyncConcurrency:
    """Test sync concurrent nutrition lookups."""

    def test_fetch_all_nutrition_sync_basic(self):
        """Test basic sync fetching with thread pool."""
        ingredients = [
            Ingredient(name="rice", estimated_grams=100, confidence=0.9),
            Ingredient(name="chicken", estimated_grams=150, confidence=0.85),
        ]

        mock_provider = Mock()

        def mock_lookup(name):
            import time

            time.sleep(0.01)
            return NutritionFacts(
                name=name,
                kcal_per_100g=100,
                protein_g_per_100g=10,
                carbs_g_per_100g=20,
                fat_g_per_100g=5,
                source="test",
            )

        mock_provider.lookup = Mock(side_effect=mock_lookup)

        results = fetch_all_nutrition_sync(ingredients, mock_provider)

        assert len(results) == 2

    def test_fetch_all_nutrition_sync_with_errors(self):
        """Test sync fetching with error handling - errors are caught."""
        ingredients = [
            Ingredient(name="rice", estimated_grams=100, confidence=0.9),
            Ingredient(name="fail", estimated_grams=100, confidence=0.9),
        ]

        mock_provider = Mock()

        def mock_lookup(name):
            if name == "fail":
                raise Exception("Lookup failed")
            return NutritionFacts(
                name=name,
                kcal_per_100g=100,
                protein_g_per_100g=10,
                carbs_g_per_100g=20,
                fat_g_per_100g=5,
                source="test",
            )

        mock_provider.lookup = Mock(side_effect=mock_lookup)

        results = fetch_all_nutrition_sync(ingredients, mock_provider)

        assert "rice" in results
        assert "fail" not in results

    def test_fetch_all_nutrition_sync_empty_list(self):
        """Test sync fetching with empty list."""
        results = fetch_all_nutrition_sync([], Mock())
        assert results == {}


class TestConcurrencyComparison:
    """Compare sync vs async performance."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_async_faster_or_equal_than_sync(self):
        """Test that async is at least as fast as sync."""
        ingredients = [
            Ingredient(name=f"item{i}", estimated_grams=100, confidence=0.9)
            for i in range(10)
        ]  # Increased to 10 for better async advantage

        async def mock_async_lookup(name):
            await asyncio.sleep(0.02)  # 20ms delay
            return NutritionFacts(
                name=name,
                kcal_per_100g=100,
                protein_g_per_100g=10,
                carbs_g_per_100g=20,
                fat_g_per_100g=5,
                source="test",
            )

        def mock_sync_lookup(name):
            import time

            time.sleep(0.02)  # 20ms delay
            return NutritionFacts(
                name=name,
                kcal_per_100g=100,
                protein_g_per_100g=10,
                carbs_g_per_100g=20,
                fat_g_per_100g=5,
                source="test",
            )

        mock_provider_async = Mock()
        mock_provider_async.async_lookup = AsyncMock(side_effect=mock_async_lookup)

        mock_provider_sync = Mock()
        mock_provider_sync.lookup = Mock(side_effect=mock_sync_lookup)

        import time

        # Measure async
        start = time.time()
        await fetch_all_nutrition_async(ingredients, mock_provider_async)
        async_time = time.time() - start

        # Measure sync
        start = time.time()
        fetch_all_nutrition_sync(ingredients, mock_provider_sync)
        sync_time = time.time() - start

        # Async should be faster or equal (allow 100ms tolerance on Windows)
        assert async_time <= sync_time + 0.1


class TestEdgeCases:
    """Test edge cases for concurrency."""

    @pytest.mark.asyncio
    async def test_duplicate_ingredients(self):
        """Test handling of duplicate ingredient names."""
        ingredients = [
            Ingredient(name="rice", estimated_grams=100, confidence=0.9),
            Ingredient(name="rice", estimated_grams=50, confidence=0.8),
        ]

        call_count = 0

        async def mock_async_lookup(name):
            nonlocal call_count
            call_count += 1
            return NutritionFacts(
                name=name,
                kcal_per_100g=100,
                protein_g_per_100g=10,
                carbs_g_per_100g=20,
                fat_g_per_100g=5,
                source="test",
            )

        mock_provider = Mock()
        mock_provider.async_lookup = AsyncMock(side_effect=mock_async_lookup)

        results = await fetch_all_nutrition_async(ingredients, mock_provider)

        # Both lookups should happen
        assert call_count == 2
        assert len(results) == 1
        assert "rice" in results

    @pytest.mark.asyncio
    async def test_large_ingredient_list(self):
        """Test handling of large ingredient lists."""
        ingredients = [
            Ingredient(name=f"item{i}", estimated_grams=100, confidence=0.9)
            for i in range(50)
        ]

        async def mock_async_lookup(name):
            await asyncio.sleep(0.001)
            return NutritionFacts(
                name=name,
                kcal_per_100g=100,
                protein_g_per_100g=10,
                carbs_g_per_100g=20,
                fat_g_per_100g=5,
                source="test",
            )

        mock_provider = Mock()
        mock_provider.async_lookup = AsyncMock(side_effect=mock_async_lookup)

        results = await fetch_all_nutrition_async(ingredients, mock_provider)

        assert len(results) == 50
