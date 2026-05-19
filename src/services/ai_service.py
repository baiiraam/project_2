from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

from ai import identify_ingredients, Ingredient
from typing import List
from ai.providers.base import ProviderError

trigger_exceptions = (ConnectionError, TimeoutError, ProviderError)

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        logger.info("AIService initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(trigger_exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def service_identify_ingredients(self, image_path: str) -> List[Ingredient]:
        try:
            logger.info(f"identifying ingredients for image: {image_path}")
            ingredients = identify_ingredients(image_path)
            logger.info(f"identified ingredients: {[ing.name for ing in ingredients]}")
            return ingredients
        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            raise
