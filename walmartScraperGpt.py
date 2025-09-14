from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re

# --------------------------
# 1. Extract Product ID from URL (optional)
# --------------------------
def get_product_id(url):
    match = re.search(r'/ip/(?:[\w-]+/)?(\d+)', url)
    if match:
        return match.group(1)
    return None

# --------------------------
# 2. Initialize Selenium WebDriver
# --------------------------
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # comment out if you want to see the browser
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')
    chrome_options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(service=Service("chromedriver.exe"), options=chrome_options)
    return driver

# --------------------------
# 3. Get Product Info
# --------------------------
def get_product_info(driver, url):
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    # Title
    try:
        title = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))).text.strip()
    except:
        title = None

    # Description
    try:
        desc_el = driver.find_element(By.CSS_SELECTOR, "div.about-desc, div.ProductDescription")
        description = desc_el.text.strip()
    except:
        description = None

    # Images
    images = []
    try:
        img_elements = driver.find_elements(By.CSS_SELECTOR, "img")
        for img in img_elements:
            src = img.get_attribute("src")
            if src and "walmartimages.com" in src:
                images.append(src)
    except:
        images = []

    return {
        "title": title,
        "description": description,
        "images": list(set(images))  # remove duplicates
    }

# --------------------------
# 4. Get Reviews (load all dynamically)
# --------------------------
def get_reviews(driver):
    reviews = []
    wait = WebDriverWait(driver, 5)

    # Scroll to first review to load section
    try:
        review_section = driver.find_element(By.CSS_SELECTOR, "div.Review")
        driver.execute_script("arguments[0].scrollIntoView();", review_section)
        time.sleep(2)
    except:
        pass

    # Click "See All Reviews" / "Load More" until gone
    while True:
        try:
            load_more = driver.find_element(By.CSS_SELECTOR, "button[data-automation-id='seeAllReviewsBtn']")
            driver.execute_script("arguments[0].click();", load_more)
            time.sleep(2)
        except:
            break

    # Collect all reviews
    review_elements = driver.find_elements(By.CSS_SELECTOR, "div.Review")
    for r in review_elements:
        try:
            reviewer = r.find_element(By.CSS_SELECTOR, "span.review-footer-userNickname").text.strip()
        except:
            reviewer = None
        try:
            rating_el = r.find_element(By.CSS_SELECTOR, "span.stars-container")
            rating = rating_el.get_attribute("aria-label")
        except:
            rating = None
        try:
            title = r.find_element(By.CSS_SELECTOR, "h3.review-title").text.strip()
        except:
            title = None
        try:
            text = r.find_element(By.CSS_SELECTOR, "div.review-text").text.strip()
        except:
            text = None
        try:
            date = r.find_element(By.CSS_SELECTOR, "span.review-date-submissionTime").text.strip()
        except:
            date = None

        reviews.append({
            "reviewer": reviewer,
            "rating": rating,
            "title": title,
            "text": text,
            "date": date
        })

    return reviews

# --------------------------
# 5. Scrape a single product
# --------------------------
def scrape_product(driver, url):
    product_data = get_product_info(driver, url)
    product_data["reviews"] = get_reviews(driver)
    return product_data

# --------------------------
# 6. Scrape multiple products
# --------------------------
def scrape_multiple_products(url_list):
    driver = init_driver()
    all_products = []

    for url in url_list:
        print(f"Scraping: {url}")
        try:
            data = scrape_product(driver, url)
            all_products.append(data)
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    driver.quit()
    return all_products

