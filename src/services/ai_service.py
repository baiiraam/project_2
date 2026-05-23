# # # import asyncio
# # # from typing import List

# # # from loguru import logger
# # # from tenacity import (
# # #     retry,
# # #     retry_if_exception,
# # #     stop_after_attempt,
# # #     wait_exponential,
# # # )

# # # from ai import Ingredient, identify_ingredients
# # # from ai.providers.base import ProviderError


# # # def before_sleep_loguru(retry_state):
# # #     """Custom before sleep callback for loguru."""
# # #     logger.warning(
# # #         f"Retry {retry_state.attempt_number}/{retry_state.retry_object.stop.max_attempt_number} "
# # #         f"for {retry_state.fn.__name__} after error: {retry_state.outcome.exception()}"
# # #     )


# # # def is_retryable_exception(exception):
# # #     """Return True if we should retry, False for 503/service unavailable."""
# # #     if isinstance(exception, ProviderError):
# # #         # Check if it's a 503 error
# # #         if "503" in str(exception) or "UNAVAILABLE" in str(exception):
# # #             logger.warning(f"503 error detected, NOT retrying: {exception}")
# # #             return False
# # #     return isinstance(exception, (ConnectionError, TimeoutError, ProviderError))


# # # class AIService:
# # #     def __init__(self):
# # #         logger.info("AIService initialized")

# # #     @retry(
# # #         stop=stop_after_attempt(3),
# # #         wait=wait_exponential(multiplier=1, min=2, max=10),
# # #         retry=retry_if_exception(is_retryable_exception),
# # #         before_sleep=before_sleep_loguru,
# # #         reraise=True,
# # #     )
# # #     def service_identify_ingredients(self, image_path: str) -> List[Ingredient]:
# # #         """Synchronous version - blocks the event loop."""
# # #         try:
# # #             logger.info(f"identifying ingredients for image: {image_path}")
# # #             ingredients = identify_ingredients(image_path)
# # #             logger.info(f"identified ingredients: {[ing.name for ing in ingredients]}")
# # #             return ingredients
# # #         except FileNotFoundError:
# # #             logger.error(f"Image file not found: {image_path}")
# # #             raise

# # #     async def service_identify_ingredients_async(
# # #         self, image_path: str, timeout: float = 15.0
# # #     ) -> List[Ingredient]:
# # #         """Async version with timeout."""
# # #         try:
# # #             logger.info(f"[ASYNC] identifying ingredients for image: {image_path}")

# # #             loop = asyncio.get_event_loop()

# # #             # Add timeout to prevent hanging
# # #             ingredients = await asyncio.wait_for(
# # #                 loop.run_in_executor(
# # #                     None, self.service_identify_ingredients, image_path
# # #                 ),
# # #                 timeout=timeout,
# # #             )

# # #             logger.info(
# # #                 f"[ASYNC] identified ingredients: {[ing.name for ing in ingredients]}"
# # #             )
# # #             return ingredients

# # #         except asyncio.TimeoutError:
# # #             logger.error(f"VLM call timed out after {timeout}s for {image_path}")
# # #             raise ProviderError(f"VLM service timeout after {timeout}s")
# # #         except FileNotFoundError:
# # #             logger.error(f"Image file not found: {image_path}")
# # #             raise
# # #         except Exception as e:
# # #             logger.error(f"Unexpected error in async identify: {e}")
# # #             raise

































# # """AI Service with retries, logging, and optional failover."""

# # import asyncio
# # import os
# # from typing import List, Optional

# # from loguru import logger
# # from tenacity import (
# #     retry,
# #     retry_if_exception,
# #     stop_after_attempt,
# #     wait_exponential,
# # )

# # from ai import Ingredient, identify_ingredients
# # from ai.providers.base import ProviderError, VLMProvider
# # from src.services.failover_provider import FailoverVLM


