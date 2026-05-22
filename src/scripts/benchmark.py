"""
THIS IS FOR TEST PURPOSE. THE CODE INSIDE NEEDS CHANGING.
"""

import asyncio
import random
import time
from typing import List

from ai.schemas import NutritionFacts


# Add this line near the top of benchmark.py (after imports)
class MockNutritionProvider:
    # Add this constant
    MOCK_FACTS = NutritionFacts(
        name="mock",
        kcal_per_100g=100.0,
        protein_g_per_100g=10.0,
        carbs_g_per_100g=20.0,
        fat_g_per_100g=5.0,
        source="mock",
    )

    async def async_lookup(self, name: str) -> NutritionFacts:
        await asyncio.sleep(random.uniform(0.05, 0.15))
        return self.MOCK_FACTS  # Use constant instead of creating new

    def lookup(self, name: str) -> NutritionFacts:
        time.sleep(random.uniform(0.05, 0.15))
        return self.MOCK_FACTS  # Use constant instead of creating new


# Test ingredients (20 items)
TEST_INGREDIENTS = [
    "rice",
    "chicken",
    "broccoli",
    "tomato",
    "cheese",
    "pasta",
    "salmon",
    "potato",
    "egg",
    "carrot",
    "onion",
    "garlic",
    "spinach",
    "apple",
    "banana",
    "milk",
    "bread",
    "butter",
    "salt",
    "pepper",
]


def benchmark_sync(provider: MockNutritionProvider, ingredients: List[str]) -> float:
    """Sequential sync lookup."""
    start = time.perf_counter()
    for name in ingredients:
        provider.lookup(name)
    end = time.perf_counter()
    return end - start


async def benchmark_async(
    provider: MockNutritionProvider, ingredients: List[str]
) -> float:
    """Concurrent async lookup."""
    start = time.perf_counter()
    tasks = [provider.async_lookup(name) for name in ingredients]
    await asyncio.gather(*tasks)
    end = time.perf_counter()
    return end - start


def main():
    """Main entry point for the benchmark script."""
    print("=" * 50)
    print("Nutrition Lookup Benchmark (Mock)")
    print(f"Ingredients: {len(TEST_INGREDIENTS)} items")
    print("Each mock lookup simulates 0.05-0.15s network delay")
    print("=" * 50)

    provider = MockNutritionProvider()

    print("\nRunning synchronous benchmark (sequential)...")
    sync_time = benchmark_sync(provider, TEST_INGREDIENTS)
    print(f"Sync (sequential): {sync_time:.4f} seconds")

    print("\nRunning asynchronous benchmark (concurrent)...")
    async_time = asyncio.run(benchmark_async(provider, TEST_INGREDIENTS))
    print(f"Async (concurrent): {async_time:.4f} seconds")

    print("\n" + "=" * 50)
    print(f"Speedup: {sync_time / async_time:.2f}x faster")
    print("=" * 50)
    print("\nNote: This benchmark uses mock delays.")
    print("Real USDA API calls would show similar or better speedup.")


if __name__ == "__main__":
    main()
