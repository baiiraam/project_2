import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from ai.schemas import Ingredient, NutritionFacts


# Sync version (existing)
def fetch_all_nutrition_sync(
    ingredients: List[Ingredient], nutrition_provider, max_workers: int = 10
) -> Dict[str, NutritionFacts]:
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ingredient = {
            executor.submit(nutrition_provider.lookup, ing.name): ing
            for ing in ingredients
        }
        for future in as_completed(future_to_ingredient):
            ingredient = future_to_ingredient[future]
            try:
                facts = future.result()
                results[ingredient.name] = facts
            except Exception as e:
                print(f"Error fetching for {ingredient.name}: {e}")
    return results


# Async version (new)
async def fetch_all_nutrition_async(
    ingredients: List[Ingredient], nutrition_provider, max_concurrent: int = 10
) -> Dict[str, NutritionFacts]:
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(ingredient: Ingredient):
        async with semaphore:
            facts = await nutrition_provider.async_lookup(ingredient.name)
            return ingredient.name, facts

    tasks = [fetch_one(ing) for ing in ingredients]
    results = await asyncio.gather(*tasks)
    return dict(results)