# # def before_sleep_loguru(retry_state):
# #     """Custom before sleep callback for loguru."""
# #     logger.warning(
# #         f"Retry {retry_state.attempt_number}/{retry_state.retry_object.stop.max_attempt_number} "
# #         f"for {retry_state.fn.__name__} after error: {retry_state.outcome.exception()}"
# #     )


# # def is_retryable_exception(exception):
# #     """Return True if we should retry, False for 503/service unavailable."""
# #     if isinstance(exception, ProviderError):
# #         if "503" in str(exception) or "UNAVAILABLE" in str(exception):
# #             logger.warning(f"503 error detected, NOT retrying: {exception}")
# #             return False
# #     return isinstance(exception, (ConnectionError, TimeoutError, ProviderError))


# # class AIService:
# #     def __init__(self, enable_failover: bool = None):
# #         """Initialize AIService with optional failover.

# #         Args:
# #             enable_failover: If True, use FailoverVLM with all available providers.
# #                             If False, use single provider from get_vlm().
# #                             If None, read from FAILOVER_ENABLED env var.
# #         """
# #         if enable_failover is None:
# #             enable_failover = os.getenv("FAILOVER_ENABLED", "false").lower() == "true"

# #         self.enable_failover = enable_failover
# #         self._vlm_provider: Optional[VLMProvider] = None
# #         logger.info(f"AIService initialized (failover={self.enable_failover})")

# #     def _get_vlm_provider(self) -> VLMProvider:
# #         """Create VLM provider with optional failover."""
# #         if self._vlm_provider is not None:
# #             return self._vlm_provider

# #         if not self.enable_failover:
# #             # Original behavior: let ai/ decide which provider to use
# #             self._vlm_provider = None  # None tells identify_ingredients to use get_vlm()
# #             return None  # Special value - will use default

# #         # Failover mode: create all available providers
# #         providers = []

# #         # Try to create OpenAI provider
# #         if os.getenv("OPENAI_API_KEY"):
# #             try:
# #                 from ai.providers.openai import OpenAIVLM
# #                 model = os.getenv("LLM_MODEL", "gpt-4o-mini")
# #                 providers.append(OpenAIVLM(model=model))
# #                 logger.info("OpenAI provider added to failover list")
# #             except Exception as e:
# #                 logger.warning(f"Failed to create OpenAI provider: {e}")

# #         # Try to create Anthropic provider
# #         if os.getenv("ANTHROPIC_API_KEY"):
# #             try:
# #                 from ai.providers.anthropic import AnthropicVLM
# #                 model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
# #                 providers.append(AnthropicVLM(model=model))
# #                 logger.info("Anthropic provider added to failover list")
# #             except Exception as e:
# #                 logger.warning(f"Failed to create Anthropic provider: {e}")

# #         # Try to create Gemini provider
# #         if os.getenv("GOOGLE_API_KEY"):
# #             try:
# #                 from ai.providers.google import GeminiVLM
# #                 model = os.getenv("LLM_MODEL", "gemini-2.0-flash")
# #                 providers.append(GeminiVLM(model=model))
# #                 logger.info("Gemini provider added to failover list")
# #             except Exception as e:
# #                 logger.warning(f"Failed to create Gemini provider: {e}")

# #         if not providers:
# #             logger.warning("No providers available for failover, falling back to default")
# #             self._vlm_provider = None
# #             return None

# #         # Wrap with failover
# #         self._vlm_provider = FailoverVLM(providers)
# #         logger.info(f"FailoverVLM created with {len(providers)} providers")
# #         return self._vlm_provider

# #     @retry(
# #         stop=stop_after_attempt(3),
# #         wait=wait_exponential(multiplier=1, min=2, max=10),
# #         retry=retry_if_exception(is_retryable_exception),
# #         before_sleep=before_sleep_loguru,
# #         reraise=True,
# #     )
# #     def service_identify_ingredients(self, image_path: str) -> List[Ingredient]:
# #         """Synchronous version - blocks the event loop."""
# #         try:
# #             logger.info(f"identifying ingredients for image: {image_path}")

