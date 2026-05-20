import requests
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ai import NutritionFacts, NutritionProvider
from ai.providers.base import ProviderError


def before_sleep_loguru_openfoodfacts(retry_state):
    """Custom before sleep callback for OpenFoodFacts retries."""
    logger.warning(
        f"OpenFoodFacts retry {retry_state.attempt_number}/3 "
        f"after error: {retry_state.outcome.exception()}"
    )


class OpenFoodFactsProvider(NutritionProvider):
    """Nutrition provider using Open Food Facts API."""

    BASE_URL = "https://world.openfoodfacts.net/api/v2"

    def __init__(self, user_agent: str, timeout: float = 10.0):
        self.user_agent = user_agent
        self.timeout = timeout
        logger.info(f"OpenFoodFactsProvider initialized with timeout={timeout}s")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, TimeoutError)),
        before_sleep=before_sleep_loguru_openfoodfacts,
        reraise=True,
    )
    def lookup(self, ingredient_name: str) -> NutritionFacts:
        """Look up nutrition facts for an ingredient."""
        if not ingredient_name or not ingredient_name.strip():
            raise ValueError("ingredient name must be non-empty")

        ingredient_name = ingredient_name.strip()
        logger.debug(f"Looking up nutrition for: '{ingredient_name}'")

        search_url = f"{self.BASE_URL}/search"
        params = {"search_terms": ingredient_name, "page_size": 10, "json": True}
        headers = {"User-Agent": self.user_agent}

        try:
            response = requests.get(
                search_url, params=params, headers=headers, timeout=self.timeout # type: ignore[arg-type]
            )

            if response.status_code == 503:
                logger.error(
                    f"OpenFoodFacts service unavailable (503) for '{ingredient_name}'"
                )
                raise ProviderError(
                    "OpenFoodFacts service temporarily unavailable (503). "
                    "Please try again later."
                )

            response.raise_for_status()
            data = response.json()

            products = data.get("products", [])
            if not products:
                raise ProviderError(f"No product found for: {ingredient_name}")

            # Find matching product
            matching_product = None
            ingredient_lower = ingredient_name.lower()

            for product in products:
                product_name = product.get("product_name", "").lower()
                if ingredient_lower in product_name:
                    matching_product = product
                    break

            if matching_product is None:
                for product in products:
                    keywords = product.get("_keywords", [])
                    if any(ingredient_lower in kw.lower() for kw in keywords):
                        matching_product = product
                        break

            if matching_product is None:
                matching_product = products[0]

            product = matching_product
            nutriments = product.get("nutriments", {})

            # Try multiple possible keys for each nutrient
            kcal = (
                nutriments.get("energy-kcal_100g")
                or nutriments.get("energy-kcal")
                or nutriments.get("energys-kcal_100g")
                or 0.0
            )

            protein = (
                nutriments.get("proteins_100g") or nutriments.get("proteins") or 0.0
            )

            carbs = (
                nutriments.get("carbohydrates_100g")
                or nutriments.get("carbohydrates")
                or 0.0
            )

            fat = nutriments.get("fat_100g") or nutriments.get("fat") or 0.0

            logger.debug(
                f"Found nutrition for '{ingredient_name}': {kcal}kcal, {protein}g protein"
            )

            return NutritionFacts(
                name=product.get("product_name", ingredient_name),
                kcal_per_100g=float(kcal),
                protein_g_per_100g=float(protein),
                carbs_g_per_100g=float(carbs),
                fat_g_per_100g=float(fat),
                source="OpenFoodFacts",
            )

        except ProviderError:
            raise
        except requests.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 503
            ):
                raise ProviderError(
                    f"OpenFoodFacts service unavailable (503): {e}"
                ) from e
            raise ProviderError(f"Open Food Facts request failed: {e}") from e
        except Exception as e:
            raise ProviderError(f"Failed to parse Open Food Facts response: {e}") from e
