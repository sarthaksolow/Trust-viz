import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, urlparse
import csv

class WalmartScraper:
    def __init__(self):
        self.base_url = "https://www.walmart.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.unique_urls = set()
        
    def is_product_url(self, url):
        """Check if URL is a product listing page"""
        product_patterns = [
            r'/ip/',  # Walmart product pages typically contain /ip/
            r'/product/',
        ]
        return any(re.search(pattern, url) for pattern in product_patterns)
    
    def extract_product_urls(self, html_content, base_url):
        """Extract product URLs from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        product_urls = set()
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                full_url = urljoin(base_url, href)
            elif href.startswith('http'):
                full_url = href
            else:
                continue
                
            # Check if it's a product URL
            if self.is_product_url(full_url) and 'walmart.com' in full_url:
                # Clean URL (remove query parameters for uniqueness)
                clean_url = full_url.split('?')[0]
                product_urls.add(clean_url)
                
        return product_urls
    
    def scrape_category_page(self, category_url, max_pages=3):
        """Scrape product URLs from a category page"""
        print(f"Scraping category: {category_url}")
        
        for page in range(1, max_pages + 1):
            try:
                # Add page parameter for pagination
                if '?' in category_url:
                    page_url = f"{category_url}&page={page}"
                else:
                    page_url = f"{category_url}?page={page}"
                
                print(f"  Scraping page {page}...")
                response = self.session.get(page_url, timeout=10)
                response.raise_for_status()
                
                # Extract product URLs
                new_urls = self.extract_product_urls(response.text, self.base_url)
                self.unique_urls.update(new_urls)
                
                print(f"  Found {len(new_urls)} new product URLs on page {page}")
                
                # Be respectful with requests
                time.sleep(2)
                
            except requests.RequestException as e:
                print(f"Error scraping page {page}: {e}")
                continue
    
    def scrape_search_results(self, search_term, max_pages=3):
        """Scrape product URLs from search results"""
        search_url = f"{self.base_url}/search?q={search_term.replace(' ', '%20')}"
        print(f"Scraping search results for: {search_term}")
        
        for page in range(1, max_pages + 1):
            try:
                page_url = f"{search_url}&page={page}"
                
                print(f"  Scraping page {page}...")
                response = self.session.get(page_url, timeout=10)
                response.raise_for_status()
                
                # Extract product URLs
                new_urls = self.extract_product_urls(response.text, self.base_url)
                self.unique_urls.update(new_urls)
                
                print(f"  Found {len(new_urls)} new product URLs on page {page}")
                
                # Be respectful with requests
                time.sleep(2)
                
            except requests.RequestException as e:
                print(f"Error scraping search page {page}: {e}")
                continue
    
    def save_urls_to_file(self, filename="walmart_product_urls.txt"):
        """Save unique URLs to a text file"""
        with open(filename, 'w', encoding='utf-8') as f:
            for url in sorted(self.unique_urls):
                f.write(url + '\n')
        print(f"Saved {len(self.unique_urls)} unique URLs to {filename}")
    
    def save_urls_to_csv(self, filename="walmart_product_urls.csv"):
        """Save unique URLs to a CSV file"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Product URL'])
            for url in sorted(self.unique_urls):
                writer.writerow([url])
        print(f"Saved {len(self.unique_urls)} unique URLs to {filename}")

# Example usage
def main():
    scraper = WalmartScraper()
    
    # Example 1: Scrape from category pages
    category_urls = [
        "https://www.walmart.com/browse/electronics/cell-phones/9003_133161",
        "https://www.walmart.com/browse/home/kitchen-dining/4044_623679",
        "https://www.walmart.com/browse/clothing/mens-clothing/5438_133197"
    ]
    
    for category_url in category_urls:
        scraper.scrape_category_page(category_url, max_pages=2)
    
    # Example 2: Scrape from search results
    search_terms = ["laptop", "headphones", "kitchen appliances"]
    
    for term in search_terms:
        scraper.scrape_search_results(term, max_pages=2)
    
    # Save results
    scraper.save_urls_to_file("walmart_urls.txt")
    scraper.save_urls_to_csv("walmart_urls.csv")
    
    print(f"\nTotal unique product URLs found: {len(scraper.unique_urls)}")

if __name__ == "__main__":
    main()