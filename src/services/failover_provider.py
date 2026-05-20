"""Failover provider that tries multiple providers in sequence."""

import logging
from typing import Dict, List, Optional

from ai.providers.base import LLMProvider, ProviderError, VLMProvider

logger = logging.getLogger(__name__)


class FailoverVLM(VLMProvider):
    """Wraps multiple VLM providers and fails over to the next on error."""

    def __init__(self, providers: List[VLMProvider]) -> None:
        if not providers:
            raise ValueError("At least one provider required")
        self.providers = providers
        self._active_index = 0
        logger.info(f"FailoverVLM initialized with {len(providers)} providers")

    def describe(
        self,
        image_path: str,
        prompt: str,
        *,
        json_schema: Optional[Dict] = None,
    ) -> str:
        last_error: Optional[Exception] = None

        for i, provider in enumerate(self.providers):
            try:
                logger.info(
                    f"Trying provider {i + 1}/{len(self.providers)}: {type(provider).__name__}"
                )
                result = provider.describe(image_path, prompt, json_schema=json_schema)
                self._active_index = i
                logger.info(f"Success with provider: {type(provider).__name__}")
                return result
            except (ProviderError, ConnectionError, TimeoutError) as e:
                logger.warning(f"Provider {type(provider).__name__} failed: {str(e)}")
                last_error = e
                continue

        raise ProviderError(
            f"All {len(self.providers)} providers failed. Last error: {last_error}"
        )


class FailoverLLM(LLMProvider):
    """Wraps multiple LLM providers and fails over to the next on error."""

    def __init__(self, providers: List[LLMProvider]) -> None:
        if not providers:
            raise ValueError("At least one provider required")
        self.providers = providers
        self._active_index = 0
        logger.info(f"FailoverLLM initialized with {len(providers)} providers")

    def complete(
        self,
        prompt: str,
        *,
        json_schema: Optional[Dict] = None,
        max_tokens: int = 1024,
    ) -> str:
        last_error: Optional[Exception] = None

        for i, provider in enumerate(self.providers):
            try:
                logger.info(
                    f"Trying provider {i + 1}/{len(self.providers)}: {type(provider).__name__}"
                )
                result = provider.complete(
                    prompt, json_schema=json_schema, max_tokens=max_tokens
                )
                self._active_index = i
                logger.info(f"Success with provider: {type(provider).__name__}")
                return result
            except (ProviderError, ConnectionError, TimeoutError) as e:
                logger.warning(f"Provider {type(provider).__name__} failed: {str(e)}")
                last_error = e
                continue

        raise ProviderError(
            f"All {len(self.providers)} providers failed. Last error: {last_error}"
        )
