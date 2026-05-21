"""Tests for OpenFoodFacts provider."""

import pytest
from unittest.mock import patch, MagicMock
import requests

from ai.providers.base import ProviderError


class TestOpenFoodFactsProvider:
    """Test OpenFoodFacts nutrition provider."""

    @pytest.fixture
    def provider(self):
        from src.services.openfoodfacts_provider import OpenFoodFactsProvider
        return OpenFoodFactsProvider(user_agent="Test/1.0", timeout=5.0)

    def test_lookup_success(self, provider):
        """Test successful lookup."""
        mock_response = {
            "products": [{
                "product_name": "White Rice",
                "nutriments": {
                    "energy-kcal_100g": 130,
                    "proteins_100g": 2.7,
                    "carbohydrates_100g": 28,
                    "fat_100g": 0.3
                }
            }]
        }

        with patch("requests.get") as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_get.return_value = mock_response_obj

            result = provider.lookup("rice")
            assert result.name == "White Rice"
            assert result.kcal_per_100g == 130

    def test_lookup_with_alternative_nutrient_keys(self, provider):
        """Test lookup with different nutrient key formats."""
        mock_response = {
            "products": [{
                "product_name": "Chicken Breast",
                "nutriments": {
                    "energy-kcal": 165, "proteins": 31,
                    "carbohydrates": 0, "fat": 3.6
                }
            }]
        }

        with patch("requests.get") as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_get.return_value = mock_response_obj

            result = provider.lookup("chicken")
            assert result.kcal_per_100g == 165

    def test_lookup_no_products_found(self, provider):
        """Test lookup when no products match."""
        mock_response = {"products": []}

        with patch("requests.get") as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_get.return_value = mock_response_obj

            with pytest.raises(ProviderError, match="No product found"):
                provider.lookup("unknown ingredient")

    def test_lookup_503_error(self, provider):
        """Test lookup with 503 service unavailable."""
        with patch("requests.get") as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 503
            mock_get.return_value = mock_response_obj

            with pytest.raises(ProviderError, match="503"):
                provider.lookup("rice")

    def test_lookup_connection_error(self, provider):
        """Test lookup with connection error."""
        with patch("requests.get", side_effect=requests.ConnectionError("Network error")):
            with pytest.raises(ProviderError, match="request failed"):
                provider.lookup("rice")

    def test_lookup_timeout(self, provider):
        """Test lookup with timeout."""
        with patch("requests.get", side_effect=requests.Timeout("Timeout")):
            with pytest.raises(ProviderError, match="request failed"):
                provider.lookup("rice")

    def test_lookup_empty_ingredient_name(self, provider):
        """Test lookup with empty ingredient name."""
        with pytest.raises(ValueError, match="non-empty"):
            provider.lookup("")
        with pytest.raises(ValueError, match="non-empty"):
            provider.lookup("   ")