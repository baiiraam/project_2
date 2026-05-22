'''API tests'''

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from ai.schemas import Ingredient, NutritionFacts
from src.api.app import app

client = TestClient(app)


def test_analyze_with_valid_image(mocker):
    """Test analyze endpoint with valid image."""
    img_path = Path("data") / "cooked_turkey.jpeg"

    if not img_path.exists():
        pytest.skip(f"Test image not found: {img_path}")

    # Mock the VLM to avoid real API calls
    mock_ingredients = [
        Ingredient(name="chicken", estimated_grams=150, confidence=0.9),
        Ingredient(name="potatoes", estimated_grams=200, confidence=0.85),
        Ingredient(name="carrots", estimated_grams=80, confidence=0.8),
    ]

    # Mock the async method
    mocker.patch(
        "src.services.ai_service.AIService.service_identify_ingredients_async",
        return_value=mock_ingredients
    )

    # Also mock the nutrition provider to avoid USDA calls
    mock_facts = {
        "chicken": NutritionFacts(
            name="chicken", kcal_per_100g=165, protein_g_per_100g=31,
            carbs_g_per_100g=0, fat_g_per_100g=3.6, source="mock"
        ),
        "potatoes": NutritionFacts(
            name="potatoes", kcal_per_100g=77, protein_g_per_100g=2.0,
            carbs_g_per_100g=17, fat_g_per_100g=0.1, source="mock"
        ),
        "carrots": NutritionFacts(
            name="carrots", kcal_per_100g=41, protein_g_per_100g=0.9,
            carbs_g_per_100g=10, fat_g_per_100g=0.2, source="mock"
        ),
    }

    mocker.patch(
        "src.services.nutrition_cache.CachedNutritionProvider.async_lookup",
        side_effect=lambda name: mock_facts.get(name)
    )

    with open(img_path, "rb") as f:
        response = client.post(
            "/analyze", files={"file": ("test.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 200
    assert "totals" in response.json()
    assert response.json()["meal_recognized"] is True
    assert len(response.json()["ingredients"]) == 3


def test_analyze_with_invalid_file_type():
    """Test analyze with invalid file type."""
    response = client.post(
        "/analyze", files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 415


def test_analyze_with_no_file():
    """Test analyze with no file uploaded."""
    response = client.post("/analyze")
    assert response.status_code == 422  # Unprocessable Entity





"""Additional API tests for better coverage."""



client = TestClient(app)


class TestAPICoverage:
    """Test additional API endpoints and error cases."""

    def test_health_check(self):
        """Test health check endpoint."""
        with patch("src.storage.database.Database.health_check", return_value=True):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    def test_health_check_degraded(self):
        """Test health check when database is down."""
        with patch("src.storage.database.Database.health_check", return_value=False):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "degraded"
            assert response.json()["database"] == "disconnected"

    def test_cache_stats_endpoint(self):
        """Test cache stats endpoint."""
        with patch("src.api.app.get_cache_stats") as mock_stats:
            mock_stats.return_value = {"status": "enabled", "response_count": 10}
            response = client.get("/cache/stats")
            assert response.status_code == 200
            assert response.json()["status"] == "enabled"

    def test_cache_stats_disabled(self):
        """Test cache stats when disabled."""
        with patch("src.api.app.get_cache_stats", return_value=None):
            response = client.get("/cache/stats")
            assert response.status_code == 200
            assert response.json()["status"] == "disabled"

    def test_clear_cache_endpoint(self):
        """Test clear cache endpoint."""
        with patch("src.api.app.clear_cache", return_value=True):
            response = client.post("/cache/clear")
            assert response.status_code == 200
            assert response.json()["message"] == "Cache cleared successfully"

    def test_clear_cache_failure(self):
        """Test clear cache when it fails."""
        with patch("src.api.app.clear_cache", return_value=False):
            response = client.post("/cache/clear")
            assert response.status_code == 500

    def test_analyze_503_error(self, tmp_path):
        """Test analyze with 503 service unavailable."""
        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"fake image data")

        with patch("src.api.app.analyzer.analyze_async") as mock_analyze:
            from ai.providers.base import ProviderError
            mock_analyze.side_effect = ProviderError("503 Service Unavailable")

            with open(img_path, "rb") as f:
                response = client.post("/analyze", files={"file": ("test.jpg", f, "image/jpeg")})

            assert response.status_code == 503
            assert "temporarily unavailable" in response.json()["detail"].lower()

    def test_analyze_provider_error(self, tmp_path):
        """Test analyze with other provider errors."""
        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"fake image data")

        with patch("src.api.app.analyzer.analyze_async") as mock_analyze:
            from ai.providers.base import ProviderError
            mock_analyze.side_effect = ProviderError("API quota exceeded")

            with open(img_path, "rb") as f:
                response = client.post("/analyze", files={"file": ("test.jpg", f, "image/jpeg")})

            assert response.status_code == 500

    def test_analyze_unexpected_error(self, tmp_path):
        """Test analyze with unexpected error."""
        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"fake image data")

        with patch("src.api.app.analyzer.analyze_async") as mock_analyze:
            mock_analyze.side_effect = Exception("Unexpected error")

            with open(img_path, "rb") as f:
                response = client.post("/analyze", files={"file": ("test.jpg", f, "image/jpeg")})

            assert response.status_code == 500

    def test_root_endpoint(self):
        """Test root endpoint returns web UI or API info."""
        response = client.get("/")
        assert response.status_code == 200

        # Check if response is HTML (web UI) or JSON
        if "text/html" in response.headers.get("content-type", ""):
            # It's the web UI - check for HTML content
            assert "<title>" in response.text.lower() or "food" in response.text.lower()
        else:
            # It's JSON response
            assert "AI Food Analyzer" in response.json()["message"]
