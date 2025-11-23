"""Test script for Amazon login and authenticated scraping."""

import os
from dotenv import load_dotenv
from sentiment_analysis.scraper.amazon_scraper import AmazonScraper
from sentiment_analysis.config import Config

# Load environment variables
load_dotenv()

def main():
    print("="*60)
    print("TESTING AMAZON LOGIN & AUTHENTICATED SCRAPING")
    print("="*60)

    # Get credentials from environment
    email = Config.AMAZON_EMAIL
    password = Config.AMAZON_PASSWORD

    if not email or not password:
        print("\n❌ ERROR: Amazon credentials not found in .env file!")
        print("\nPlease add your Amazon credentials to the .env file:")
        print("  AMAZON_EMAIL=your_email@example.com")
        print("  AMAZON_PASSWORD=your_password")
        print("\nNote: Use the .env.example file as a template.")
        return

    print(f"\n📧 Email: {email}")
    print(f"🔑 Password: {'*' * len(password)}")

    # Initialize scraper with visible browser (headless=False)
    print("\n🚀 Initializing Amazon scraper (browser will be visible)...")
    scraper = AmazonScraper(headless=False)

    try:
        # Attempt login
        print("\n🔐 Attempting to log in to Amazon India...")
        print("⏳ This may take a moment...")
        print("💡 If OTP or CAPTCHA appears, you'll have 60 seconds to complete it.\n")

        success = scraper.login(email, password)

        if success:
            print("\n" + "="*60)
            print("✅ LOGIN SUCCESSFUL!")
            print("="*60)

            # Test scraping a product with reviews
            print("\n📦 Testing product and reviews scraping...")
            test_url = "https://www.amazon.in/OnePlus-Wireless-Bluetooth-Cancellation-Harmonic/dp/B0DFQ1R3W4"

            print(f"\n🔍 Scraping product: {test_url}")
            product = scraper.scrape_product(test_url)

            if product and product.get('Product_Name'):
                print(f"\n✅ Product scraped successfully:")
                print(f"   Name: {product['Product_Name']}")
                print(f"   ASIN: {product['Product_ASIN']}")
                print(f"   Price: ₹{product.get('Price', 'N/A')}")
                print(f"   Rating: {product.get('Rating', 'N/A')}")

                # Scrape reviews
                print(f"\n📝 Scraping reviews...")
                reviews = scraper.scrape_reviews(test_url, max_pages=2)

                if reviews:
                    print(f"\n✅ Found {len(reviews)} reviews!")
                    print(f"\n   First review:")
                    print(f"   Rating: {reviews[0].get('rating', 'N/A')}")
                    print(f"   Text: {reviews[0].get('text', 'N/A')[:100]}...")
                else:
                    print("\n⚠️  No reviews found. This might mean:")
                    print("   - The product has no reviews")
                    print("   - Amazon still requires additional verification")
                    print("   - The page structure has changed")
            else:
                print("\n⚠️  Failed to scrape product information")

        else:
            print("\n" + "="*60)
            print("❌ LOGIN FAILED")
            print("="*60)
            print("\nPossible reasons:")
            print("  1. Incorrect email or password")
            print("  2. Amazon requires additional verification (OTP/CAPTCHA)")
            print("  3. Account locked or security check required")
            print("\n💡 Try logging in manually at https://www.amazon.in to check your account.")

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")

    finally:
        # Keep browser open for inspection
        print("\n" + "="*60)
        print("Press Enter to close the browser...")
        input()
        scraper.close()
        print("✅ Browser closed. Test complete.")

if __name__ == "__main__":
    main()
