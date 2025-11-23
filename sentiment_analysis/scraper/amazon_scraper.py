"""Amazon India scraper implementation."""

import re
import time
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from sentiment_analysis.scraper.base_scraper import BaseScraper
from sentiment_analysis.config import Config

logger = logging.getLogger(__name__)

class AmazonScraper(BaseScraper):
    """Scraper for Amazon India."""

    def __init__(self, headless: bool = True):
        """
        Initialize Amazon scraper with Selenium for dynamic content.

        Args:
            headless: Whether to run browser in headless mode (False shows browser for login)
        """
        super().__init__(use_selenium=True, headless=headless)
        self.base_url = "https://www.amazon.in"
        self.logged_in = False

    def login(self, email: str, password: str) -> bool:
        """
        Log in to Amazon account.

        Args:
            email: Amazon account email
            password: Amazon account password

        Returns:
            True if login successful, False otherwise
        """
        try:
            logger.info("Attempting to log in to Amazon...")

            # Go to Amazon homepage
            self.driver.get(self.base_url)
            time.sleep(2)

            # Click on "Hello, Sign in" button
            try:
                sign_in_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "nav-link-accountList"))
                )
                sign_in_button.click()
            except TimeoutException:
                logger.error("Could not find sign-in button")
                return False

            # Wait for login page and enter email
            try:
                email_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "ap_email"))
                )
                email_input.clear()
                email_input.send_keys(email)

                # Click Continue button
                continue_button = self.driver.find_element(By.ID, "continue")
                continue_button.click()

                logger.info("Email entered, waiting for password field...")
                time.sleep(2)
            except TimeoutException:
                logger.error("Could not find email input field")
                return False

            # Enter password
            try:
                password_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "ap_password"))
                )
                password_input.clear()
                password_input.send_keys(password)

                # Click Sign-In button
                sign_in_button = self.driver.find_element(By.ID, "signInSubmit")
                sign_in_button.click()

                logger.info("Password entered, logging in...")
                time.sleep(3)
            except TimeoutException:
                logger.error("Could not find password input field")
                return False

            # Check if login was successful
            try:
                # Wait a bit for page to load
                time.sleep(3)

                # Check if we're on a page that requires OTP or CAPTCHA
                page_source = self.driver.page_source.lower()

                if "otp" in page_source or "one-time password" in page_source:
                    logger.warning("⚠️  OTP verification required!")
                    logger.warning("Please enter the OTP manually in the browser window...")
                    logger.warning("You have 60 seconds to complete OTP verification.")
                    time.sleep(60)  # Give user time to enter OTP

                if "captcha" in page_source:
                    logger.warning("⚠️  CAPTCHA detected!")
                    logger.warning("Please solve the CAPTCHA manually in the browser window...")
                    logger.warning("You have 60 seconds to complete CAPTCHA.")
                    time.sleep(60)  # Give user time to solve CAPTCHA

                # Check if we successfully logged in
                if "Hello" in self.driver.page_source or "Your Account" in self.driver.page_source:
                    logger.info("✅ Successfully logged in to Amazon!")
                    self.logged_in = True
                    return True
                else:
                    logger.error("❌ Login appears to have failed")
                    return False

            except Exception as e:
                logger.error(f"Error checking login status: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

    def scrape_product(self, product_url: str) -> Dict:
        """
        Scrape product information from Amazon.

        Args:
            product_url: Amazon product URL

        Returns:
            Dictionary with product information
        """
        soup = self._get_page(product_url)
        if not soup:
            return {}

        product_data = {
            "Product_Name": "",
            "Product_ASIN": "",
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
            # Extract ASIN from URL
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
            if asin_match:
                product_data["Product_ASIN"] = asin_match.group(1)

            # Product name
            title_elem = soup.find('span', {'id': 'productTitle'})
            if title_elem:
                product_data["Product_Name"] = title_elem.get_text(strip=True)

            # Brand
            brand_elem = soup.find('a', {'id': 'bylineInfo'})
            if brand_elem:
                brand_text = brand_elem.get_text(strip=True)
                product_data["Brand"] = brand_text.replace('Visit the', '').replace('Store', '').strip()

            # Price
            price_elem = soup.find('span', {'class': 'a-price-whole'})
            if price_elem:
                product_data["Price"] = price_elem.get_text(strip=True).replace(',', '')

            # MRP and Discount
            mrp_elem = soup.find('span', {'class': 'a-price', 'data-a-strike': 'true'})
            if mrp_elem:
                mrp_text = mrp_elem.find('span', {'class': 'a-offscreen'})
                if mrp_text:
                    product_data["MRP"] = mrp_text.get_text(strip=True).replace('₹', '').replace(',', '')

            discount_elem = soup.find('span', {'class': 'a-size-large a-color-price savingPriceOverride'})
            if discount_elem:
                product_data["Discount"] = discount_elem.get_text(strip=True)

            # Stock Status
            availability_elem = soup.find('div', {'id': 'availability'})
            if availability_elem:
                stock_text = availability_elem.get_text(strip=True)
                product_data["Stock_Status"] = "In Stock" if "In stock" in stock_text else "Out of Stock"

            # Rating
            rating_elem = soup.find('span', {'class': 'a-icon-alt'})
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    product_data["Rating"] = rating_match.group(1)

            # Number of reviews
            reviews_elem = soup.find('span', {'id': 'acrCustomerReviewText'})
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                reviews_match = re.search(r'(\d+)', reviews_text.replace(',', ''))
                if reviews_match:
                    product_data["Reviews"] = reviews_match.group(1)

            # Seller
            seller_elem = soup.find('a', {'id': 'sellerProfileTriggerId'})
            if seller_elem:
                product_data["Seller"] = seller_elem.get_text(strip=True)

            # Reviews link
            if product_data["Product_ASIN"]:
                product_data["Reviews_Link"] = f"{self.base_url}/product-reviews/{product_data['Product_ASIN']}"

        except Exception as e:
            logger.error(f"Error parsing product data: {str(e)}")

        return product_data

    def scrape_reviews(self, product_url: str, max_pages: int = 10) -> List[Dict]:
        """
        Scrape reviews for an Amazon product.

        Args:
            product_url: Product URL or ASIN
            max_pages: Maximum number of review pages to scrape

        Returns:
            List of review dictionaries
        """
        reviews = []

        # Extract ASIN
        if '/dp/' in product_url:
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
            if asin_match:
                asin = asin_match.group(1)
            else:
                logger.error("Could not extract ASIN from URL")
                return reviews
        else:
            asin = product_url

        # Iterate through review pages
        for page in range(1, max_pages + 1):
            review_url = f"{self.base_url}/product-reviews/{asin}?pageNumber={page}"
            logger.info(f"Scraping reviews page {page}: {review_url}")

            soup = self._get_page(review_url)
            if not soup:
                break

            # Find all review containers
            review_divs = soup.find_all('div', {'data-hook': 'review'})

            if not review_divs:
                logger.info(f"No more reviews found on page {page}")
                break

            for review_div in review_divs:
                review_data = self._parse_review(review_div, asin)
                if review_data:
                    reviews.append(review_data)

            self._random_delay()

        logger.info(f"Scraped {len(reviews)} reviews for ASIN {asin}")
        return reviews

    def _parse_review(self, review_div, asin: str) -> Optional[Dict]:
        """Parse a single review element."""
        try:
            review = {
                "product_asin": asin,
                "review_id": "",
                "reviewer_name": "",
                "rating": "",
                "title": "",
                "text": "",
                "date": "",
                "verified_purchase": False,
                "helpful_count": 0,
                "scraped_at": datetime.now().isoformat()
            }

            # Review ID
            review_id = review_div.get('id')
            if review_id:
                review["review_id"] = review_id

            # Reviewer name
            name_elem = review_div.find('span', {'class': 'a-profile-name'})
            if name_elem:
                review["reviewer_name"] = name_elem.get_text(strip=True)

            # Rating
            rating_elem = review_div.find('i', {'data-hook': 'review-star-rating'})
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    review["rating"] = rating_match.group(1)

            # Title
            title_elem = review_div.find('a', {'data-hook': 'review-title'})
            if title_elem:
                review["title"] = title_elem.get_text(strip=True)

            # Review text
            text_elem = review_div.find('span', {'data-hook': 'review-body'})
            if text_elem:
                review["text"] = text_elem.get_text(strip=True)

            # Date
            date_elem = review_div.find('span', {'data-hook': 'review-date'})
            if date_elem:
                review["date"] = date_elem.get_text(strip=True)

            # Verified purchase
            verified_elem = review_div.find('span', {'data-hook': 'avp-badge'})
            if verified_elem:
                review["verified_purchase"] = True

            # Helpful count
            helpful_elem = review_div.find('span', {'data-hook': 'helpful-vote-statement'})
            if helpful_elem:
                helpful_text = helpful_elem.get_text(strip=True)
                helpful_match = re.search(r'(\d+)', helpful_text)
                if helpful_match:
                    review["helpful_count"] = int(helpful_match.group(1))

            return review

        except Exception as e:
            logger.error(f"Error parsing review: {str(e)}")
            return None
