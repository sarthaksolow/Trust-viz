

# works fineeeeeeeeeeeeeeeeeeeeeeeee

import asyncio
import json
import time
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import httpx
from parsel import Selector
from loguru import logger as log
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc


class WalmartScraper:
    def __init__(self, use_selenium=True, headless=True):
        """
        Initialize the Walmart scraper
        
        Args:
            use_selenium (bool): Whether to use Selenium for dynamic content
            headless (bool): Whether to run browser in headless mode
        """
        self.use_selenium = use_selenium
        self.headless = headless
        
        # Headers to mimic real browser
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        }
        
        if self.use_selenium:
            self.setup_selenium()
    
    def setup_selenium(self):
        """Setup Selenium WebDriver with optimal settings"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Performance and anti-detection options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = uc.Chrome(headless=self.headless)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            log.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def extract_product_id(self, url: str) -> Optional[str]:
        """Extract product ID from Walmart URL"""
        patterns = [
            r'/ip/([^/?]+)',
            r'WMT_ID=(\d+)',
            r'selected=true.*?(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def get_page_content(self, url: str, wait_for_reviews=True) -> str:
        """
        Get page content using either Selenium or httpx
        
        Args:
            url (str): URL to scrape
            wait_for_reviews (bool): Whether to wait for reviews to load
            
        Returns:
            str: Page HTML content
        """
        if self.use_selenium:
            return self.get_content_with_selenium(url, wait_for_reviews)
        else:
            return await self.get_content_with_httpx(url)
    
    def get_content_with_selenium(self, url: str, wait_for_reviews=True) -> str:
        """Get content using Selenium (for dynamic content)"""
        try:
            log.info(f"Loading page with Selenium: {url}")
            self.driver.get(url)

            time.sleep(2)
            # Gradual scrolling to load content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.25);")
            time.sleep(1.5)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.5);")
            time.sleep(1.5)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.75);")
            time.sleep(1.5)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Wait for main content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Enhanced review loading logic
            if wait_for_reviews:
                try:
                    # Scroll down to reviews section
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(2)
                    
                    # Look for various review loading elements
                    review_selectors = [
                        '[data-testid="reviews-section"]',
                        '[data-automation-id="product-review-summary"]',
                        '.review-text',
                        '[data-testid="review-section-header"]'
                    ]
                    
                    for selector in review_selectors:
                        try:
                            WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            break
                        except TimeoutException:
                            continue
                    
                    # Try to load more reviews with multiple attempts
                    load_more_attempts = 0
                    max_attempts = 5
                    while load_more_attempts < max_attempts:
                        try:
                            # Multiple possible selectors for load more button
                            load_more_selectors = [
                                '[data-testid="load-more-reviews"]',
                                '[data-automation-id="load-more-reviews"]', 
                                'button[aria-label*="more review"]',
                                'button:contains("See more reviews")',
                                'button:contains("Load more")',
                                '[data-testid*="more-reviews"]'
                            ]
                            
                            button_found = False
                            for selector in load_more_selectors:
                                try:
                                    load_more_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                                    if load_more_btn.is_displayed() and load_more_btn.is_enabled():
                                        self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_btn)
                                        time.sleep(1)
                                        self.driver.execute_script("arguments[0].click();", load_more_btn)
                                        log.info(f"Clicked load more reviews button: {selector}")
                                        time.sleep(3)
                                        button_found = True
                                        break
                                except (NoSuchElementException, TimeoutException):
                                    continue
                            
                            if not button_found:
                                break
                                
                            load_more_attempts += 1
                            
                        except Exception as e:
                            log.debug(f"Error clicking load more button: {e}")
                            break
                    
                    log.info(f"Attempted to load more reviews {load_more_attempts} times")
                    
                except TimeoutException:
                    log.warning("Reviews section not found or took too long to load")
            
            return self.driver.page_source
            
        except Exception as e:
            log.error(f"Error loading page with Selenium: {e}")
            return ""
    
    async def get_content_with_httpx(self, url: str) -> str:
        """Get content using httpx (for static content)"""
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            log.error(f"Error loading page with httpx: {e}")
            return ""

    def parse_hidden_data(self, html: str) -> Dict:
        """Extract data from __NEXT_DATA__ script tag"""
        sel = Selector(text=html)
        
        # Try to find the __NEXT_DATA__ script
        script_data = sel.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        
        if not script_data:
            # Fallback: look for other script tags with JSON data
            scripts = sel.xpath('//script[contains(text(), "window.__WML_REDUX_INITIAL_STATE__")]/text()').getall()
            if scripts:
                for script in scripts:
                    try:
                        # Extract JSON from window.__WML_REDUX_INITIAL_STATE__
                        start_idx = script.find('window.__WML_REDUX_INITIAL_STATE__ = ') + len('window.__WML_REDUX_INITIAL_STATE__ = ')
                        end_idx = script.find('};', start_idx) + 1
                        json_str = script[start_idx:end_idx]
                        return json.loads(json_str)
                    except:
                        continue
        
        if script_data:
            try:
                return json.loads(script_data)
            except json.JSONDecodeError as e:
                log.error(f"Failed to parse __NEXT_DATA__: {e}")
        
        return {}

    def _get_product_from_json(self, json_data: Dict) -> Optional[Dict]:
        """Extract product data from the JSON structure - using your working logic"""
        try:
            if not json_data:
                return None
            
            # Navigate through the JSON structure
            props = json_data.get('props', {})
            page_props = props.get('pageProps', {})
            initial_data = page_props.get('initialData', {})
            data = initial_data.get('data', {})
            product = data.get('product', {})
            
            return product if product else None
            
        except Exception as e:
            log.debug(f"Error navigating JSON structure: {e}")
            return None

    def extract_product_data(self, html: str, url: str) -> Dict:
        """Extract product data from HTML - using your working logic"""
        sel = Selector(text=html)
        
        # Try hidden data first
        hidden_data = self.parse_hidden_data(html)
        product_data = {
            'url': url,
            'title': '',
            'description': '',
            'price': {},
            'images': [],
            'specifications': {},
            'brand': '',
            'model': '',
            'sku': '',
            'upc': '',
            'rating': 0,
            'review_count': 0,
            'availability': '',
            'category': '',
            'seller': '',
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if hidden_data:
            try:
                # Get product data from JSON using your working method
                product = self._get_product_from_json(hidden_data)
                
                if product:
                    log.info("Found product data in hidden JSON")
                    
                    # Title
                    product_data['title'] = product.get('name', '')
                    
                    # Description - try multiple fields
                    desc_fields = ['longDescription', 'shortDescription', 'description']
                    for field in desc_fields:
                        if product.get(field):
                            product_data['description'] = product[field]
                            break
                    
                    # If no description found, try highlights
                    if not product_data['description'] and product.get('highlights'):
                        highlights = product['highlights']
                        if isinstance(highlights, list):
                            product_data['description'] = ' | '.join(highlights)
                        elif isinstance(highlights, str):
                            product_data['description'] = highlights
                    
                    # Price information
                    price_info = product.get('priceInfo', {})
                    if price_info:
                        current_price = price_info.get('currentPrice', {})
                        if current_price:
                            product_data['price'] = {
                                'current': current_price.get('price', 0),
                                'currency': current_price.get('currencyUnit', 'USD'),
                                'display': current_price.get('priceString', ''),
                                'was_price': price_info.get('wasPrice', {}).get('price') if price_info.get('wasPrice') else None,
                                'savings': price_info.get('savings', {}).get('amount') if price_info.get('savings') else None
                            }
                    
                    # Images
                    product_data['images'] = self.extract_images(product.get('imageInfo', {}))
                    
                    # Specifications
                    product_data['specifications'] = self.extract_specifications(product)
                    
                    # Basic product info
                    product_data['brand'] = product.get('brand', '')
                    product_data['model'] = product.get('model', '')
                    product_data['sku'] = str(product.get('id', ''))
                    product_data['upc'] = product.get('upc', '')
                    product_data['rating'] = product.get('averageRating', 0)
                    product_data['review_count'] = product.get('numberOfReviews', 0)
                    product_data['availability'] = product.get('availabilityStatus', '')
                    product_data['category'] = product.get('category', {}).get('path', '') if product.get('category') else ''
                    product_data['seller'] = product.get('sellerName', '')
                    
            except Exception as e:
                log.error(f"Error extracting from hidden data: {e}")
        
        # Fallback to HTML parsing if needed
        if not product_data.get('title'):
            log.info("Falling back to HTML parsing for product data")
            title_elem = sel.css('h1::text').get()
            if title_elem:
                product_data['title'] = title_elem.strip()
        
        return product_data

    def extract_images(self, image_info: Dict) -> List[str]:
        """Extract product images - using your working logic"""
        images = []
        if not image_info:
            return images
        
        # Main thumbnail
        if 'thumbnailUrl' in image_info:
            images.append(image_info['thumbnailUrl'])
        
        # All images
        if image_info.get('allImages'):
            for img in image_info['allImages']:
                if isinstance(img, dict) and img.get('url'):
                    if img['url'] not in images:
                        images.append(img['url'])
                elif isinstance(img, str) and img not in images:
                    images.append(img)
        
        return images

    def extract_specifications(self, product_data: Dict) -> Dict:
        """Extract product specifications - using your working logic"""
        specs = {}
        
        # Try specifications field
        if product_data.get('specifications'):
            spec_data = product_data['specifications']
            if isinstance(spec_data, dict):
                specs.update(spec_data)
            elif isinstance(spec_data, list):
                for spec in spec_data:
                    if isinstance(spec, dict):
                        if 'name' in spec and 'value' in spec:
                            specs[spec['name']] = spec['value']
        
        # Try idml specifications
        if not specs and product_data.get('idml'):
            idml = product_data['idml']
            if isinstance(idml, dict) and idml.get('specifications'):
                for group in idml['specifications']:
                    if isinstance(group, dict) and group.get('specifications'):
                        for spec in group['specifications']:
                            if isinstance(spec, dict) and 'name' in spec and 'value' in spec:
                                specs[spec['name']] = spec['value']
        
        # Add basic product attributes as specs
        basic_attrs = {
            'Brand': product_data.get('brand'),
            'Model': product_data.get('model'),
            'UPC': product_data.get('upc'),
            'Weight': product_data.get('weight'),
            'Color': product_data.get('color')
        }
        
        for key, value in basic_attrs.items():
            if value and key not in specs:
                specs[key] = str(value)
        
        return specs

    def extract_reviews(self, html: str, hidden_data: Dict = None) -> List[Dict]:
        """Extract reviews data - enhanced with dynamic loading capability"""
        reviews = []
        
        # Try to extract from hidden data first
        if hidden_data:
            try:
                if 'props' in hidden_data and 'pageProps' in hidden_data['props']:
                    initial_data = hidden_data['props']['pageProps'].get('initialData', {})
                    if 'data' in initial_data and 'reviews' in initial_data['data']:
                        reviews_data = initial_data['data']['reviews']
                        customer_reviews = reviews_data.get('customerReviews', [])
                        
                        log.info(f"Found {len(customer_reviews)} reviews in hidden JSON")
                        
                        for review in customer_reviews:
                            reviews.append({
                                'review_id': review.get('reviewId', ''),
                                'rating': review.get('rating', 0),
                                'title': review.get('reviewTitle', ''),
                                'text': review.get('reviewText', ''),
                                'author': review.get('userNickname', ''),
                                'date': review.get('reviewSubmissionTime', ''),
                                'helpful_count': review.get('positiveFeedback', 0),
                                'not_helpful_count': review.get('negativeFeedback', 0),
                                'verified_purchase': self.is_verified_purchase(review.get('badges', [])),
                                'photos': self.extract_review_photos(review.get('photos', []))
                            })
            except Exception as e:
                log.error(f"Error extracting reviews from hidden data: {e}")
        
        # Fallback to HTML parsing if no reviews found
        if not reviews:
            log.info("Falling back to HTML parsing for reviews")
            reviews = self.extract_reviews_from_html(html)
        
        return reviews

    def extract_reviews_from_html(self, html: str) -> List[Dict]:
        """Extract reviews from HTML (fallback method)"""
        sel = Selector(text=html)
        reviews = []
        
        # Common review selectors - more comprehensive
        review_selectors = [
            '[data-testid="reviews-section"] [data-testid*="review"]',
            '[data-automation-id="product-review-summary"] + div [data-testid*="review"]',
            '.review-list .review',
            '[data-testid*="customer-review"]',
            '.customer-review'
        ]
        
        for selector in review_selectors:
            review_elements = sel.css(selector)
            if review_elements:
                log.info(f"Found {len(review_elements)} review elements with selector: {selector}")
                for review_el in review_elements:
                    try:
                        rating = self.extract_review_rating(review_el)
                        title = review_el.css('.review-title::text, [data-testid*="review-title"]::text').get('').strip()
                        text = review_el.css('.review-text::text, [data-testid*="review-text"]::text').get('').strip()
                        author = review_el.css('.review-author::text, [data-testid*="review-author"]::text').get('').strip()
                        date = review_el.css('.review-date::text, [data-testid*="review-date"]::text').get('').strip()
                        verified = bool(review_el.css('[data-testid*="verified"], .verified-purchase'))
                        
                        review = {
                            'rating': rating,
                            'title': title,
                            'text': text,
                            'author': author,
                            'date': date,
                            'verified_purchase': verified,
                            'helpful_count': 0,
                            'not_helpful_count': 0,
                            'photos': []
                        }
                        
                        if review['text'] or review['title']:
                            reviews.append(review)
                    except Exception as e:
                        log.warning(f"Error parsing individual review: {e}")
                        continue
                break
        
        return reviews

    def is_verified_purchase(self, badges: List[Dict]) -> bool:
        """Check if review is from verified purchase"""
        for badge in badges:
            if badge.get('id') == 'VerifiedPurchaser' or 'verified' in badge.get('text', '').lower():
                return True
        return False

    def extract_review_photos(self, photos: List[Dict]) -> List[str]:
        """Extract review photo URLs"""
        photo_urls = []
        for photo in photos:
            if 'sizes' in photo:
                normal_url = photo['sizes'].get('normal', {}).get('url')
                if normal_url:
                    photo_urls.append(normal_url)
        return photo_urls

    def extract_review_rating(self, review_el: Selector) -> int:
        """Extract rating from review element"""
        # Look for star ratings
        stars = review_el.css('[aria-label*="star"]').get()
        if stars:
            try:
                return int(re.search(r'(\d+)', stars).group(1))
            except:
                pass
        return 0

    def parse_price(self, price_text: str) -> float:
        """Parse price from text"""
        try:
            price_match = re.search(r'\$(\d+\.?\d*)', price_text.replace(',', ''))
            return float(price_match.group(1)) if price_match else 0.0
        except:
            return 0.0

    async def scrape_product(self, url: str) -> Dict:
        """
        Scrape a single Walmart product
        
        Args:
            url (str): Product URL
            
        Returns:
            Dict: Product data including reviews
        """
        log.info(f"Scraping product: {url}")
        
        try:
            # Get page content with dynamic loading
            html = await self.get_page_content(url, wait_for_reviews=True)
            
            if not html:
                log.error(f"Failed to get content for {url}")
                return {}
            
            # Parse hidden data
            hidden_data = self.parse_hidden_data(html)
            
            # Extract product data using your working logic
            product_data = self.extract_product_data(html, url)
            
            # Extract reviews using enhanced dynamic extraction
            reviews = self.extract_reviews(html, hidden_data)
            
            # Combine data
            result = {
                **product_data,
                'reviews': reviews,
                'total_reviews': len(reviews),
                'review_summary': {
                    'average_rating': product_data.get('rating', 0),
                    'total_count': product_data.get('review_count', len(reviews)),
                    'rating_distribution': self.calculate_rating_distribution(reviews)
                }
            }
            
            log.success(f"Successfully scraped product with {len(reviews)} reviews")
            return result
            
        except Exception as e:
            log.error(f"Error scraping product {url}: {e}")
            return {}

    def calculate_rating_distribution(self, reviews: List[Dict]) -> Dict:
        """Calculate rating distribution from reviews"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            rating = review.get('rating', 0)
            if 1 <= rating <= 5:
                distribution[rating] += 1
        return distribution

    async def scrape_multiple_products(self, urls: List[str]) -> List[Dict]:
        """
        Scrape multiple Walmart products
        
        Args:
            urls (List[str]): List of product URLs
            
        Returns:
            List[Dict]: List of product data
        """
        log.info(f"Starting to scrape {len(urls)} products")
        
        results = []
        for url in urls:
            try:
                result = await self.scrape_product(url)
                if result:
                    results.append(result)
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                log.error(f"Error processing {url}: {e}")
                continue
        
        log.success(f"Completed scraping {len(results)} products")
        return results

    def save_to_json(self, data: List[Dict], filename: str = "walmart_products.json"):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log.success(f"Data saved to {filename}")
        except Exception as e:
            log.error(f"Error saving to JSON: {e}")

    def debug_product_json(self, url: str):
        """Debug method to inspect the JSON structure"""
        try:
            html = asyncio.run(self.get_page_content(url, wait_for_reviews=False))
            json_data = self.parse_hidden_data(html)
            
            if json_data:
                product = self._get_product_from_json(json_data)
                if product:
                    print("=== AVAILABLE PRODUCT FIELDS ===")
                    for key, value in product.items():
                        value_type = type(value).__name__
                        if isinstance(value, (list, dict)):
                            print(f"{key}: {value_type} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                        else:
                            preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                            print(f"{key}: {value_type} = {preview}")
                
                # Save full JSON for inspection
                with open('debug_walmart_json.json', 'w') as f:
                    json.dump(json_data, f, indent=2)
                print("\nFull JSON saved to debug_walmart_json.json")
            else:
                print("No JSON data found")
                
        except Exception as e:
            log.error(f"Debug error: {e}")

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass
def save_to_json_amend(new_data, file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = []

    if isinstance(existing_data, list):
        if isinstance(new_data, list):
            existing_data.extend(new_data)
        else:
            existing_data.append(new_data)
    elif isinstance(existing_data, dict):
        if isinstance(new_data, dict):
            existing_data.update(new_data)

    # ✅ This line is the exact change you need to make it work
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, indent=2, ensure_ascii=False)


# Example usage
async def main():
    # Example Walmart product URLs
    urls = [
       
        "https://www.walmart.com/ip/seort/14590271671",
        "https://www.walmart.com/ip/290404627",
        "https://www.walmart.com/ip/954302821",
        "https://www.walmart.com/ip/5314190515",
        "https://www.walmart.com/ip/2703155849",
        "https://www.walmart.com/ip/527818837",
        "https://www.walmart.com/ip/16344006899",
        "https://www.walmart.com/ip/5351994960",
        "https://www.walmart.com/ip/3910421282",
        "https://www.walmart.com/ip/AND1-Men-s-Cushion-Quarter-Socks-12-Pack/870945481?athAsset=eyJhdGhjcGlkIjoiODcwOTQ1NDgxIiwiYXRoc3RpZCI6IkNTMDIwIiwiYXRoYW5jaWQiOiJJdGVtQ2Fyb3VzZWwiLCJhdGhyayI6MC4wfQ==&athena=true&athbdg=L1300"
        # Add more URLs here
    ]
    
    # Initialize scraper
    scraper = WalmartScraper(use_selenium=True, headless=False)
    
    try:
        # Scrape products
        results = await scraper.scrape_multiple_products(urls)
        
        # Save results
        # scraper.save_to_json(results, "walmart_scraped_data.json")
        save_to_json_amend(results, 'walmart_scraped_data.json')
        
        # Print summary
        for result in results:
            print(f"Product: {result.get('title', 'Unknown')}")
            print(f"Price: {result.get('price', {}).get('display', 'N/A')}")
            print(f"Reviews: {result.get('total_reviews', 0)}")
            print(f"Rating: {result.get('rating', 0)}")
            print(f"Description length: {len(result.get('description', ''))}")
            print(f"Images: {len(result.get('images', []))}")
            print("-" * 50)
            
    finally:
        scraper.close()

if __name__ == "__main__":
    # Install required packages:
    # pip install httpx parsel loguru selenium undetected-chromedriver
    
    asyncio.run(main())



    





# import requests
# import json
# import re
# import time
# from bs4 import BeautifulSoup
# from typing import Dict, List, Optional
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class WalmartScraper:
#     def __init__(self):
#         self.session = requests.Session()
#         # Headers to mimic a real browser
#         self.headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#             'Accept-Language': 'en-US,en;q=0.5',
#             'Accept-Encoding': 'gzip, deflate, br',
#             'Connection': 'keep-alive',
#         }
#         self.session.headers.update(self.headers)

#     def get_product_info(self, url: str) -> Dict:
#         """Main function to scrape product information"""
#         try:
#             logger.info(f"Scraping product: {url}")
#             response = self.session.get(url, timeout=30)
#             response.raise_for_status()
            
#             soup = BeautifulSoup(response.content, 'html.parser')
            
#             # Extract JSON data from __NEXT_DATA__
#             json_data = self._extract_next_data(response.text)
            
#             # Initialize product data
#             product_data = {
#                 'url': url,
#                 'title': '',
#                 'description': '',
#                 'price': {},
#                 'images': [],
#                 'specifications': {},
#                 'reviews': {
#                     'average_rating': 0,
#                     'total_reviews': 0,
#                     'individual_reviews': []
#                 },
#                 'brand': '',
#                 'model': '',
#                 'sku': '',
#                 'upc': ''
#             }
            
#             # Extract data
#             product_data.update(self._extract_basic_info(soup, json_data))
#             product_data['images'] = self._extract_images(soup, json_data)
#             product_data['specifications'] = self._extract_specifications(json_data, soup)
#             product_data['reviews'] = self._extract_reviews_data(json_data, soup)
            
#             return product_data
            
#         except Exception as e:
#             logger.error(f"Error scraping {url}: {e}")
#             return {'url': url, 'error': str(e)}

#     def _extract_next_data(self, html_content: str) -> Dict:
#         """Extract JSON data from __NEXT_DATA__ script tag"""
#         try:
#             soup = BeautifulSoup(html_content, 'html.parser')
#             script = soup.find('script', {'id': '__NEXT_DATA__'})
            
#             if script and script.string:
#                 return json.loads(script.string)
#             return {}
#         except Exception as e:
#             logger.debug(f"Error extracting __NEXT_DATA__: {e}")
#             return {}

#     def _extract_basic_info(self, soup: BeautifulSoup, json_data: Dict) -> Dict:
#         """Extract basic product information"""
#         info = {
#             'title': '',
#             'description': '',
#             'price': {},
#             'brand': '',
#             'model': '',
#             'sku': '',
#             'upc': ''
#         }
        
#         try:
#             # Get product data from JSON
#             product = self._get_product_from_json(json_data)
            
#             if product:
#                 # Title
#                 info['title'] = product.get('name', '')
                
#                 # Description - try multiple fields
#                 desc_fields = ['longDescription', 'shortDescription', 'description']
#                 for field in desc_fields:
#                     if product.get(field):
#                         info['description'] = product[field]
#                         break
                
#                 # If no description found, try highlights
#                 if not info['description'] and product.get('highlights'):
#                     highlights = product['highlights']
#                     if isinstance(highlights, list):
#                         info['description'] = ' | '.join(highlights)
#                     elif isinstance(highlights, str):
#                         info['description'] = highlights
                
#                 # Price information
#                 price_info = product.get('priceInfo', {})
#                 if price_info:
#                     current_price = price_info.get('currentPrice', {})
#                     if current_price:
#                         info['price'] = {
#                             'current': current_price.get('price', 0),
#                             'formatted': current_price.get('priceString', '')
#                         }
                
#                 # Basic product info
#                 info['brand'] = product.get('brand', '')
#                 info['model'] = product.get('model', '')
#                 info['sku'] = str(product.get('id', ''))
#                 info['upc'] = product.get('upc', '')
            
#             # Fallback to HTML if JSON extraction failed
#             if not info['title']:
#                 title_elem = soup.find('h1')
#                 if title_elem:
#                     info['title'] = title_elem.get_text().strip()
            
#         except Exception as e:
#             logger.debug(f"Error extracting basic info: {e}")
        
#         return info

#     def _extract_images(self, soup: BeautifulSoup, json_data: Dict) -> List[str]:
#         """Extract product images"""
#         images = []
        
#         try:
#             # Try JSON first
#             product = self._get_product_from_json(json_data)
#             if product and product.get('imageInfo'):
#                 image_info = product['imageInfo']
#                 if image_info.get('allImages'):
#                     for img in image_info['allImages']:
#                         if isinstance(img, dict) and img.get('url'):
#                             images.append(img['url'])
#                         elif isinstance(img, str):
#                             images.append(img)
            
#             # Fallback to HTML
#             if not images:
#                 img_elements = soup.find_all('img')
#                 for img in img_elements:
#                     src = img.get('src') or img.get('data-src')
#                     if src and 'walmartimages.com' in src:
#                         if src.startswith('//'):
#                             src = 'https:' + src
#                         images.append(src)
            
#         except Exception as e:
#             logger.debug(f"Error extracting images: {e}")
        
#         # Remove duplicates
#         return list(dict.fromkeys(images))

#     def _extract_specifications(self, json_data: Dict, soup: BeautifulSoup) -> Dict:
#         """Extract product specifications"""
#         specs = {}
        
#         try:
#             product = self._get_product_from_json(json_data)
#             if not product:
#                 return specs
            
#             # Try specifications field
#             if product.get('specifications'):
#                 spec_data = product['specifications']
#                 if isinstance(spec_data, dict):
#                     specs.update(spec_data)
#                 elif isinstance(spec_data, list):
#                     for spec in spec_data:
#                         if isinstance(spec, dict):
#                             if 'name' in spec and 'value' in spec:
#                                 specs[spec['name']] = spec['value']
            
#             # Try idml specifications
#             if not specs and product.get('idml'):
#                 idml = product['idml']
#                 if isinstance(idml, dict) and idml.get('specifications'):
#                     for group in idml['specifications']:
#                         if isinstance(group, dict) and group.get('specifications'):
#                             for spec in group['specifications']:
#                                 if isinstance(spec, dict) and 'name' in spec and 'value' in spec:
#                                     specs[spec['name']] = spec['value']
            
#             # Add basic product attributes as specs
#             basic_attrs = {
#                 'Brand': product.get('brand'),
#                 'Model': product.get('model'),
#                 'UPC': product.get('upc'),
#                 'Weight': product.get('weight'),
#                 'Color': product.get('color')
#             }
            
#             for key, value in basic_attrs.items():
#                 if value and key not in specs:
#                     specs[key] = str(value)
            
#         except Exception as e:
#             logger.debug(f"Error extracting specifications: {e}")
        
#         return specs

#     def _extract_reviews_data(self, json_data: Dict, soup: BeautifulSoup) -> Dict:
#         """Extract review information"""
#         reviews_data = {
#             'average_rating': 0,
#             'total_reviews': 0,
#             'individual_reviews': []
#         }
        
#         try:
#             product = self._get_product_from_json(json_data)
#             if not product:
#                 return reviews_data
            
#             # Extract rating information
#             if 'averageRating' in product:
#                 reviews_data['average_rating'] = float(product['averageRating'])
#             elif 'rating' in product:
#                 reviews_data['average_rating'] = float(product['rating'])
            
#             # Extract review count
#             review_count_fields = ['numberOfReviews', 'reviewCount', 'totalReviewCount']
#             for field in review_count_fields:
#                 if product.get(field):
#                     reviews_data['total_reviews'] = int(product[field])
#                     break
            
#             # Extract individual reviews if available
#             if product.get('reviews'):
#                 reviews_list = product['reviews']
#                 if isinstance(reviews_list, list):
#                     for review in reviews_list[:10]:  # Limit to first 10 reviews
#                         review_data = self._parse_single_review(review)
#                         if review_data:
#                             reviews_data['individual_reviews'].append(review_data)
            
#         except Exception as e:
#             logger.debug(f"Error extracting reviews: {e}")
        
#         return reviews_data

#     def _parse_single_review(self, review: Dict) -> Optional[Dict]:
#         """Parse a single review from JSON"""
#         try:
#             review_data = {}
            
#             # Rating
#             if 'rating' in review:
#                 review_data['rating'] = float(review['rating'])
#             elif 'starRating' in review:
#                 review_data['rating'] = float(review['starRating'])
            
#             # Title
#             title_fields = ['title', 'reviewTitle', 'subject']
#             for field in title_fields:
#                 if review.get(field):
#                     review_data['title'] = review[field]
#                     break
            
#             # Text
#             text_fields = ['reviewText', 'text', 'content', 'body']
#             for field in text_fields:
#                 if review.get(field):
#                     review_data['text'] = review[field]
#                     break
            
#             # Author
#             author_fields = ['author', 'reviewer', 'userName', 'customerName']
#             for field in author_fields:
#                 if review.get(field):
#                     review_data['author'] = review[field]
#                     break
            
#             # Date
#             date_fields = ['date', 'reviewDate', 'submittedDate', 'createdAt']
#             for field in date_fields:
#                 if review.get(field):
#                     review_data['date'] = review[field]
#                     break
            
#             return review_data if len(review_data) > 1 else None
            
#         except Exception as e:
#             logger.debug(f"Error parsing review: {e}")
#             return None

#     def _get_product_from_json(self, json_data: Dict) -> Optional[Dict]:
#         """Extract product data from the JSON structure"""
#         try:
#             if not json_data:
#                 return None
            
#             # Navigate through the JSON structure
#             props = json_data.get('props', {})
#             page_props = props.get('pageProps', {})
#             initial_data = page_props.get('initialData', {})
#             data = initial_data.get('data', {})
#             product = data.get('product', {})
            
#             return product if product else None
            
#         except Exception as e:
#             logger.debug(f"Error navigating JSON structure: {e}")
#             return None

#     def debug_product_json(self, url: str):
#         """Debug method to inspect the JSON structure"""
#         try:
#             response = self.session.get(url, timeout=30)
#             response.raise_for_status()
            
#             json_data = self._extract_next_data(response.text)
            
#             if json_data:
#                 product = self._get_product_from_json(json_data)
#                 if product:
#                     print("=== AVAILABLE PRODUCT FIELDS ===")
#                     for key, value in product.items():
#                         value_type = type(value).__name__
#                         if isinstance(value, (list, dict)):
#                             print(f"{key}: {value_type} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
#                         else:
#                             preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
#                             print(f"{key}: {value_type} = {preview}")
                
#                 # Save full JSON for inspection
#                 with open('debug_walmart_json.json', 'w') as f:
#                     json.dump(json_data, f, indent=2)
#                 print("\nFull JSON saved to debug_walmart_json.json")
#             else:
#                 print("No JSON data found")
                
#         except Exception as e:
#             logger.error(f"Debug error: {e}")

#     def scrape_multiple_products(self, urls: List[str], delay: float = 2.0) -> List[Dict]:
#         """Scrape multiple products with delay"""
#         results = []
        
#         for i, url in enumerate(urls):
#             try:
#                 result = self.get_product_info(url)
#                 results.append(result)
                
#                 if i < len(urls) - 1:
#                     time.sleep(delay)
                    
#             except Exception as e:
#                 logger.error(f"Error processing {url}: {e}")
#                 results.append({'url': url, 'error': str(e)})
        
#         return results

#     def save_to_json(self, data: Dict, filename: str):
#         """Save data to JSON file"""
#         try:
#             with open(filename, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, indent=2, ensure_ascii=False)
#             logger.info(f"Data saved to {filename}")
#         except Exception as e:
#             logger.error(f"Error saving to {filename}: {e}")


# # Example usage
# def main():
#     scraper = WalmartScraper()
    
#     # Test URL
#     url = "https://www.walmart.com/ip/Meta-Quest-2-All-in-One-Wireless-VR-Headset-256GB/519725606"
    
#     # Debug first to see available data
#     print("=== DEBUGGING JSON STRUCTURE ===")
#     scraper.debug_product_json(url)
    
#     print("\n=== SCRAPING PRODUCT ===")
#     # Scrape the product
#     product_data = scraper.get_product_info(url)
#     print(json.dumps(product_data, indent=2))
    
#     # Save results
#     scraper.save_to_json(product_data, 'walmart_product_clean.json')


# if __name__ == "__main__":
#     main()












# import requests
# import json
# import re
# import time
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin, urlparse
# from typing import Dict, List, Optional
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class WalmartScraper:
#     def __init__(self):
#         self.session = requests.Session()
#         # Headers to mimic a real browser
#         self.headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#             'Accept-Language': 'en-US,en;q=0.5',
#             'Accept-Encoding': 'gzip, deflate, br',
#             'Connection': 'keep-alive',
#             'Upgrade-Insecure-Requests': '1',
#             'Sec-Fetch-Dest': 'document',
#             'Sec-Fetch-Mode': 'navigate',
#             'Sec-Fetch-Site': 'none',
#             'Cache-Control': 'max-age=0'
#         }
#         self.session.headers.update(self.headers)

#     def extract_json_data(self, html_content: str) -> Dict:
#         """Extract JSON data from Walmart's NextJS application"""
#         try:
#             # Look for __NEXT_DATA__ script tag containing product data
#             soup = BeautifulSoup(html_content, 'html.parser')
#             next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            
#             if next_data_script:
#                 json_data = json.loads(next_data_script.string)
#                 return json_data
#             return {}
#         except Exception as e:
#             logger.error(f"Error extracting JSON data: {e}")
#             return {}

#     def get_product_info(self, url: str) -> Dict:
#         """Main function to scrape product information"""
#         try:
#             logger.info(f"Scraping product: {url}")
#             response = self.session.get(url, timeout=30)
#             response.raise_for_status()
            
#             soup = BeautifulSoup(response.content, 'html.parser')
#             json_data = self.extract_json_data(response.text)
            
#             # Initialize product data structure
#             product_data = {
#                 'url': url,
#                 'title': '',
#                 'description': '',
#                 'price': {},
#                 'images': [],
#                 'specifications': {},
#                 'reviews': {
#                     'average_rating': 0,
#                     'total_reviews': 0,
#                     'review_breakdown': {},
#                     'individual_reviews': []
#                 },
#                 'availability': '',
#                 'brand': '',
#                 'model': '',
#                 'sku': '',
#                 'upc': ''
#             }
            
#             # Extract basic product info
#             product_data.update(self._extract_basic_info(soup, json_data))
#             product_data.update(self._extract_price_info(soup, json_data))
#             product_data['images'] = self._extract_images(soup, json_data)
#             product_data['specifications'] = self._extract_specifications(soup, json_data)
#             product_data['reviews'] = self._extract_reviews(soup, json_data, url)
            
#             return product_data
            
#         except requests.RequestException as e:
#             logger.error(f"Request error for {url}: {e}")
#             return {'error': str(e)}
#         except Exception as e:
#             logger.error(f"Unexpected error for {url}: {e}")
#             return {'error': str(e)}

#     def _extract_basic_info(self, soup: BeautifulSoup, json_data: Dict) -> Dict:
#         """Extract basic product information"""
#         info = {}
        
#         # Try to get title from multiple sources
#         title_selectors = [
#             'h1[data-automation-id="product-title"]',
#             'h1[id*="main-title"]',
#             'h1.prod-ProductTitle',
#             '.product-title h1'
#         ]
        
#         for selector in title_selectors:
#             title_elem = soup.select_one(selector)
#             if title_elem:
#                 info['title'] = title_elem.get_text().strip()
#                 break
        
#         # Try JSON data for title if not found
#         if not info.get('title') and json_data:
#             try:
#                 page_data = json_data.get('props', {}).get('pageProps', {})
#                 if 'initialData' in page_data:
#                     product = page_data['initialData'].get('data', {}).get('product', {})
#                     info['title'] = product.get('name', '')
#             except:
#                 pass
        
#         # Extract description
#         desc_selectors = [
#             '[data-automation-id="product-highlights"]',
#             '.product-highlights',
#             '.about-desc',
#             '.prod-ProductHighlights'
#         ]
        
#         for selector in desc_selectors:
#             desc_elem = soup.select_one(selector)
#             if desc_elem:
#                 info['description'] = desc_elem.get_text().strip()
#                 break
        
#         # Extract brand, model, SKU from JSON or HTML
#         try:
#             if json_data:
#                 page_data = json_data.get('props', {}).get('pageProps', {})
#                 if 'initialData' in page_data:
#                     product = page_data['initialData'].get('data', {}).get('product', {})
#                     info['brand'] = product.get('brand', '')
#                     info['model'] = product.get('model', '')
#                     info['sku'] = str(product.get('id', ''))
#                     info['upc'] = product.get('upc', '')
#         except:
#             pass
        
#         return info

#     def _extract_price_info(self, soup: BeautifulSoup, json_data: Dict) -> Dict:
#         """Extract price information"""
#         price_info = {'price': {}}
        
#         # Price selectors
#         current_price_selectors = [
#             '[data-automation-id="product-price"] .notranslate',
#             '.price-current .price-characteristic',
#             '.price-group .price-current',
#             'span[itemprop="price"]'
#         ]
        
#         for selector in current_price_selectors:
#             price_elem = soup.select_one(selector)
#             if price_elem:
#                 price_text = price_elem.get_text().strip()
#                 # Extract numeric price
#                 price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
#                 if price_match:
#                     price_info['price']['current'] = float(price_match.group(1).replace(',', ''))
#                     price_info['price']['formatted'] = price_text
#                 break
        
#         # Try to extract from JSON data
#         if not price_info['price'] and json_data:
#             try:
#                 page_data = json_data.get('props', {}).get('pageProps', {})
#                 if 'initialData' in page_data:
#                     product = page_data['initialData'].get('data', {}).get('product', {})
#                     price_info['price']['current'] = product.get('priceInfo', {}).get('currentPrice', {}).get('price', 0)
#             except:
#                 pass
        
#         return price_info

#     def _extract_images(self, soup: BeautifulSoup, json_data: Dict) -> List[str]:
#         """Extract product images"""
#         images = []
        
#         # Image selectors
#         img_selectors = [
#             '.prod-hero-image-carousel img',
#             '.product-images img',
#             '[data-automation-id="product-image"] img'
#         ]
        
#         for selector in img_selectors:
#             img_elements = soup.select(selector)
#             for img in img_elements:
#                 src = img.get('src') or img.get('data-src')
#                 if src and src not in images:
#                     # Convert to full URL if needed
#                     if src.startswith('//'):
#                         src = 'https:' + src
#                     elif src.startswith('/'):
#                         src = 'https://i5.walmartimages.com' + src
#                     images.append(src)
        
#         # Try JSON data for images
#         if json_data:
#             try:
#                 page_data = json_data.get('props', {}).get('pageProps', {})
#                 if 'initialData' in page_data:
#                     product = page_data['initialData'].get('data', {}).get('product', {})
#                     image_info = product.get('imageInfo', {}).get('allImages', [])
#                     for img_data in image_info:
#                         if img_data.get('url'):
#                             images.append(img_data['url'])
#             except:
#                 pass
        
#         return list(dict.fromkeys(images))  # Remove duplicates while preserving order

#     def _extract_specifications(self, soup: BeautifulSoup, json_data: Dict) -> Dict:
#         """Extract product specifications"""
#         specs = {}
        
#         # Try to find specifications table
#         spec_selectors = [
#             '.product-specifications table tr',
#             '.spec-table tr',
#             '[data-automation-id="product-specifications"] tr'
#         ]
        
#         for selector in spec_selectors:
#             spec_rows = soup.select(selector)
#             for row in spec_rows:
#                 cells = row.select('td, th')
#                 if len(cells) == 2:
#                     key = cells[0].get_text().strip()
#                     value = cells[1].get_text().strip()
#                     specs[key] = value
#             if specs:
#                 break
        
#         return specs

#     def _extract_reviews(self, soup: BeautifulSoup, json_data: Dict, product_url: str) -> Dict:
#         """Extract review information"""
#         reviews_data = {
#             'average_rating': 0,
#             'total_reviews': 0,
#             'review_breakdown': {},
#             'individual_reviews': []
#         }
        
#         # Extract rating and review count
#         rating_selectors = [
#             '.average-rating .visuallyhidden',
#             '[data-automation-id="product-rating-value"]',
#             '.stars-rating-value'
#         ]
        
#         for selector in rating_selectors:
#             rating_elem = soup.select_one(selector)
#             if rating_elem:
#                 rating_text = rating_elem.get_text()
#                 rating_match = re.search(r'([\d.]+)', rating_text)
#                 if rating_match:
#                     reviews_data['average_rating'] = float(rating_match.group(1))
#                 break
        
#         # Extract review count
#         count_selectors = [
#             '.reviews-section-title',
#             '[data-automation-id="reviews-section-title"]',
#             '.product-reviews-count'
#         ]
        
#         for selector in count_selectors:
#             count_elem = soup.select_one(selector)
#             if count_elem:
#                 count_text = count_elem.get_text()
#                 count_match = re.search(r'(\d+)', count_text)
#                 if count_match:
#                     reviews_data['total_reviews'] = int(count_match.group(1))
#                 break
        
#         # Extract individual reviews
#         review_selectors = [
#             '.reviews-list .review-item',
#             '[data-automation-id="reviews-section"] .review',
#             '.product-review'
#         ]
        
#         for selector in review_selectors:
#             review_elements = soup.select(selector)
#             for review in review_elements:
#                 review_data = {}
                
#                 # Extract rating
#                 rating_elem = review.select_one('.stars-rating, [data-testid="reviews-section-stars"]')
#                 if rating_elem:
#                     rating_attr = rating_elem.get('aria-label') or rating_elem.get('title', '')
#                     rating_match = re.search(r'([\d.]+)', rating_attr)
#                     if rating_match:
#                         review_data['rating'] = float(rating_match.group(1))
                
#                 # Extract title
#                 title_elem = review.select_one('.review-title, .review-subject')
#                 if title_elem:
#                     review_data['title'] = title_elem.get_text().strip()
                
#                 # Extract text
#                 text_elem = review.select_one('.review-text, .review-body')
#                 if text_elem:
#                     review_data['text'] = text_elem.get_text().strip()
                
#                 # Extract author
#                 author_elem = review.select_one('.review-author, .reviewer-name')
#                 if author_elem:
#                     review_data['author'] = author_elem.get_text().strip()
                
#                 # Extract date
#                 date_elem = review.select_one('.review-date, .review-submitted-date')
#                 if date_elem:
#                     review_data['date'] = date_elem.get_text().strip()
                
#                 if review_data:
#                     reviews_data['individual_reviews'].append(review_data)
            
#             if reviews_data['individual_reviews']:
#                 break
        
#         return reviews_data

#     def scrape_multiple_products(self, urls: List[str], delay: float = 2.0) -> List[Dict]:
#         """Scrape multiple products with delay between requests"""
#         results = []
        
#         for i, url in enumerate(urls):
#             try:
#                 result = self.get_product_info(url)
#                 results.append(result)
                
#                 # Add delay between requests to be respectful
#                 if i < len(urls) - 1:
#                     time.sleep(delay)
                    
#             except Exception as e:
#                 logger.error(f"Error processing {url}: {e}")
#                 results.append({'url': url, 'error': str(e)})
        
#         return results

#     def save_to_json(self, data: Dict, filename: str):
#         """Save data to JSON file"""
#         try:
#             with open(filename, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, indent=2, ensure_ascii=False)
#             logger.info(f"Data saved to {filename}")
#         except Exception as e:
#             logger.error(f"Error saving to {filename}: {e}")

# # Example usage
# def main():
#     scraper = WalmartScraper()
    
#     # Example Walmart product URLs
#     urls = [
#         "https://www.walmart.com/ip/AT-T-iPhone-14-128GB-Midnight/1756765288",
#         # Add more URLs here
#     ]
    
#     # Scrape single product
#     if urls:
#         product_data = scraper.get_product_info(urls[0])
#         print(json.dumps(product_data, indent=2))
        
#         # Save to file
#         scraper.save_to_json(product_data, 'walmart_product.json')
    
#     # Scrape multiple products
#     # all_products = scraper.scrape_multiple_products(urls)
#     # scraper.save_to_json(all_products, 'walmart_products.json')

# if __name__ == "__main__":
#     main()