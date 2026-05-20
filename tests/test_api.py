"""Tests for API endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_analyze_with_valid_image():
    """Test analyze endpoint with valid image."""
    # Use path that works from project root
    img_path = Path("data") / "rice_chicken_broccoli.png"

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
