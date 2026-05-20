import asyncio
from typing import List

from loguru import logger
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from ai import Ingredient, identify_ingredients
from ai.providers.base import ProviderError


def before_sleep_loguru(retry_state):
    """Custom before sleep callback for loguru."""
    logger.warning(
        f"Retry {retry_state.attempt_number}/{retry_state.retry_object.stop.max_attempt_number} "
        f"for {retry_state.fn.__name__} after error: {retry_state.outcome.exception()}"
    )


def is_retryable_exception(exception):
    """Return True if we should retry, False for 503/service unavailable."""
    if isinstance(exception, ProviderError):
        # Check if it's a 503 error
        if "503" in str(exception) or "UNAVAILABLE" in str(exception):
            logger.warning(f"503 error detected, NOT retrying: {exception}")
            return False
    return isinstance(exception, (ConnectionError, TimeoutError, ProviderError))


class AIService:
    def __init__(self):
        logger.info("AIService initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(is_retryable_exception),
        before_sleep=before_sleep_loguru,
        reraise=True,
    )
    def service_identify_ingredients(self, image_path: str) -> List[Ingredient]:
        """Synchronous version - blocks the event loop."""
        try:
            logger.info(f"identifying ingredients for image: {image_path}")
            ingredients = identify_ingredients(image_path)
            logger.info(f"identified ingredients: {[ing.name for ing in ingredients]}")
            return ingredients
        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            raise

    async def service_identify_ingredients_async(
        self, image_path: str, timeout: float = 15.0
    ) -> List[Ingredient]:
        """Async version with timeout."""
        try:
            logger.info(f"[ASYNC] identifying ingredients for image: {image_path}")

            loop = asyncio.get_event_loop()

            # Add timeout to prevent hanging
            ingredients = await asyncio.wait_for(
                loop.run_in_executor(
                    None, self.service_identify_ingredients, image_path
                ),
                timeout=timeout,
            )

            logger.info(
                f"[ASYNC] identified ingredients: {[ing.name for ing in ingredients]}"
            )
            return ingredients

        except asyncio.TimeoutError:
            logger.error(f"VLM call timed out after {timeout}s for {image_path}")
            raise ProviderError(f"VLM service timeout after {timeout}s")
        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in async identify: {e}")
            raise
