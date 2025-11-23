"""Quick product comparison across Amazon and Flipkart."""

import sys
import io
from sentiment_analysis.scraper.amazon_scraper import AmazonScraper
from sentiment_analysis.scraper.flipkart_scraper import FlipkartScraper

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    print("="*60)
    print("CROSS-PLATFORM PRODUCT COMPARISON")
    print("="*60)

    # OnePlus Buds 3 URLs
    amazon_url = "https://www.amazon.in/OnePlus-Wireless-Bluetooth-Cancellation-Harmonic/dp/B0DFQ1R3W4"
    flipkart_url = "https://www.flipkart.com/oneplus-nord-buds-3-up-32db-anc-bluetooth/p/itm5ccf10ad44d73?pid=ACCH47XTY5U5SVPF&lid=LSTACCH47XTY5U5SVPFDOWWMU&marketplace=FLIPKART&q=OnePlus+Buds+3&store=0pm%2Ffcn&srno=s_1_2&otracker=search&otracker1=search&fm=Search&iid=74ff871b-16fd-47a1-b2b7-4e1490891827.ACCH47XTY5U5SVPF.SEARCH&ppt=sp&ppn=sp&ssid=3lr9ugcts0000001763808266498&qH=f830d0d79057c07f"

    print("\nScraping OnePlus Buds 3 from multiple platforms...\n")

    # Amazon
    print("Scraping Amazon India...")
    amazon_scraper = AmazonScraper(headless=True)
    amazon_product = amazon_scraper.scrape_product(amazon_url)
    amazon_scraper.close()

    # Flipkart
    print("Scraping Flipkart...")
    flipkart_scraper = FlipkartScraper(headless=True)
    flipkart_product = flipkart_scraper.scrape_product(flipkart_url)
    flipkart_reviews = flipkart_scraper.scrape_reviews(flipkart_url, max_pages=2)
    flipkart_scraper.close()

    # Display comparison
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)

    print("\n--- AMAZON INDIA ---")
    if amazon_product and amazon_product.get('Product_Name'):
        print(f"Product: {amazon_product.get('Product_Name', 'N/A')}")
        print(f"Price: Rs.{amazon_product.get('Price', 'N/A')}")
        print(f"Rating: {amazon_product.get('Rating', 'N/A')}")
        print(f"Reviews: {amazon_product.get('Reviews', 'N/A')}")
        print(f"Stock: {amazon_product.get('Stock_Status', 'N/A')}")
    else:
        print("Failed to scrape Amazon product")

    print("\n--- FLIPKART ---")
    if flipkart_product and flipkart_product.get('Product_Name'):
        print(f"Product: {flipkart_product.get('Product_Name', 'N/A')}")
        print(f"Price: Rs.{flipkart_product.get('Price', 'N/A')}")
        print(f"Rating: {flipkart_product.get('Rating', 'N/A')}")
        print(f"Reviews: {flipkart_product.get('Reviews', 'N/A')}")
        print(f"Stock: {flipkart_product.get('Stock_Status', 'N/A')}")
        print(f"Flipkart reviews scraped: {len(flipkart_reviews)}")
    else:
        print("Failed to scrape Flipkart product")

    print("\n" + "="*60)
    print("PRICE COMPARISON")
    print("="*60)

    amazon_price = float(amazon_product.get('Price', 0) or 0) if amazon_product else 0
    flipkart_price = float(flipkart_product.get('Price', 0) or 0) if flipkart_product else 0

    if amazon_price and flipkart_price:
        if amazon_price < flipkart_price:
            diff = flipkart_price - amazon_price
            print(f"\nAmazon is CHEAPER by Rs.{diff:.2f}")
        elif flipkart_price < amazon_price:
            diff = amazon_price - flipkart_price
            print(f"\nFlipkart is CHEAPER by Rs.{diff:.2f}")
        else:
            print(f"\nBoth platforms have the SAME PRICE: Rs.{amazon_price}")
    else:
        print("\nCould not compare prices")

    print("\n")

if __name__ == "__main__":
    main()
