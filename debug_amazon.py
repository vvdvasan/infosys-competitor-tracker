"""Debug script to test Amazon scraping."""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Setup Chrome
chrome_options = Options()
# Don't use headless for debugging - we want to see what's happening
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Test URL - OnePlus Buds 3
asin = "B0DFQ1R3W4"
review_url = f"https://www.amazon.in/product-reviews/{asin}"

print(f"Opening: {review_url}")
driver.get(review_url)

# Wait for page to load
print("Waiting 5 seconds for page to load...")
time.sleep(5)

# Get page source
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# Try different selectors
print("\n" + "="*60)
print("TESTING DIFFERENT SELECTORS:")
print("="*60)

# Original selector
reviews1 = soup.find_all('div', {'data-hook': 'review'})
print(f"\n1. div[data-hook='review']: Found {len(reviews1)} reviews")

# Alternative selectors
reviews2 = soup.find_all('div', {'class': 'review'})
print(f"2. div.review: Found {len(reviews2)} reviews")

reviews3 = soup.find_all('div', {'data-hook': 'review-collapsed'})
print(f"3. div[data-hook='review-collapsed']: Found {len(reviews3)} reviews")

reviews4 = soup.find_all('div', id=lambda x: x and x.startswith('customer_review'))
print(f"4. div[id^='customer_review']: Found {len(reviews4)} reviews")

# Check for CAPTCHA or bot detection
captcha = soup.find('form', {'action': '/errors/validateCaptcha'})
if captcha:
    print("\n⚠️  CAPTCHA DETECTED - Amazon is blocking the scraper!")
else:
    print("\n✅ No CAPTCHA detected")

# Check page title
title = soup.find('title')
if title:
    print(f"\nPage Title: {title.get_text()}")

# Save HTML for manual inspection
with open('debug_amazon_page.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\n📄 HTML saved to: debug_amazon_page.html")

# Try to find review text directly
review_texts = soup.find_all('span', {'data-hook': 'review-body'})
print(f"\nReview texts found: {len(review_texts)}")

if review_texts:
    print("\nFirst review text preview:")
    print(review_texts[0].get_text()[:200])

print("\n" + "="*60)
print("Press Enter to close browser...")
input()

driver.quit()
print("Done!")
