"""Token-aware rate limiter with sliding window."""

import asyncio
import time
from collections import deque
from typing import Dict, Optional, Tuple

from loguru import logger

# Provider rate limits (tokens per minute)
PROVIDER_LIMITS: Dict[Tuple[str, str], int] = {
    ("openai", "gpt-4o-mini"): 200000,
    ("openai", "gpt-4o"): 10000,
    ("anthropic", "claude-3-5-sonnet"): 50000,
    ("gemini", "gemini-2.0-flash"): 1000000,
}

DEFAULT_TPM_LIMIT = 50000


class TokenBudget:
    """Track token consumption in a sliding 60-second window."""

    def __init__(self, provider: str, model: str, tpm_limit: Optional[int] = None):
        self.provider = provider
        self.model = model
        key = (provider.lower(), model.lower())
        self.tpm_limit = tpm_limit or PROVIDER_LIMITS.get(key, DEFAULT_TPM_LIMIT)
        self._events: deque[Tuple[float, int]] = deque()  # (timestamp, tokens)
        self._lock = asyncio.Lock()
        logger.info(f"TokenBudget for {provider}/{model}: limit={self.tpm_limit} TPM")

    async def acquire(self, estimated_tokens: int) -> None:
        """Wait until token budget is available."""
        if estimated_tokens <= 0:
            return

        while True:
            async with self._lock:
                now = time.monotonic()
                self._cleanup(now)
                used = sum(t for _, t in self._events)

                if used + estimated_tokens <= self.tpm_limit:
                    self._events.append((now, estimated_tokens))
                    return

                # Calculate wait time until oldest token expires
                if self._events:
                    wait = 60 - (now - self._events[0][0])
                else:
                    wait = 0.1

            logger.debug(f"Rate limit: waiting {wait:.2f}s for {estimated_tokens} tokens")
            await asyncio.sleep(max(wait, 0.1))

    def _cleanup(self, now: float) -> None:
        """Remove events older than 60 seconds."""
        while self._events and self._events[0][0] < now - 60:
            self._events.popleft()

    def get_stats(self) -> dict:
        """Get current budget statistics."""
        now = time.monotonic()
        self._cleanup(now)
        used = sum(t for _, t in self._events)
        return {
            "provider": self.provider,
            "model": self.model,
            "tpm_limit": self.tpm_limit,
            "tokens_used_last_minute": used,
            "tokens_remaining": max(0, self.tpm_limit - used),
        }
