"""Tests for cost telemetry."""

import tempfile
from datetime import datetime, timedelta

from src.telemetry.cost_meter import CostMeter


class TestCostMeter:
    """Test cost meter functionality."""

    def test_estimate_cost_known_model(self):
        """Test cost estimation for known model."""
        meter = CostMeter(db_path=":memory:")
        cost = meter.estimate_cost("openai", "gpt-4o-mini", 1000, 500)
        # (1000/1000)*0.00015 = 0.00015, (500/1000)*0.0006 = 0.0003
        assert cost == 0.00045

    def test_estimate_cost_unknown_model(self):
        """Test cost estimation falls back to default."""
        meter = CostMeter(db_path=":memory:")
        cost = meter.estimate_cost("unknown", "unknown-model", 1000, 500)
        assert cost > 0

    def test_record_and_get_report(self):
        """Test recording cost and getting report."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            meter = CostMeter(db_path=tmp.name)

            meter.record("openai", "gpt-4o-mini", 1000, 500, "test prompt")
            meter.record("gemini", "gemini-2.0-flash", 2000, 1000, "another prompt")

            report = meter.get_report()

            assert report["totals"]["total_calls"] == 2
            assert report["totals"]["total_prompt_tokens"] == 3000
            assert len(report["by_provider"]) == 2
            assert len(report["by_model"]) == 2

    def test_filter_by_provider(self):
        """Test filtering report by provider."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            meter = CostMeter(db_path=tmp.name)

            meter.record("openai", "gpt-4o-mini", 1000, 500)
            meter.record("gemini", "gemini-2.0-flash", 2000, 1000)

            report = meter.get_report(provider="openai")

            assert report["totals"]["total_calls"] == 1
            assert report["by_provider"][0]["provider"] == "openai"

    def test_filter_by_time(self):
        """Test filtering report by time range."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            meter = CostMeter(db_path=tmp.name)

            # Record old call
            old_time = datetime.now() - timedelta(days=2)
            meter.record("openai", "gpt-4o-mini", 1000, 500, timestamp=old_time)

            # Record recent call
            meter.record("openai", "gpt-4o-mini", 2000, 1000)

            report = meter.get_report(since=timedelta(hours=24))

            assert report["totals"]["total_calls"] == 1
            assert report["totals"]["total_prompt_tokens"] == 2000

    def test_clear(self):
        """Test clearing all records."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            meter = CostMeter(db_path=tmp.name)

            meter.record("openai", "gpt-4o-mini", 1000, 500)
            assert meter.get_report()["totals"]["total_calls"] == 1

            meter.clear()
            assert meter.get_report()["totals"]["total_calls"] == 0
