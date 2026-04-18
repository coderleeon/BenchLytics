import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_app_import():
    # Sanity check: Ensure app imports correctly and is initialized
    assert app is not None
    assert app.title == "Benchlytics API"

def test_health_endpoint():
    # Test the root endpoint
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Benchlytics Backend Running"

def test_api_models():
    # Minimal viable test to ensure dynamic router imports are active
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], list)
