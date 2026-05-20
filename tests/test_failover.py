"""Chaos tests for failover provider."""

from unittest.mock import Mock

import pytest

from ai.providers.base import LLMProvider, ProviderError, VLMProvider
from src.services.failover_provider import FailoverLLM, FailoverVLM


class TestFailoverVLM:
    """Test VLM failover functionality."""

    def test_failover_uses_secondary_when_primary_fails(self):
        """Chaos test: primary fails, secondary succeeds."""
        primary = Mock(spec=VLMProvider)
        primary.describe.side_effect = ProviderError("upstream down")

        secondary = Mock(spec=VLMProvider)
        secondary.describe.return_value = '{"result": "from secondary"}'

        failover = FailoverVLM([primary, secondary])
        result = failover.describe("test.jpg", "prompt")

        assert result == '{"result": "from secondary"}'
        primary.describe.assert_called_once()
        secondary.describe.assert_called_once()

    def test_failover_uses_primary_when_it_works(self):
        """Test that primary is used when it succeeds."""
        primary = Mock(spec=VLMProvider)
        primary.describe.return_value = '{"result": "from primary"}'

        secondary = Mock(spec=VLMProvider)

        failover = FailoverVLM([primary, secondary])
        result = failover.describe("test.jpg", "prompt")

        assert result == '{"result": "from primary"}'
        primary.describe.assert_called_once()
        secondary.describe.assert_not_called()

    def test_failover_raises_when_all_providers_fail(self):
        """Test that error is raised when all providers fail."""
        primary = Mock(spec=VLMProvider)
        primary.describe.side_effect = ProviderError("primary down")

        secondary = Mock(spec=VLMProvider)
        secondary.describe.side_effect = ProviderError("secondary down")

        failover = FailoverVLM([primary, secondary])

        with pytest.raises(ProviderError, match="All 2 providers failed"):
            failover.describe("test.jpg", "prompt")

    def test_failover_requires_at_least_one_provider(self):
        """Test that constructor validates at least one provider."""
        with pytest.raises(ValueError, match="At least one provider required"):
            FailoverVLM([])


class TestFailoverLLM:
    """Test LLM failover functionality."""

    def test_failover_llm_uses_secondary_on_failure(self):
        """Chaos test: primary LLM fails, secondary succeeds."""
        primary = Mock(spec=LLMProvider)
        primary.complete.side_effect = ProviderError("primary down")

        secondary = Mock(spec=LLMProvider)
        secondary.complete.return_value = "from secondary"

        failover = FailoverLLM([primary, secondary])
        result = failover.complete("prompt")

        assert result == "from secondary"
        primary.complete.assert_called_once()
        secondary.complete.assert_called_once()

    def test_failover_llm_handles_connection_error(self):
        """Test that ConnectionError triggers failover."""
        primary = Mock(spec=LLMProvider)
        primary.complete.side_effect = ConnectionError("network down")

        secondary = Mock(spec=LLMProvider)
        secondary.complete.return_value = "from secondary"

        failover = FailoverLLM([primary, secondary])
        result = failover.complete("prompt")

        assert result == "from secondary"

    def test_failover_llm_handles_timeout(self):
        """Test that TimeoutError triggers failover."""
        primary = Mock(spec=LLMProvider)
        primary.complete.side_effect = TimeoutError("timeout")

        secondary = Mock(spec=LLMProvider)
        secondary.complete.return_value = "from secondary"

        failover = FailoverLLM([primary, secondary])
        result = failover.complete("prompt")

        assert result == "from secondary"

    def test_failover_llm_requires_at_least_one_provider(self):
        """Test that constructor validates at least one provider."""
        with pytest.raises(ValueError, match="At least one provider required"):
            FailoverLLM([])
