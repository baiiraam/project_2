from ai import NutritionFacts, NutritionProvider

# Per-100g nutrition values for common ingredients
MOCK_NUTRITION = {
    # Breads
    "bread": (265, 9.0, 49.0, 3.2),
    "slice of bread": (265, 9.0, 49.0, 3.2),
    "toast": (265, 9.0, 49.0, 3.2),
    # Cheeses
    "cheese": (403, 25.0, 1.3, 33.0),
    "piece of cheese": (403, 25.0, 1.3, 33.0),
    "cheddar": (403, 25.0, 1.3, 33.0),
    # Rice
    "rice": (130, 2.7, 28.0, 0.3),
    "white rice": (130, 2.7, 28.0, 0.3),
    "cooked rice": (130, 2.7, 28.0, 0.3),
    # Chicken
    "chicken": (165, 31.0, 0.0, 3.6),
    "grilled chicken": (165, 31.0, 0.0, 3.6),
    "chicken breast": (165, 31.0, 0.0, 3.6),
    # Beef/Steak
    "steak": (250, 26.0, 0.0, 17.0),
    "grilled steak": (250, 26.0, 0.0, 17.0),
    "beef": (250, 26.0, 0.0, 17.0),
    # Vegetables
    "broccoli": (34, 2.8, 7.0, 0.4),
    "broccoli florets": (34, 2.8, 7.0, 0.4),
    # Fish
    "salmon": (206, 22.0, 0.0, 13.0),
    # Potatoes
    "potato": (93, 2.5, 21.0, 0.1),
    "baked potato": (93, 2.5, 21.0, 0.1),
    # Eggs
    "egg": (155, 13.0, 1.1, 11.0),
}


class MockNutritionProvider(NutritionProvider):
    """Mock nutrition provider that returns fake data for common ingredients."""

    def lookup(self, ingredient_name: str) -> NutritionFacts:
        name = ingredient_name.lower().strip()

        # Try exact match first
        if name in MOCK_NUTRITION:
            kcal, protein, carbs, fat = MOCK_NUTRITION[name]
        else:
            # Try to find a keyword (e.g., "bread" in "slice of bread")
            for key in MOCK_NUTRITION:
                if key in name:
                    kcal, protein, carbs, fat = MOCK_NUTRITION[key]
                    break
            else:
                # Default to zero if not found
                kcal, protein, carbs, fat = (0, 0, 0, 0)

        return NutritionFacts(
            name=ingredient_name,
            kcal_per_100g=kcal,
            protein_g_per_100g=protein,
            carbs_g_per_100g=carbs,
            fat_g_per_100g=fat,
            source="mock",
        )
