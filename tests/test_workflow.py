import requests
import json
import time

# Sample test data for ingestion
test_data = {
    "seller_id": "test_seller_001",
    "product_id": "test_product_001",
    "product_name": "Test Product",
    "quantity": 10,
    "price": 99.99,
    "product_image_url": "https://example.com/product.jpg"
}

# Sample review data for Review Analyzer
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

# Sample seller data for Seller Behavior Analyzer
sample_seller = {
    "seller_id": "seller-001",
    "seller_name": "Test Seller",
    "account_created_at": "2023-01-01T12:00:00Z",
    "first_listing_date": "2023-02-01T12:00:00Z",
    "total_orders": 100,
    "total_sales": 5000.00,
    "products": [
        {
            "product_id": "prod-001",
            "title": "Test Product 1",
            "description": "A product for testing",
            "created_at": "2023-02-15T12:00:00Z",
            "price": 49.99,
            "category": "electronics",
            "is_high_risk": False
        }
    ],
    "complaints": [],
    "metadata": {}
}

def test_data_ingestion():
    print("Testing Data Ingestion Service...")
    try:
        response = requests.post('http://localhost:8001/ingest', json=test_data, timeout=10)
        print("Data Ingestion Response status code:", response.status_code)
        if response.status_code == 200:
            print("Data Ingestion Response body:", response.json())
            return True
        else:
            print("Unexpected status code from Data Ingestion")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error sending request to Data Ingestion: {e}")
        return False

def test_swarm_intelligence():
    print("\nTesting Swarm Intelligence Service...")
    try:
        response = requests.get('http://localhost:5001/health', timeout=10)
        print("Swarm Intelligence Response status code:", response.status_code)
        if response.status_code == 200:
            print("Swarm Intelligence Response body:", response.json())
            return True
        else:
            print("Unexpected status code from Swarm Intelligence")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error sending request to Swarm Intelligence: {e}")
        return False

def test_perceptual_ai():
    print("\nTesting Perceptual AI Service...")
    try:
        response = requests.get('http://localhost:5003/health', timeout=10)
        print("Perceptual AI Response status code:", response.status_code)
        if response.status_code == 200:
            print("Perceptual AI Response body:", response.json())
            return True
        else:
            print("Unexpected status code from Perceptual AI")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error sending request to Perceptual AI: {e}")
        return False

def test_trust_ledger():
    print("\nTesting Trust Ledger Service...")
    try:
        response = requests.get('http://localhost:8004/health', timeout=10)
        print("Trust Ledger Response status code:", response.status_code)
        if response.status_code == 200:
            print("Trust Ledger Response body:", response.json())
            return True
        else:
            print("Unexpected status code from Trust Ledger")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error sending request to Trust Ledger: {e}")
        return False

def test_review_analyzer():
    print("\nTesting Review Analyzer Service...")
    try:
        # Health check
        health_resp = requests.get('http://localhost:5004/health', timeout=10)
        print("Review Analyzer Health status code:", health_resp.status_code)
        if health_resp.status_code != 200:
            print("Review Analyzer Health check failed")
            return False
        print("Review Analyzer Health response:", health_resp.json())

        # Analyze review
        analyze_resp = requests.post('http://localhost:5004/analyze', json=sample_review, timeout=10)
        print("Review Analyzer Analyze status code:", analyze_resp.status_code)
        if analyze_resp.status_code == 200:
            print("Review Analyzer Analyze response:", analyze_resp.json())
            return True
        else:
            print("Unexpected status code from Review Analyzer Analyze endpoint")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error sending request to Review Analyzer: {e}")
        return False

def test_seller_behavior_analyzer():
    print("\nTesting Seller Behavior Analyzer Service...")
    try:
        # Health check
        health_resp = requests.get('http://localhost:5005/health', timeout=10)
        print("Seller Behavior Analyzer Health status code:", health_resp.status_code)
        if health_resp.status_code != 200:
            print("Seller Behavior Analyzer Health check failed")
            return False
        print("Seller Behavior Analyzer Health response:", health_resp.json())

        # Analyze seller
        analyze_resp = requests.post('http://localhost:5005/analyze', json=sample_seller, timeout=10)
        print("Seller Behavior Analyzer Analyze status code:", analyze_resp.status_code)
        if analyze_resp.status_code == 200:
            print("Seller Behavior Analyzer Analyze response:", analyze_resp.json())
            return True
        else:
            print("Unexpected status code from Seller Behavior Analyzer Analyze endpoint")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error sending request to Seller Behavior Analyzer: {e}")
        return False

def main():
    print("Starting Workflow Test for Trust-viz\n")
    
    # Ensure services are up by waiting a bit if needed
    print("Waiting for services to be fully operational...")
    time.sleep(5)
    
    # Run tests for each service
    ingestion_passed = test_data_ingestion()
    swarm_passed = test_swarm_intelligence()
    perceptual_passed = test_perceptual_ai()
    ledger_passed = test_trust_ledger()
    review_passed = test_review_analyzer()
    seller_passed = test_seller_behavior_analyzer()
    
    # Summary
    print("\nTest Summary:")
    print(f"Data Ingestion: {'PASSED' if ingestion_passed else 'FAILED'}")
    print(f"Swarm Intelligence: {'PASSED' if swarm_passed else 'FAILED'}")
    print(f"Perceptual AI: {'PASSED' if perceptual_passed else 'FAILED'}")
    print(f"Trust Ledger: {'PASSED' if ledger_passed else 'FAILED'}")
    print(f"Review Analyzer: {'PASSED' if review_passed else 'FAILED'}")
    print(f"Seller Behavior Analyzer: {'PASSED' if seller_passed else 'FAILED'}")
    
    if all([ingestion_passed, swarm_passed, perceptual_passed, ledger_passed, review_passed, seller_passed]):
        print("\nOverall Workflow Test: PASSED")
    else:
        print("\nOverall Workflow Test: FAILED")

if __name__ == "__main__":
    main()
