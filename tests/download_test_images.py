import requests
import os

# Create test_images directory if it doesn't exist
os.makedirs('test_images', exist_ok=True)

# Image URLs and their corresponding filenames
images = {
    'seller.jpg': 'https://images.squarespace-cdn.com/content/v1/5ab94f5e3c3a536987d16ce5/1553621431674-2EQGHV5O5Y0PET3L86CJ/abibas-TFE.jpg',
    'brand1.jpg': 'https://m.media-amazon.com/images/I/71G1hGj4QeL._AC_UY1000_.jpg',
    'brand2.jpg': 'https://m.media-amazon.com/images/I/61F8rZ0i5VL._AC_UY1000_.jpg'
}

# Download and save each image
for filename, url in images.items():
    try:
        print(f"Downloading {filename}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(f'test_images/{filename}', 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully saved {filename}")
        
    except Exception as e:
        print(f"Error downloading {filename}: {str(e)}")

print("\nTest images downloaded successfully!")
