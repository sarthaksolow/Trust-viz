import requests

BASE_URL = "http://localhost:5004"

def test_health_check():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data

def test_analyze_review():
    sample_review = {
        "review_id": "rev-001",
        "text": "This product is amazing! Highly recommend.",
        "reviewer_id": "user-123",
        "product_id": "prod-456",
        "timestamp": "2024-12-01T12:00:00Z",
        "is_verified": True,
        "rating": 5,
        "metadata": {
            "ip_address": "192.168.1.100",
            "device": "mobile"
        }
    }

    response = requests.post(f"{BASE_URL}/analyze", json=sample_review)
    assert response.status_code == 200

    data = response.json()

    assert data["review_id"] == "rev-001"
    assert isinstance(data["authenticity_score"], float)
    assert "is_suspicious" in data
    assert isinstance(data["components"], dict)
    assert "analysis_timestamp" in data
