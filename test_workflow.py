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
    
    # Summary
    print("\nTest Summary:")
    print(f"Data Ingestion: {'PASSED' if ingestion_passed else 'FAILED'}")
    print(f"Swarm Intelligence: {'PASSED' if swarm_passed else 'FAILED'}")
    print(f"Perceptual AI: {'PASSED' if perceptual_passed else 'FAILED'}")
    print(f"Trust Ledger: {'PASSED' if ledger_passed else 'FAILED'}")
    
    if all([ingestion_passed, swarm_passed, perceptual_passed, ledger_passed]):
        print("\nOverall Workflow Test: PASSED")
    else:
        print("\nOverall Workflow Test: FAILED")

if __name__ == "__main__":
    main()
