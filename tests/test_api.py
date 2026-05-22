"""Tests for API endpoints."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_analyze_with_valid_image():
    """Test analyze endpoint with valid image."""
    # Use path that works from project root
    img_path = Path("data") / "cooked_turkey.jpeg"

    # Skip test if file doesn't exist
    if not img_path.exists():
        pytest.skip(f"Test image not found: {img_path}")

    with open(img_path, "rb") as f:
        response = client.post(
            "/analyze", files={"file": ("test.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 200
    assert "totals" in response.json()


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
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "AI Food Analyzer" in response.json()["message"]
