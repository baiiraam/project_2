"""Tests for benchmark script - simplified version."""


from src.services.mock_nutrition_provider import MockNutritionProvider

# Test ingredients
TEST_INGREDIENTS = [
    "rice", "chicken breast", "broccoli", "tomato", "cheese",
    "pasta", "salmon", "potato", "egg", "carrot",
]


def benchmark_sync(provider: MockNutritionProvider, ingredients: list) -> float:
    """Sequential sync lookup."""
    import time
    start = time.perf_counter()
    for name in ingredients:
        provider.lookup(name)
    return time.perf_counter() - start


class TestMockNutritionProvider:
    """Test mock nutrition provider."""

    def test_mock_provider_returns_values(self):
        """Test that MockNutritionProvider returns consistent data."""
        provider = MockNutritionProvider()

        result = provider.lookup("rice")
        assert result.kcal_per_100g == 130
        assert result.protein_g_per_100g == 2.7

    def test_mock_provider_unknown_ingredient(self):
        """Test unknown ingredient returns zeros."""
        provider = MockNutritionProvider()
        result = provider.lookup("unknown ingredient")
        assert result.kcal_per_100g == 0

    def test_mock_provider_keyword_matching(self):
        """Test keyword matching for phrases."""
        provider = MockNutritionProvider()
        result = provider.lookup("bowl of white rice")
        assert result.kcal_per_100g == 130


class TestBenchmarkSync:
    """Test sync benchmark functions."""

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

    def test_benchmark_sync_with_large_list(self):
        """Test sync benchmark with large ingredient list."""
        provider = MockNutritionProvider()
        large_list = TEST_INGREDIENTS * 3

        result = benchmark_sync(provider, large_list)

        assert isinstance(result, float)
        assert result > 0
