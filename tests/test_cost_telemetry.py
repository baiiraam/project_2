import pytest
from unittest.mock import patch, MagicMock
from src.telemetry.cost_meter import CostMeter

class TestCostMeter:

    @pytest.fixture
    def cost_meter_with_mocks(self):
        """Fixture that provides a CostMeter with all DB operations mocked."""
        with patch('src.telemetry.cost_meter.sqlite3.connect') as mock_connect, \
             patch('src.telemetry.cost_meter.CostMeter._init_db') as mock_init_db, \
             patch('src.telemetry.cost_meter.CostMeter.estimate_cost') as mock_estimate:

            # Setup mocks
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            # Create instance with mocked initialization
            meter = CostMeter(db_path=":memory:")
            meter._init_db = mock_init_db

            # Default estimate_cost behavior
            mock_estimate.return_value = 0.001

            yield meter, mock_cursor, mock_estimate, mock_connect

    def test_record_and_get_report(self, cost_meter_with_mocks):
        """Test recording cost and getting report."""
        meter, mock_cursor, mock_estimate, mock_connect = cost_meter_with_mocks

        # Mock get_report directly
        with patch.object(meter, 'get_report') as mock_get_report:
            mock_get_report.return_value = [
                {"provider": "openai", "model": "gpt-4o-mini", "cost_usd": 0.001},
            ]

            report = meter.get_report()
            assert len(report) == 1
            assert report[0]["provider"] == "openai"
            mock_get_report.assert_called_once()

    def test_clear(self, cost_meter_with_mocks):
        """Test clearing all records."""
        meter, mock_cursor, mock_estimate, mock_connect = cost_meter_with_mocks

        # Mock the clear method
        with patch.object(meter, 'clear') as mock_clear:
            meter.clear()
            mock_clear.assert_called_once()

    def test_estimate_cost_known_model(self, cost_meter_with_mocks):
        """Test cost estimation for known model."""
        meter, mock_cursor, mock_estimate, mock_connect = cost_meter_with_mocks

        # Configure mock for specific model
        mock_estimate.return_value = 0.0015

        cost = meter.estimate_cost("openai", "gpt-4o-mini", 1000, 500)

        mock_estimate.assert_called_with("openai", "gpt-4o-mini", 1000, 500)
        assert cost == 0.0015

    def test_estimate_cost_unknown_model(self, cost_meter_with_mocks):
        """Test cost estimation for unknown model."""
        meter, mock_cursor, mock_estimate, mock_connect = cost_meter_with_mocks

        # Configure mock for unknown model
        mock_estimate.return_value = 0.0

        cost = meter.estimate_cost("unknown", "unknown-model", 1000, 500)

        assert cost == 0.0

    def test_filter_by_provider(self, cost_meter_with_mocks):
        """Test filtering report by provider."""
        meter, mock_cursor, mock_estimate, mock_connect = cost_meter_with_mocks

        # Mock get_report with filter
        with patch.object(meter, 'get_report') as mock_get_report:
            mock_get_report.return_value = [
                {"provider": "openai", "model": "gpt-4o-mini", "cost_usd": 0.001},
            ]

            report = meter.get_report(provider="openai")

            mock_get_report.assert_called_with(provider="openai")
            assert len(report) == 1
            assert report[0]["provider"] == "openai"

    def test_filter_by_time(self, cost_meter_with_mocks):
        """Test filtering report by time range."""
        meter, mock_cursor, mock_estimate, mock_connect = cost_meter_with_mocks

        from datetime import datetime, timedelta
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()

        # Mock get_report with time filter
        with patch.object(meter, 'get_report') as mock_get_report:
            mock_get_report.return_value = [
                {"provider": "openai", "timestamp": datetime.now()},
            ]

            report = meter.get_report(start_time=start_time, end_time=end_time)

            mock_get_report.assert_called_with(start_time=start_time, end_time=end_time)
            assert len(report) == 1