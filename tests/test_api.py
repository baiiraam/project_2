from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)


def test_analyze_with_valid_image():
    with open("data/rice_chicken_broccoli.png", "rb") as f:
        response = client.post(
            "/analyze", files={"file": ("test.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 200
    assert "totals" in response.json()


def test_analyze_with_invalid_file_type():
    response = client.post(
        "/analyze", files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 415


def test_analyze_with_no_file():
    response = client.post("/analyze")
    assert response.status_code == 422  # Unprocessable Entity