# #             vlm = self._get_vlm_provider()

# #             # Pass vlm to identify_ingredients if we have one
# #             if vlm is not None:
# #                 ingredients = identify_ingredients(image_path, vlm=vlm)
# #             else:
# #                 ingredients = identify_ingredients(image_path)

# #             logger.info(f"identified ingredients: {[ing.name for ing in ingredients]}")
# #             return ingredients
# #         except FileNotFoundError:
# #             logger.error(f"Image file not found: {image_path}")
# #             raise

# #     async def service_identify_ingredients_async(
# #         self, image_path: str, timeout: float = 15.0
# #     ) -> List[Ingredient]:
# #         """Async version with timeout."""
# #         try:
# #             logger.info(f"[ASYNC] identifying ingredients for image: {image_path}")

# #             loop = asyncio.get_event_loop()

# #             vlm = self._get_vlm_provider()

# #             # Pass vlm to identify_ingredients if we have one
# #             if vlm is not None:
# #                 ingredients = await asyncio.wait_for(
# #                     loop.run_in_executor(
# #                         None, lambda: identify_ingredients(image_path, vlm=vlm)
# #                     ),
# #                     timeout=timeout,
# #                 )
# #             else:
# #                 ingredients = await asyncio.wait_for(
# #                     loop.run_in_executor(
# #                         None, lambda: identify_ingredients(image_path)
# #                     ),
# #                     timeout=timeout,
# #                 )

# #             logger.info(
# #                 f"[ASYNC] identified ingredients: {[ing.name for ing in ingredients]}"
# #             )
# #             return ingredients

# #         except asyncio.TimeoutError:
# #             logger.error(f"VLM call timed out after {timeout}s for {image_path}")
# #             raise ProviderError(f"VLM service timeout after {timeout}s")
# #         except FileNotFoundError:
# #             logger.error(f"Image file not found: {image_path}")
# #             raise
# #         except Exception as e:
# #             logger.error(f"Unexpected error in async identify: {e}")
# #             raise




























# """AI Service with retries, logging, and optional failover."""

# import asyncio
# from typing import List

# from src.telemetry.cost_meter import get_cost_meter

# from loguru import logger
# from tenacity import (
#     retry,
#     retry_if_exception,
#     stop_after_attempt,
#     wait_exponential,
# )

# from ai import Ingredient, identify_ingredients
# from ai.providers.base import ProviderError
# from src.config import get_settings

# from src.services.token_rate_limiter import TokenBudget
# from ai.vlm import _PROMPT


# def before_sleep_loguru(retry_state):
#     """Custom before sleep callback for loguru."""
#     logger.warning(
#         f"Retry {retry_state.attempt_number}/{retry_state.retry_object.stop.max_attempt_number} "
#         f"for {retry_state.fn.__name__} after error: {retry_state.outcome.exception()}"
#     )


# def is_retryable_exception(exception):
#     """Return True if we should retry, False for 503/service unavailable."""
#     if isinstance(exception, ProviderError):
#         if "503" in str(exception) or "UNAVAILABLE" in str(exception):
#             logger.warning(f"503 error detected, NOT retrying: {exception}")
#             return False
#     return isinstance(exception, (ConnectionError, TimeoutError, ProviderError))


# class AIService:
#     def __init__(self):
#         self.settings = get_settings()
#         self._budgets: dict = {}  # Add this line
#         logger.info("AIService initialized")

#     def _get_budget(self, provider: str, model: str) -> TokenBudget:
#         """Get or create token budget for a provider/model."""
#         key = f"{provider}:{model}"
#         if key not in self._budgets:
#             self._budgets[key] = TokenBudget(provider, model)
#         return self._budgets[key]

