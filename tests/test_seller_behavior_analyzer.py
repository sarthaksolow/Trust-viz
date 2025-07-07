import requests

BASE_URL = "http://localhost:5005"

def test_health_check():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data

def test_analyze_seller():
    payload = {
        "seller_id": "seller-001",
        "seller_name": "Test Seller",
        "account_created_at": "2023-01-01T00:00:00Z",
        "first_listing_date": "2023-02-01T00:00:00Z",
        "total_orders": 100,
        "total_sales": 15000.0,
        "products": [
            {
                "product_id": "prod-123",
                "title": "Product X",
                "description": "Test product description",
                "created_at": "2023-05-01T00:00:00Z",
                "price": 299.99,
                "category": "Electronics",
                "is_high_risk": False
            }
        ],
        "complaints": [
            {
                "complaint_id": "comp-123",
                "type": "fraud",
                "description": "Fake item received",
                "created_at": "2023-06-01T00:00:00Z",
                "result": "refunded"
            }
        ],
        "metadata": {
            "region": "EU",
            "flagged": True
        }
    }

    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["seller_id"] == "seller-001"
    assert isinstance(data["behavior_score"], float)
    assert data["risk_level"] in ["low", "medium", "high"]
    assert isinstance(data["components"], dict)
    assert "analysis_timestamp" in data
    assert isinstance(data["is_high_risk"], bool)
