import requests
import json

# Sample test data
test_data = {
    "seller_id": "test_seller_001",
    "product_id": "test_product_001",
    "product_name": "Test Product",
    "quantity": 10,
    "price": 99.99,
    "product_image_url": "https://example.com/product.jpg"
}

try:
    # (Send POST request to data ingestion service)
    response = requests.post('http://localhost:8001/ingest', json=test_data)
    
    # Print response
    print("Response status code:", response.status_code)
    print("Response body:", response.json())
    
except requests.exceptions.RequestException as e:
    print(f"Error sending request: {e}")