# --------------------------
# 7. Main
# --------------------------
if __name__ == "__main__":
    walmart_urls = [
        "https://www.walmart.com/ip/Samsung-Galaxy-Watch8-40mm-Bluetooth-Silver/17030062000",
        # Add more product URLs here
    ]

    all_data = scrape_multiple_products(walmart_urls)

    with open("walmart_products.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

    print("Data saved to walmart_products.json")
















# import requests
# from bs4 import BeautifulSoup
# import json
# import re

# # --------------------------
# # 1. Extract product ID from URL
# # --------------------------
# def get_product_id(url):
#     """
#     Extract the numeric product ID from a Walmart URL.
#     Works for URLs like:
#     /ip/12345678
#     /ip/Product-Name/12345678
#     """
#     match = re.search(r'/ip/(?:[\w-]+/)?(\d+)', url)
#     if match:
#         return match.group(1)
#     return None


# # --------------------------
# # 2. Get Product Info
# # --------------------------
# def get_product_info(url):
    
#     headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
#     "Accept": "application/json",
#     # "Referer": f"https://www.walmart.com/ip/{product_id}",
#     "x-requested-with": "XMLHttpRequest"
# }

#     response = requests.get(url, headers=headers)
#     soup = BeautifulSoup(response.text, 'lxml')

#     # Title
#     title_tag = soup.find("h1")
#     title = title_tag.text.strip() if title_tag else None

#     # Description
#     desc_tag = soup.find("div", {"class": re.compile(r'about-desc|ProductDescription')})
#     description = desc_tag.text.strip() if desc_tag else None

#     # Images
#     images = []
#     img_tags = soup.find_all("img")
#     for img in img_tags:
#         src = img.get("src")
#         if src and "https://i5.walmartimages.com" in src:
#             images.append(src)

#     return {
#         "title": title,
#         "description": description,
#         "images": list(set(images))  # remove duplicates
#     }

# # --------------------------
# # 3. Get Reviews via Walmart API
# # --------------------------
# def get_reviews(product_id, pages=5):
#     headers = {
#         "User-Agent": "Mozilla/5.0",
#         "Accept": "application/json"
#     }
#     reviews = []

#     for page in range(1, pages+1):
#         url = f"https://www.walmart.com/product-reviews/{product_id}?page={page}&format=json"
#         response = requests.get(url, headers=headers)

#         try:
#             data = response.json()
#             for r in data.get('reviews', []):
#                 reviews.append({
#                     "reviewer": r.get('displayName'),
#                     "rating": r.get('rating'),
#                     "title": r.get('title', ''),
#                     "text": r.get('reviewText', ''),
#                     "date": r.get('submissionTime', '')
#                 })
#         except Exception as e:
#             print(f"Error fetching reviews page {page} for product {product_id}: {e}")
#             break

#     return reviews

# # --------------------------
# # 4. Scrape a single product
# # --------------------------
# def scrape_walmart_product(url, review_pages=5):
#     product_id = get_product_id(url)
#     if not product_id:
#         print(f"Could not extract product ID from URL: {url}")
#         return None

#     product_data = get_product_info(url)
#     product_data["reviews"] = get_reviews(product_id, pages=review_pages)

#     return product_data

# # --------------------------
# # 5. Scrape multiple products
# # --------------------------
# def scrape_multiple_products(url_list, review_pages=5):
#     all_products = []

#     for url in url_list:
#         print(f"Scraping: {url}")
#         product_data = scrape_walmart_product(url, review_pages=review_pages)
#         if product_data:
#             all_products.append(product_data)

#     return all_products

# # --------------------------
# # 6. Main
# # --------------------------
# if __name__ == "__main__":
#     # List of Walmart URLs
#     walmart_urls = [
#         "https://www.walmart.com/ip/Samsung-Galaxy-Watch8-40mm-Bluetooth-Silver/17030062000?classType=VARIANT&athbdg=L1600",
#         "https://www.walmart.com/ip/Samsung-Galaxy-Watch8-40mm-Bluetooth-Silver/17030062000?classType=VARIANT&athbdg=L1600",
#         # add more URLs here
#     ]

#     data = scrape_multiple_products(walmart_urls, review_pages=10)  # adjust pages as needed

#     if data:
#         # Save JSON to file
#         with open("walmart_products.json", "w", encoding="utf-8") as f:
#             json.dump(data, f, indent=4, ensure_ascii=False)
#         print("Data saved to walmart_products.json")
#     else:
#         print("No products scraped.")
