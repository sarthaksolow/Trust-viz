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

 
import time

try:
    # Send POST request to data ingestion service with retries
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post('http://localhost:8001/ingest', json=test_data, timeout=10)
            # Print response
            print("Response status code:", response.status_code)
            print("Response body:", response.json())
            break
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                print("Error: Max retries reached. Could not connect to the service.")
            time.sleep(2)  # Wait before retrying
            
 
except requests.exceptions.RequestException as e:
    print(f"Error sending request: {e}")
