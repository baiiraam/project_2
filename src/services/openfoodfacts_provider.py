import requests
from ai import NutritionFacts, NutritionProvider
from ai.providers.base import ProviderError


class OpenFoodFactsProvider(NutritionProvider):
    """Nutrition provider using Open Food Facts API."""

    # Use staging environment for development
    BASE_URL = "https://world.openfoodfacts.net/api/v2"

    def __init__(self, user_agent: str, timeout: float = 10.0):
        """Initialize the provider.

        Args:
            user_agent: Required. Format: "AppName/Version (contact@example.com)"
            timeout: Request timeout in seconds.
        """
        self.user_agent = user_agent
        self.timeout = timeout

    def lookup(self, ingredient_name: str) -> NutritionFacts:
        """Look up nutrition facts for an ingredient.

        Searches Open Food Facts for a product matching the ingredient name
        and returns per-100g nutrition values.
        """
        # Search for products matching the ingredient
        search_url = f"{self.BASE_URL}/search"
        params = {"search_terms": ingredient_name, "page_size": 1, "json": True}
        headers = {"User-Agent": self.user_agent}

        try:
            response = requests.get(
                search_url, params=params, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            products = data.get("products", [])
            if not products:
                raise ProviderError(f"No product found for: {ingredient_name}")

            # Find a product whose name contains the ingredient name
            matching_product = None
            ingredient_lower = ingredient_name.lower()

            for product in products:
                product_name = product.get("product_name", "").lower()
                if ingredient_lower in product_name:
                    matching_product = product
                    break

            # If no match by name, try checking keywords
            if matching_product is None:
                for product in products:
                    keywords = product.get("_keywords", [])
                    if any(ingredient_lower in kw for kw in keywords):
                        matching_product = product
                        break

            # If still no match, use the first product (fallback)
            if matching_product is None:
                matching_product = products[0]

            product = matching_product
            nutriments = product.get("nutriments", {})

            # Extract per-100g values (fallback to 0 if missing)
            return NutritionFacts(
                name=product.get("product_name", ingredient_name),
                kcal_per_100g=nutriments.get("energy-kcal_100g", 0.0),
                protein_g_per_100g=nutriments.get("proteins_100g", 0.0),
                carbs_g_per_100g=nutriments.get("carbohydrates_100g", 0.0),
                fat_g_per_100g=nutriments.get("fat_100g", 0.0),
                source="OpenFoodFacts",
            )

        except requests.RequestException as e:
            raise ProviderError(f"Open Food Facts request failed: {e}")
        except Exception as e:
            raise ProviderError(f"Failed to parse Open Food Facts response: {e}")
