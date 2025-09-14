

from walmartScraper import WalmartScraper
import json

# Initialize scraper
scraper = WalmartScraper()
urls = [
    "https://www.walmart.com/ip/Meta-Quest-2-All-in-One-Wireless-VR-Headset-256GB/519725606?classType=VARIANT&athbdg=L1600",
    "https://www.walmart.com/ip/B7-512GB-Jet-Black/16860058829?classType=VARIANT",
    "https://www.walmart.com/ip/Samsung-Galaxy-Watch8-40mm-Bluetooth-Silver/17030062000?classType=VARIANT&athbdg=L1600"
]

# Scrape all products with 2-second delay between requests
all_products = scraper.scrape_multiple_products(urls, delay=2.0)

# Save all results
# scraper.save_to_json(all_products, 'all_products.json')


# Function to save new data into the JSON file by appending it
def save_to_json_amend(new_data, file_name):
    try:
        # Try to open and read the existing data
        with open(file_name, 'r') as file:
            # Load the existing data
            existing_data = json.load(file)
    except FileNotFoundError:
        # If the file does not exist, initialize an empty list
        existing_data = []

    # Assuming the product data is a dictionary or list, append new data to it
    if isinstance(existing_data, list):
        existing_data.append(new_data)
    elif isinstance(existing_data, dict):
        # If it's a dictionary, you can merge or update keys as needed
        existing_data.update(new_data)

    # Save the amended data back to the JSON file
    with open(file_name, 'w') as file:
        json.dump(existing_data, file, indent=4)

# Example usage
save_to_json_amend(all_products, 'all_products.json')










# from walmartScraper import WalmartScraper
# import json

# # Initialize scraper
# scraper = WalmartScraper()

# # Single product
# url = "https://www.walmart.com/ip/Meta-Quest-2-All-in-One-Wireless-VR-Headset-256GB/519725606?classType=VARIANT&athbdg=L1600"
# product_data = scraper.get_product_info(url)

# # Print formatted JSON
# print(json.dumps(product_data, indent=2))

# # Save to file
# # scraper.save_to_json(product_data, 'product.json')


# # Function to save new data into the JSON file by appending it
# def save_to_json_amend(new_data, file_name):
#     try:
#         # Try to open and read the existing data
#         with open(file_name, 'r') as file:
#             # Load the existing data
#             existing_data = json.load(file)
#     except FileNotFoundError:
#         # If the file does not exist, initialize an empty list
#         existing_data = []

#     # Assuming the product data is a dictionary or list, append new data to it
#     if isinstance(existing_data, list):
#         existing_data.append(new_data)
#     elif isinstance(existing_data, dict):
#         # If it's a dictionary, you can merge or update keys as needed
#         existing_data.update(new_data)

#     # Save the amended data back to the JSON file
#     with open(file_name, 'w') as file:
#         json.dump(existing_data, file, indent=4)

# # Example usage
# save_to_json_amend(product_data, 'product.json')