#     # @retry(
#     #     stop=stop_after_attempt(3),
#     #     wait=wait_exponential(multiplier=1, min=2, max=10),
#     #     retry=retry_if_exception(is_retryable_exception),
#     #     before_sleep=before_sleep_loguru,
#     #     reraise=True,
#     # )
#     # def service_identify_ingredients(self, image_path: str) -> List[Ingredient]:
#     #     """Synchronous version - blocks the event loop."""
#     #     try:
#     #         logger.info(f"identifying ingredients for image: {image_path}")

#     #         # Get VLM provider from settings (handles failover logic)
#     #         vlm = self.settings.get_vlm_provider()

#     #         if vlm is not None:
#     #             ingredients = identify_ingredients(image_path, vlm=vlm)
#     #         else:
#     #             ingredients = identify_ingredients(image_path)

#     #         logger.info(f"identified ingredients: {[ing.name for ing in ingredients]}")
#     #         return ingredients
#     #     except FileNotFoundError:
#     #         logger.error(f"Image file not found: {image_path}")
#     #         raise


#     @retry(
#         stop=stop_after_attempt(3),
#         wait=wait_exponential(multiplier=1, min=2, max=10),
#         retry=retry_if_exception(is_retryable_exception),
#         before_sleep=before_sleep_loguru,
#         reraise=True,
#     )
#     def service_identify_ingredients(self, image_path: str) -> List[Ingredient]:
#         """Synchronous version - blocks the event loop."""
#         try:
#             logger.info(f"identifying ingredients for image: {image_path}")

#             # Get VLM provider from settings (handles failover logic)
#             vlm = self.settings.get_vlm_provider()

#             # Cost telemetry
#             cost_meter = get_cost_meter()
#             provider_name = self.settings.LLM_PROVIDER
#             model_name = self.settings.LLM_MODEL or "unknown"

#             # Get the prompt from ai/vlm.py
#             from ai.vlm import _PROMPT

#             with cost_meter.record_context(provider_name, model_name, _PROMPT) as ctx:
#                 if vlm is not None:
#                     ingredients = identify_ingredients(image_path, vlm=vlm)
#                 else:
#                     ingredients = identify_ingredients(image_path)

#                 # Estimate tokens (rough approximation)
#                 # In production, you'd extract actual token counts from API response
#                 ctx.prompt_tokens = len(_PROMPT) // 4
#                 ctx.completion_tokens = len(str(ingredients)) // 4

#             logger.info(f"identified ingredients: {[ing.name for ing in ingredients]}")
#             return ingredients
#         except FileNotFoundError:
#             logger.error(f"Image file not found: {image_path}")
#             raise






#     # async def service_identify_ingredients_async(
#     #     self, image_path: str, timeout: float = 15.0
#     # ) -> List[Ingredient]:
#     #     """Async version with timeout."""
#     #     try:
#     #         logger.info(f"[ASYNC] identifying ingredients for image: {image_path}")

#     #         loop = asyncio.get_event_loop()

#     #         vlm = self.settings.get_vlm_provider()

#     #         if vlm is not None:
#     #             ingredients = await asyncio.wait_for(
#     #                 loop.run_in_executor(
#     #                     None, lambda: identify_ingredients(image_path, vlm=vlm)
#     #                 ),
#     #                 timeout=timeout,
#     #             )
#     #         else:
#     #             ingredients = await asyncio.wait_for(
#     #                 loop.run_in_executor(
#     #                     None, lambda: identify_ingredients(image_path)
#     #                 ),
#     #                 timeout=timeout,
#     #             )

#     #         logger.info(
#     #             f"[ASYNC] identified ingredients: {[ing.name for ing in ingredients]}"
#     #         )
#     #         return ingredients

#     #     except asyncio.TimeoutError:
#     #         logger.error(f"VLM call timed out after {timeout}s for {image_path}")
#     #         raise ProviderError(f"VLM service timeout after {timeout}s")
#     #     except FileNotFoundError:
#     #         logger.error(f"Image file not found: {image_path}")
#     #         raise
#     #     except Exception as e:
#     #         logger.error(f"Unexpected error in async identify: {e}")
#     #         raise






