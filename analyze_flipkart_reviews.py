"""Scrape Flipkart reviews and analyze sentiment with Groq AI."""

import sys
import io
from sentiment_analysis.scraper.flipkart_scraper import FlipkartScraper
from sentiment_analysis.database.db_manager import DatabaseManager
from sentiment_analysis.api.groq_client import GroqSentimentAnalyzer

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    print("="*60)
    print("FLIPKART PRODUCT ANALYSIS")
    print("="*60)

    flipkart_url = "https://www.flipkart.com/oneplus-nord-buds-3-up-32db-anc-bluetooth/p/itm5ccf10ad44d73?pid=ACCH47XTY5U5SVPF"

    # Step 1: Scrape product and reviews
    print("\nStep 1: Scraping Flipkart...")
    scraper = FlipkartScraper(headless=True)

    product = scraper.scrape_product(flipkart_url)
    reviews = scraper.scrape_reviews(flipkart_url, max_pages=3)

    scraper.close()

    if not product or not reviews:
        print("\nFailed to scrape data!")
        return

    print(f"\nProduct: {product['Product_Name']}")
    print(f"Price: Rs.{product['Price']}")
    print(f"Rating: {product['Rating']}")
    print(f"Scraped {len(reviews)} reviews")

    # Step 2: Save to database
    print("\nStep 2: Saving to database...")
    db = DatabaseManager()

    db.insert_product(product)
    db.insert_reviews(reviews)

    print(f"Saved product and {len(reviews)} reviews")

    # Step 3: Analyze sentiment with Groq AI
    print("\nStep 3: Analyzing sentiment with Groq AI...")
    print("(This uses free Llama 3 model)\n")

    analyzer = GroqSentimentAnalyzer()
    sentiment_results = []

    for idx, review in enumerate(reviews, 1):
        print(f"Analyzing review {idx}/{len(reviews)}...")

        result = analyzer.analyze_sentiment(review['text'])

        sentiment_results.append({
            'review_id': review['review_id'],
            'sentiment': result['sentiment'],
            'confidence': result.get('confidence', 0.9),
            'response_time': result.get('response_time', 0),
            'tokens_used': result.get('tokens_used', 0),
            'timestamp': result.get('timestamp', ''),
            'error': result.get('error')
        })

        print(f"  → {result['sentiment']}")

    # Step 4: Save sentiment results
    print("\nStep 4: Saving sentiment analysis...")
    db.insert_sentiment_results(sentiment_results)

    # Step 5: Display statistics
    print("\n" + "="*60)
    print("SENTIMENT ANALYSIS RESULTS")
    print("="*60)

    sentiment_counts = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0}
    for result in sentiment_results:
        sentiment = result['sentiment']
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1

    print(f"\nTotal reviews analyzed: {len(reviews)}")
    print(f"POSITIVE: {sentiment_counts['POSITIVE']} ({sentiment_counts['POSITIVE']/len(reviews)*100:.1f}%)")
    print(f"NEGATIVE: {sentiment_counts['NEGATIVE']} ({sentiment_counts['NEGATIVE']/len(reviews)*100:.1f}%)")
    print(f"NEUTRAL: {sentiment_counts['NEUTRAL']} ({sentiment_counts['NEUTRAL']/len(reviews)*100:.1f}%)")

    print("\nSample reviews:")
    for i in range(min(3, len(reviews))):
        print(f"\nReview {i+1}:")
        print(f"  Rating: {reviews[i]['rating']}")
        print(f"  Text: {reviews[i]['text'][:100]}...")
        print(f"  AI Sentiment: {sentiment_results[i]['sentiment']}")

    print("\n" + "="*60)
    print("SUCCESS! Data saved to database.")
    print("View results in dashboard: http://localhost:8501")
    print("="*60)

if __name__ == "__main__":
    main()
