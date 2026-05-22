"""Tests for benchmark script."""

import asyncio

import pytest

from src.scripts.benchmark import (
    TEST_INGREDIENTS,
    MockNutritionProvider,
    benchmark_async,
    benchmark_sync,
)


class TestBenchmarkScript:
    """Test benchmark script functionality."""

    def test_benchmark_sync_returns_time(self):
        """Test sync benchmark returns a positive time measurement."""
        provider = MockNutritionProvider()
        ingredients = TEST_INGREDIENTS[:5]

        result = benchmark_sync(provider, ingredients)

        assert isinstance(result, float)
        assert result > 0

    def test_benchmark_sync_with_empty_list(self):
        """Test sync benchmark with empty ingredient list."""
        provider = MockNutritionProvider()
        result = benchmark_sync(provider, [])

        assert isinstance(result, float)
        assert result >= 0

    def test_benchmark_sync_with_single_ingredient(self):
        """Test sync benchmark with single ingredient."""
        provider = MockNutritionProvider()
        result = benchmark_sync(provider, ["rice"])

        assert isinstance(result, float)
        assert result > 0

    @pytest.mark.asyncio
    async def test_benchmark_async_returns_time(self):
        """Test async benchmark returns a positive time measurement."""
        provider = MockNutritionProvider()
        ingredients = TEST_INGREDIENTS[:5]

        result = await benchmark_async(provider, ingredients)

        assert isinstance(result, float)
        assert result > 0

    @pytest.mark.asyncio
    async def test_benchmark_async_with_empty_list(self):
        """Test async benchmark with empty ingredient list."""
        provider = MockNutritionProvider()
        result = await benchmark_async(provider, [])

        assert isinstance(result, float)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_benchmark_async_faster_or_equal_to_sync(self):
        """Test that async is at least as fast as sync (within tolerance)."""
        provider = MockNutritionProvider()
        ingredients = TEST_INGREDIENTS[:10]

        # Run sync benchmark
        sync_time = benchmark_sync(provider, ingredients)

        # Run async benchmark
        async_time = await benchmark_async(provider, ingredients)

        # Async should be faster or equal (allow 0.1s overhead on Windows)
        assert async_time <= sync_time + 0.1

    def test_benchmark_with_large_ingredient_list(self):
        """Test benchmark with large ingredient list."""
        provider = MockNutritionProvider()
        large_list = TEST_INGREDIENTS * 3  # 60 ingredients

        result = benchmark_sync(provider, large_list)

        assert isinstance(result, float)
        assert result > 0

    @pytest.mark.asyncio
    async def test_async_benchmark_concurrent_execution(self):
        """Test that async benchmark actually runs concurrently."""
        import time

        # Create a custom provider that tracks execution
        start_times = []
        end_times = []

        class TrackedProvider(MockNutritionProvider):
            async def async_lookup(self, name: str):
                start_times.append(time.time())
                await asyncio.sleep(0.05)  # Simulate network delay
                end_times.append(time.time())
                return self.MOCK_FACTS

        provider = TrackedProvider()
        ingredients = TEST_INGREDIENTS[:20]

        await benchmark_async(provider, ingredients)

        # If concurrent, total time should be less than sum of individual delays
        # With 20 items at 0.05s each, sync would be 1.0s, async should be ~0.05s
        if start_times and end_times:
            total_duration = max(end_times) - min(start_times)
            assert total_duration < 0.3  # Much less than 1.0 second

    def test_benchmark_module_imports(self):
        """Test that benchmark module imports correctly."""
        from src.scripts import benchmark as bench_module

        # Verify the module has required attributes
        assert hasattr(bench_module, 'MockNutritionProvider')
        assert hasattr(bench_module, 'TEST_INGREDIENTS')
        assert hasattr(bench_module, 'benchmark_sync')
        assert hasattr(bench_module, 'benchmark_async')

        # Verify TEST_INGREDIENTS is a non-empty list
        assert len(bench_module.TEST_INGREDIENTS) > 0

    def test_mock_provider_returns_consistent_results(self):
        """Test that MockNutritionProvider returns consistent fake data."""
        provider = MockNutritionProvider()

        # Multiple calls should return the same structure
        result1 = provider.lookup("rice")
        result2 = provider.lookup("chicken")

        assert result1.kcal_per_100g == 100.0
        assert result1.protein_g_per_100g == 10.0
        assert result2.kcal_per_100g == 100.0
        assert result2.protein_g_per_100g == 10.0