#     @retry(
#         stop=stop_after_attempt(3),
#         wait=wait_exponential(multiplier=1, min=2, max=10),
#         retry=retry_if_exception(is_retryable_exception),
#         before_sleep=before_sleep_loguru,
#         reraise=True,
#     )
#     async def service_identify_ingredients_async(
#         self, image_path: str, timeout: float = 15.0
#     ) -> List[Ingredient]:
#         """Async version with timeout."""
#         try:
#             logger.info(f"[ASYNC] identifying ingredients for image: {image_path}")

#             loop = asyncio.get_event_loop()
#             vlm = self.settings.get_vlm_provider()

#             # Cost telemetry
#             cost_meter = get_cost_meter()
#             provider_name = self.settings.LLM_PROVIDER
#             model_name = self.settings.LLM_MODEL or "unknown"

#             # ========== TOKEN RATE LIMITER (NEW) ==========
#             budget = self._get_budget(provider_name, model_name)
#             await budget.acquire(1500)  # Estimate 1500 tokens for VLM call
#             # =============================================


#             with cost_meter.record_context(provider_name, model_name, _PROMPT) as ctx:
#                 if vlm is not None:
#                     ingredients = await asyncio.wait_for(
#                         loop.run_in_executor(
#                             None, lambda: identify_ingredients(image_path, vlm=vlm)
#                         ),
#                         timeout=timeout,
#                     )
#                 else:
#                     ingredients = await asyncio.wait_for(
#                         loop.run_in_executor(
#                             None, lambda: identify_ingredients(image_path)
#                         ),
#                         timeout=timeout,
#                     )

#                 ctx.prompt_tokens = len(_PROMPT) // 4
#                 ctx.completion_tokens = len(str(ingredients)) // 4

#             logger.info(
#                 f"[ASYNC] identified ingredients: {[ing.name for ing in ingredients]}"
#             )
#             return ingredients

#         except asyncio.TimeoutError:
#             logger.error(f"VLM call timed out after {timeout}s for {image_path}")
#             raise ProviderError(f"VLM service timeout after {timeout}s")
#         except FileNotFoundError:
#             logger.error(f"Image file not found: {image_path}")
#             raise
#         except Exception as e:
#             logger.error(f"Unexpected error in async identify: {e}")
#             raise
















































"""AI Service with retries, logging, and optional failover."""

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
from ai.vlm import _PROMPT
from src.config import get_settings
from src.services.token_rate_limiter import TokenBudget
from src.telemetry import get_cost_meter, get_tracer


def before_sleep_loguru(retry_state):
    """Custom before sleep callback for loguru."""
    logger.warning(
        f"Retry {retry_state.attempt_number}/{retry_state.retry_object.stop.max_attempt_number} "
        f"for {retry_state.fn.__name__} after error: {retry_state.outcome.exception()}"
    )


def is_retryable_exception(exception):
    """Return True if we should retry, False for 503/service unavailable."""
    if isinstance(exception, ProviderError):
        if "503" in str(exception) or "UNAVAILABLE" in str(exception):
            logger.warning(f"503 error detected, NOT retrying: {exception}")
            return False
    return isinstance(exception, (ConnectionError, TimeoutError, ProviderError))


