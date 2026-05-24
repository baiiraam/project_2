"""Benchmark for nutrition lookups - Windows compatible (no emojis)."""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_settings

TEST_INGREDIENTS = [
    "rice", "chicken breast", "broccoli", "tomato", "cheese",
    "pasta", "salmon", "potato", "egg", "carrot",
    "onion", "garlic", "spinach", "apple", "banana",
]


def main():
    print("\n" + "=" * 60)
    print("AI FOOD ANALYZER - BENCHMARK (15 INGREDIENTS)")
    print("=" * 60)

    settings = get_settings()
    provider = settings.get_nutrition_provider()

    print("\n[CONFIGURATION]")
    print(f"  Nutrition Providers: {settings.get_available_nutrition_providers()}")
    print(f"  Failover Enabled: {settings.NUTRITION_FAILOVER_ENABLED}")
    print(f"  Provider Type: {type(provider).__name__}")

    # Sequential
    print("\n" + "-" * 60)
    print("SEQUENTIAL LOOKUP")
    print("-" * 60)

    start = time.perf_counter()
    seq_results = {}
    for i, name in enumerate(TEST_INGREDIENTS, 1):
        try:
            facts = provider.lookup(name)
            seq_results[name] = facts.kcal_per_100g
            print(f"  {i:2}. {name:<20} {facts.kcal_per_100g:>6.0f} kcal/100g")
        except Exception as e:
            print(f"  {i:2}. {name:<20} FAILED: {e}")
            seq_results[name] = 0
    seq_time = time.perf_counter() - start
    print(f"\n  Time: {seq_time:.2f} seconds")

    # Concurrent
    print("\n" + "-" * 60)
    print("CONCURRENT LOOKUP (ThreadPoolExecutor)")
    print("-" * 60)

    def lookup_one(name):
        try:
            facts = provider.lookup(name)
            return name, facts.kcal_per_100g
        except Exception:
            return name, 0

    start = time.perf_counter()
    con_results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(lookup_one, name): name for name in TEST_INGREDIENTS}
        for future in as_completed(futures):
            name, kcal = future.result()
            con_results[name] = kcal

    con_time = time.perf_counter() - start

    for i, name in enumerate(TEST_INGREDIENTS, 1):
        kcal = con_results.get(name, 0)
        print(f"  {i:2}. {name:<20} {kcal:>6.0f} kcal/100g")
    print(f"\n  Time: {con_time:.2f} seconds")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Sequential: {seq_time:.2f}s")
    print(f"  Concurrent: {con_time:.2f}s")
    print(f"  Speedup: {seq_time / con_time:.1f}x")

    # Success rate
    success = sum(1 for v in seq_results.values() if v > 0)
    print(f"  Success rate: {success}/{len(TEST_INGREDIENTS)} ({success/len(TEST_INGREDIENTS)*100:.0f}%)")

    print("\nBenchmark complete!\n")


if __name__ == "__main__":
    main()
