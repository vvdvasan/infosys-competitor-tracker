"""Flipkart India scraper implementation."""

import re
import time
from typing import List, Dict, Optional
from datetime import datetime
import logging
from sentiment_analysis.scraper.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class FlipkartScraper(BaseScraper):
    """Scraper for Flipkart India."""

    def __init__(self, headless: bool = True):
        """
        Initialize Flipkart scraper with Selenium for dynamic content.

        Args:
            headless: Whether to run browser in headless mode
        """
        super().__init__(use_selenium=True, headless=headless)
        self.base_url = "https://www.flipkart.com"

    def scrape_product(self, product_url: str) -> Dict:
        """
        Scrape product information from Flipkart.

        Args:
            product_url: Flipkart product URL

        Returns:
            Dictionary with product information
        """
        soup = self._get_page(product_url)
        if not soup:
            return {}

        product_data = {
            "Product_Name": "",
            "Product_ASIN": "",  # Using ASIN field for Flipkart product ID
            "Brand": "",
            "Price": "",
            "MRP": "",
            "Discount": "",
            "Stock_Status": "",
            "Rating": "",
            "Reviews": "",
            "Seller": "",
            "Product_Link": product_url,
            "Reviews_Link": "",
            "Scraped_At": datetime.now().isoformat()
        }

        try:
            # Extract product ID from URL
            product_id_match = re.search(r'/p/([^?]+)', product_url)
            if product_id_match:
                product_data["Product_ASIN"] = product_id_match.group(1)

            # Product name
            title_elem = soup.find('span', {'class': 'VU-ZEz'}) or soup.find('span', {'class': 'B_NuCI'})
            if title_elem:
                product_data["Product_Name"] = title_elem.get_text(strip=True)

            # Brand (usually in the product name)
            if product_data["Product_Name"]:
                brand = product_data["Product_Name"].split()[0]
                product_data["Brand"] = brand

            # Price
            price_elem = soup.find('div', {'class': 'Nx9bqj CxhGGd'}) or soup.find('div', {'class': '_30jeq3 _16Jk6d'})
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_cleaned = re.sub(r'[₹,]', '', price_text)
                product_data["Price"] = price_cleaned

            # MRP (original price)
            mrp_elem = soup.find('div', {'class': 'yRaY8j ZYYwLA'}) or soup.find('div', {'class': '_3I9_wc _2p6lqe'})
            if mrp_elem:
                mrp_text = mrp_elem.get_text(strip=True)
                mrp_cleaned = re.sub(r'[₹,]', '', mrp_text)
                product_data["MRP"] = mrp_cleaned

            # Discount
            discount_elem = soup.find('div', {'class': 'UkUFwK'}) or soup.find('div', {'class': '_3Ay6Sb _31Dcoz'})
            if discount_elem:
                product_data["Discount"] = discount_elem.get_text(strip=True)

            # Stock Status
            availability_elem = soup.find('button', {'class': 'QqFHMw vslbG+ In9uk2'})
            if availability_elem and 'ADD TO CART' in availability_elem.get_text(strip=True).upper():
                product_data["Stock_Status"] = "In Stock"
            else:
                product_data["Stock_Status"] = "Out of Stock"

            # Rating
            rating_elem = soup.find('div', {'class': 'XQDdHH'}) or soup.find('div', {'class': '_3LWZlK'})
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    product_data["Rating"] = rating_match.group(1)

            # Number of ratings/reviews
            reviews_elem = soup.find('span', {'class': 'Wphh3N'}) or soup.find('span', {'class': '_2_R_DZ'})
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                # Extract numbers like "1,234 Ratings" or "567 Reviews"
                reviews_match = re.search(r'([\d,]+)', reviews_text)
                if reviews_match:
                    product_data["Reviews"] = reviews_match.group(1).replace(',', '')

            # Seller (Flipkart is usually the platform)
            seller_elem = soup.find('div', {'class': '_2Eq6O8'}) or soup.find('div', {'id': 'sellerName'})
            if seller_elem:
                product_data["Seller"] = seller_elem.get_text(strip=True)
            else:
                product_data["Seller"] = "Flipkart"

            # Reviews link
            if product_data["Product_ASIN"]:
                product_data["Reviews_Link"] = product_url + "#reviews"

        except Exception as e:
            logger.error(f"Error parsing Flipkart product data: {str(e)}")

        return product_data

    def scrape_reviews(self, product_url: str, max_pages: int = 10) -> List[Dict]:
        """
        Scrape reviews for a Flipkart product.

        Args:
            product_url: Product URL
            max_pages: Maximum number of review pages to scrape

        Returns:
            List of review dictionaries
        """
        reviews = []

        # Navigate to reviews section
        reviews_url = product_url + "#reviews"
        logger.info(f"Scraping Flipkart reviews: {reviews_url}")

        soup = self._get_page(reviews_url)
        if not soup:
            return reviews

        # Extract product ID for review IDs
        product_id_match = re.search(r'/p/([^?]+)', product_url)
        product_id = product_id_match.group(1) if product_id_match else "unknown"

        # Find all review containers
        # Flipkart review selectors (these may change)
        review_divs = soup.find_all('div', {'class': 'cPHDOP col-12-12'}) or \
                     soup.find_all('div', {'class': '_1AtVbE col-12-12'})

        if not review_divs:
            logger.info(f"No reviews found")
            return reviews

        for idx, review_div in enumerate(review_divs[:max_pages * 10]):  # Limit reviews
            review_data = self._parse_review(review_div, product_id, idx)
            if review_data:
                reviews.append(review_data)

        logger.info(f"Scraped {len(reviews)} reviews from Flipkart")
        return reviews

    def _parse_review(self, review_div, product_id: str, idx: int) -> Optional[Dict]:
        """Parse a single Flipkart review element."""
        try:
            review = {
                "product_asin": product_id,
                "review_id": f"flipkart_{product_id}_review_{idx}",
                "reviewer_name": "",
                "rating": "",
                "title": "",
                "text": "",
                "date": "",
                "verified_purchase": False,
                "helpful_count": 0,
                "scraped_at": datetime.now().isoformat()
            }

            # Reviewer name
            name_elem = review_div.find('p', {'class': '_2NsDsF AwS1CA'}) or \
                       review_div.find('p', {'class': '_2sc7ZR _2V5EHH'})
            if name_elem:
                review["reviewer_name"] = name_elem.get_text(strip=True)

            # Rating
            rating_elem = review_div.find('div', {'class': 'XQDdHH Ga3i8K'}) or \
                         review_div.find('div', {'class': '_3LWZlK _1BLPMq'})
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+)', rating_text)
                if rating_match:
                    review["rating"] = rating_match.group(1)

            # Review title
            title_elem = review_div.find('p', {'class': 'z9E0IG'}) or \
                        review_div.find('p', {'class': '_2-N8zT'})
            if title_elem:
                review["title"] = title_elem.get_text(strip=True)

            # Review text
            text_elem = review_div.find('div', {'class': 'ZmyHeo'}) or \
                       review_div.find('div', {'class': 't-ZTKy'})
            if text_elem:
                review["text"] = text_elem.get_text(strip=True)

            # Date
            date_elem = review_div.find('p', {'class': '_2NsDsF'}) or \
                       review_div.find('p', {'class': '_2sc7ZR'})
            if date_elem:
                review["date"] = date_elem.get_text(strip=True)

            # Verified purchase badge
            verified_elem = review_div.find('div', {'class': '_2_R_DZ'})
            if verified_elem and 'Certified Buyer' in verified_elem.get_text():
                review["verified_purchase"] = True

            # Helpful count
            helpful_elem = review_div.find('div', {'class': '_1ZudkL'})
            if helpful_elem:
                helpful_text = helpful_elem.get_text(strip=True)
                helpful_match = re.search(r'(\d+)', helpful_text)
                if helpful_match:
                    review["helpful_count"] = int(helpful_match.group(1))

            return review

        except Exception as e:
            logger.error(f"Error parsing Flipkart review: {str(e)}")
            return None