class AIService:
    def __init__(self):
        self.settings = get_settings()
        self._budgets: dict = {}
        self.tracer = get_tracer()
        logger.info("AIService initialized")

    def _get_budget(self, provider: str, model: str) -> TokenBudget:
        """Get or create token budget for a provider/model."""
        key = f"{provider}:{model}"
        if key not in self._budgets:
            self._budgets[key] = TokenBudget(provider, model)
        return self._budgets[key]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(is_retryable_exception),
        before_sleep=before_sleep_loguru,
        reraise=True,
    )
    def service_identify_ingredients(self, image_path: str) -> List[Ingredient]:
        """Synchronous version - blocks the event loop."""
        with self.tracer.start_as_current_span("ai_service.identify_ingredients_sync") as span:
            span.set_attribute("image_path", image_path)
            span.set_attribute("provider", self.settings.LLM_PROVIDER)
            span.set_attribute("model", self.settings.LLM_MODEL or "unknown")

            try:
                logger.info(f"identifying ingredients for image: {image_path}")

                # Get VLM provider from settings (handles failover logic)
                vlm = self.settings.get_vlm_provider()

                # Cost telemetry
                cost_meter = get_cost_meter()
                provider_name = self.settings.LLM_PROVIDER
                model_name = self.settings.LLM_MODEL or "unknown"

                with cost_meter.record_context(provider_name, model_name, _PROMPT) as ctx:
                    if vlm is not None:
                        ingredients = identify_ingredients(image_path, vlm=vlm)
                    else:
                        ingredients = identify_ingredients(image_path)

                    ctx.prompt_tokens = len(_PROMPT) // 4
                    ctx.completion_tokens = len(str(ingredients)) // 4

                span.set_attribute("num_ingredients", len(ingredients))
                span.set_attribute("status", "success")
                logger.info(f"identified ingredients: {[ing.name for ing in ingredients]}")
                return ingredients
            except FileNotFoundError:
                logger.error(f"Image file not found: {image_path}")
                span.set_attribute("status", "error")
                raise
            except Exception as e:
                span.set_attribute("status", "error")
                span.record_exception(e)
                raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(is_retryable_exception),
        before_sleep=before_sleep_loguru,
        reraise=True,
    )
    async def service_identify_ingredients_async(
        self, image_path: str, timeout: float = 15.0
    ) -> List[Ingredient]:
        """Async version with timeout."""
        with self.tracer.start_as_current_span("ai_service.identify_ingredients_async") as span:
            span.set_attribute("image_path", image_path)
            span.set_attribute("provider", self.settings.LLM_PROVIDER)
            span.set_attribute("model", self.settings.LLM_MODEL or "unknown")

            try:
                logger.info(f"[ASYNC] identifying ingredients for image: {image_path}")

                loop = asyncio.get_event_loop()
                vlm = self.settings.get_vlm_provider()

                # Cost telemetry
                cost_meter = get_cost_meter()
                provider_name = self.settings.LLM_PROVIDER
                model_name = self.settings.LLM_MODEL or "unknown"

                # Token rate limiter
                budget = self._get_budget(provider_name, model_name)
                await budget.acquire(1500)

                with cost_meter.record_context(provider_name, model_name, _PROMPT) as ctx:
                    if vlm is not None:
                        ingredients = await asyncio.wait_for(
                            loop.run_in_executor(
                                None, lambda: identify_ingredients(image_path, vlm=vlm)
                            ),
                            timeout=timeout,
                        )
                    else:
                        ingredients = await asyncio.wait_for(
                            loop.run_in_executor(
                                None, lambda: identify_ingredients(image_path)
                            ),
                            timeout=timeout,
                        )

                    ctx.prompt_tokens = len(_PROMPT) // 4
                    ctx.completion_tokens = len(str(ingredients)) // 4

                span.set_attribute("num_ingredients", len(ingredients))
                span.set_attribute("status", "success")
                logger.info(
                    f"[ASYNC] identified ingredients: {[ing.name for ing in ingredients]}"
                )
                return ingredients

            except asyncio.TimeoutError:
                logger.error(f"VLM call timed out after {timeout}s for {image_path}")
                span.set_attribute("status", "timeout")
                raise ProviderError(f"VLM service timeout after {timeout}s")
            except FileNotFoundError:
                logger.error(f"Image file not found: {image_path}")
                span.set_attribute("status", "error")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in async identify: {e}")
                span.set_attribute("status", "error")
                span.record_exception(e)
                raise
