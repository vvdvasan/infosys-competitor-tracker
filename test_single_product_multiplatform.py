"""Test script to scrape a single product from multiple platforms."""

import os
import sys
import io
from dotenv import load_dotenv
from sentiment_analysis.scraper.amazon_scraper import AmazonScraper
from sentiment_analysis.config import Config
from sentiment_analysis.database.db_manager import DatabaseManager

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

def test_amazon(product_url, product_name):
    """Test Amazon scraping with login."""
    print("\n" + "="*60)
    print("TESTING AMAZON INDIA")
    print("="*60)

    email = Config.AMAZON_EMAIL
    password = Config.AMAZON_PASSWORD

    if not email or not password:
        print("\nERROR: Amazon credentials not found in .env file!")
        return None

    print(f"\nEmail: {email}")
    print(f"Password: {'*' * len(password)}")

    # Initialize scraper (visible browser for login)
    print("\nInitializing Amazon scraper (browser will open)...")
    scraper = AmazonScraper(headless=False)

    try:
        # Login
        print("\nAttempting login...")
        print("If OTP/CAPTCHA appears, you have 60 seconds to complete it.\n")

        success = scraper.login(email, password)

        if not success:
            print("\nAmazon login failed!")
            return None

        print("\nLogin successful!")

        # Scrape product
        print(f"\nScraping product: {product_name}")
        product = scraper.scrape_product(product_url)

        if product and product.get('Product_Name'):
            print(f"\nProduct found:")
            print(f"  Name: {product['Product_Name']}")
            print(f"  ASIN: {product['Product_ASIN']}")
            print(f"  Price: Rs.{product.get('Price', 'N/A')}")
            print(f"  Rating: {product.get('Rating', 'N/A')}")

            # Scrape reviews
            print(f"\nScraping reviews (first 2 pages)...")
            reviews = scraper.scrape_reviews(product_url, max_pages=2)

            print(f"\nFound {len(reviews)} reviews")

            if reviews:
                print(f"\nFirst review sample:")
                print(f"  Rating: {reviews[0].get('rating', 'N/A')}")
                print(f"  Text: {reviews[0].get('text', 'N/A')[:100]}...")

            return {
                'platform': 'Amazon India',
                'product': product,
                'reviews': reviews
            }
        else:
            print("\nFailed to scrape product")
            return None

    except Exception as e:
        print(f"\nError: {str(e)}")
        return None
    finally:
        print("\nPress Enter to close browser...")
        input()
        scraper.close()

def test_flipkart(product_url, product_name):
    """Test Flipkart scraping (placeholder for now)."""
    print("\n" + "="*60)
    print("TESTING FLIPKART")
    print("="*60)
    print("\nFlipkart scraper not yet implemented.")
    print("Will be added in the next step!")
    return None

def save_to_database(results):
    """Save results to database."""
    if not results:
        print("\nNo data to save.")
        return

    print("\n" + "="*60)
    print("SAVING TO DATABASE")
    print("="*60)

    db = DatabaseManager()

    for result in results:
        if result:
            platform = result['platform']
            product = result['product']
            reviews = result['reviews']

            # Save product
            db.insert_product(product)
            print(f"\nSaved product from {platform}")

            # Save reviews
            if reviews:
                inserted = db.insert_reviews(reviews)
                print(f"Saved {inserted} reviews from {platform}")

def main():
    """Main function."""
    print("="*60)
    print("MULTI-PLATFORM PRODUCT SCRAPER")
    print("="*60)

    # Test product - OnePlus Buds 3
    product_name = "OnePlus Buds 3"
    amazon_url = "https://www.amazon.in/OnePlus-Wireless-Bluetooth-Cancellation-Harmonic/dp/B0DFQ1R3W4"
    flipkart_url = "https://www.flipkart.com/oneplus-buds-3-5g-bluetooth-headset/p/itm..."  # Add real URL

    results = []

    # Test Amazon
    print(f"\nTesting product: {product_name}")
    print(f"Amazon URL: {amazon_url}\n")

    amazon_result = test_amazon(amazon_url, product_name)
    if amazon_result:
        results.append(amazon_result)

    # Test Flipkart (coming soon)
    # flipkart_result = test_flipkart(flipkart_url, product_name)
    # if flipkart_result:
    #     results.append(flipkart_result)

    # Save to database
    if results:
        save_to_database(results)

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        for result in results:
            platform = result['platform']
            reviews_count = len(result['reviews'])
            print(f"\n{platform}:")
            print(f"  Product: {result['product'].get('Product_Name', 'N/A')}")
            print(f"  Price: Rs.{result['product'].get('Price', 'N/A')}")
            print(f"  Reviews scraped: {reviews_count}")

        print("\nDone! You can now view the results in the dashboard.")
    else:
        print("\nNo data was scraped successfully.")

if __name__ == "__main__":
    main()
