#!/usr/bin/env python3
"""
Standalone Walmart Product Scraper
Save this as walmart_scraper.py and run: python walmart_scraper.py
"""

import scrapy
import math
import json
import sys
import os
from scrapy.crawler import CrawlerProcess
from scrapy_playwright.page import PageMethod

class WalmartFullProductSpider(scrapy.Spider):
    name = "walmart_full_product"
    allowed_domains = ["walmart.com"]

    # Replace this with any product URL
    start_urls = [
        "https://www.walmart.com/ip/Costway-Kitchen-Storage-Cabinet-Sideboard-Buffet-Cupboard-w-Sliding-Door-Brown/549055407?athAsset=eyJhdGhjcGlkIjoiNTQ5MDU1NDA3IiwiYXRoc3RpZCI6IkNTMDIwIiwiYXRoYW5jaWQiOiJJdGVtQ2Fyb3VzZWwiLCJhdGhyayI6MC4wfQ==&athena=true"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", 'script#__NEXT_DATA__', timeout=10000),
                        PageMethod("wait_for_timeout", 3000)
                    ],
                }
            )

    def parse(self, response):
        self.logger.info(f"Parsing main product page: {response.url}")
        
        # Extract the JSON that contains product info
        script = response.css('script#__NEXT_DATA__::text').get()
        if not script:
            self.logger.error("Could not find __NEXT_DATA__ script")
            return
            
        try:
            data = json.loads(script)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            return

        try:
            product_json = data["props"]["pageProps"]["initialState"]["product"]["product"]
        except KeyError as e:
            self.logger.error(f"Could not find product data in JSON: {e}")
            # Log the structure to debug
            self.logger.info(f"Available keys: {list(data.keys())}")
            return

        # Product info
        title = product_json.get("productName", "No title")
        description = product_json.get("longDescription", "No description")
        images = [img.get("url") for img in product_json.get("imageEntities", []) if img.get("url")]
        product_id = product_json.get("productId")
        price = product_json.get("priceInfo", {}).get("currentPrice", {}).get("price")
        rating = product_json.get("averageRating")
        review_count = product_json.get("numberOfReviews", 0)
        
        if not product_id:
            self.logger.error("No product ID found")
            return

        # Initialize product dict
        product = {
            "title": title,
            "description": description,
            "price": price,
            "rating": rating,
            "review_count": review_count,
            "images": images,
            "product_id": product_id,
            "reviews": [],
            "url": response.url
        }

        self.logger.info(f"Found product: {title} (ID: {product_id})")

        # Start fetching reviews if there are any
        if review_count > 0:
            reviews_url = f"https://www.walmart.com/product-reviews/{product_id}?page=1"
            yield scrapy.Request(
                url=reviews_url,
                callback=self.parse_reviews,
                meta={
                    "product": product,
                    "page_number": 1,
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", 'script#__NEXT_DATA__', timeout=10000),
                        PageMethod("wait_for_timeout", 2000)
                    ],
                }
            )
        else:
            # No reviews, yield product directly
            yield product

    def parse_reviews(self, response):
        product = response.meta["product"]
        page_number = response.meta["page_number"]
        
        self.logger.info(f"Parsing reviews page {page_number} for product {product['product_id']}")

        script_data = response.css('script#__NEXT_DATA__::text').get()
        if not script_data:
            self.logger.warning(f"No __NEXT_DATA__ found on reviews page {page_number}")
            # Yield the product even without reviews
            yield product
            return

        try:
            data = json.loads(script_data)
            reviews_data = data["props"]["pageProps"]["initialState"]["product"]["reviews"]["reviews"]
            total_reviews = data["props"]["pageProps"]["initialState"]["product"]["reviews"]["totalReviewCount"]
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse reviews JSON on page {page_number}: {e}")
            # If this is the first page and we can't get reviews, still yield the product
            if page_number == 1:
                yield product
            return

        # Extract reviews
        reviews_added = 0
        for r in reviews_data:
            review_text = r.get("reviewText")
            rating = r.get("rating")
            author = r.get("reviewer", {}).get("displayName", "Anonymous")
            date = r.get("submissionTime")
            helpful_votes = r.get("helpfulVotes", 0)
            verified = r.get("verifiedPurchase", False)
            
            if review_text:  # Only add reviews with text
                product["reviews"].append({
                    "author": author,
                    "text": review_text,
                    "rating": rating,
                    "date": date,
                    "helpful_votes": helpful_votes,
                    "verified": verified
                })
                reviews_added += 1

        self.logger.info(f"Added {reviews_added} reviews from page {page_number}")

        # Pagination logic - limit to first 5 pages to avoid being blocked
        reviews_per_page = 20
        max_pages = min(math.ceil(total_reviews / reviews_per_page), 5)

        if page_number < max_pages:
            next_page_number = page_number + 1
            next_url = f"https://www.walmart.com/product-reviews/{product['product_id']}?page={next_page_number}"
            yield scrapy.Request(
                next_url,
                callback=self.parse_reviews,
                meta={
                    "product": product,
                    "page_number": next_page_number,
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", 'script#__NEXT_DATA__', timeout=10000),
                        PageMethod("wait_for_timeout", 2000)
                    ],
                }
            )
        else:
            # All reviews fetched, yield final product
            self.logger.info(f"Finished scraping product {product['product_id']} with {len(product['reviews'])} reviews")
            yield product


def main():
    """Main function to run the spider"""
    
    # Check if required packages are installed
    try:
        import scrapy_playwright
    except ImportError:
        print("Error: scrapy-playwright is not installed.")
        print("Please install it with: pip install scrapy-playwright")
        print("Then run: playwright install")
        sys.exit(1)
    
    # Configuration settings
    settings = {
        "USER_AGENT": "walmart_scraper (+http://www.yourdomain.com)",
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "DOWNLOAD_DELAY": 3,
        "RANDOMIZE_DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "LOG_LEVEL": "INFO",
        # Output files
        "FEEDS": {
            "walmart_products.json": {
                "format": "json",
                "overwrite": True,
            },
            "walmart_products.csv": {
                "format": "csv", 
                "overwrite": True,
            },
        },
    }
    
    print("🛒 Starting Walmart Product Scraper...")
    print("📁 Output files: walmart_products.json, walmart_products.csv")
    
    # Create and configure the crawler
    process = CrawlerProcess(settings)
    process.crawl(WalmartFullProductSpider)
    
    try:
        process.start()
        print("\n✅ Scraping completed successfully!")
        print("📄 Check the following files for results:")
        
        # Check if files were created and show their info
        files_created = []
        for filename in ["walmart_products.json", "walmart_products.csv"]:
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                files_created.append(f"   • {filename} ({size} bytes)")
        
        if files_created:
            print("\n".join(files_created))
        else:
            print("   ⚠️  No output files were created. Check the logs above for errors.")
            
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("Check the logs above for more details.")


if __name__ == "__main__":
    main()