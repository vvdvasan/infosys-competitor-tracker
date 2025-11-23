"""Analyze iPhone 14 Flipkart reviews with Llama 3.3 70B."""

import sys
import io
import pandas as pd
from datetime import datetime, timedelta
import random
from sentiment_analysis.database.db_manager import DatabaseManager
from sentiment_analysis.api.groq_client import GroqSentimentAnalyzer

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_reviews():
    """Analyze iPhone 14 reviews from Flipkart."""
    print("="*60)
    print("iPHONE 14 SENTIMENT ANALYSIS")
    print("Using: Llama 3.3 70B (Latest FREE AI Model)")
    print("="*60)

    # Read CSV
    print("\nReading iPhone 14 reviews...")
    df = pd.read_csv('iphone14_flipkart_reviews.csv')
    print(f"Found {len(df)} reviews")

    # Initialize
    db = DatabaseManager()
    analyzer = GroqSentimentAnalyzer()

    # Create product entry
    product_data = {
        'Product_ASIN': 'IPHONE14_FLIP',
        'Product_Name': 'iPhone 14 (128GB)',
        'Brand': 'Apple',
        'Price': '66999',
        'MRP': '79900',
        'Discount': '16%',
        'Stock_Status': 'In Stock',
        'Rating': '4.6',
        'Reviews': str(len(df)),
        'Seller': 'Flipkart',
        'Product_Link': 'https://www.flipkart.com/apple-iphone-14-blue-128-gb/p/itm9e6293c322a84',
        'Reviews_Link': '',
        'Scraped_At': datetime.now().isoformat()
    }

    print("\nSaving product to database...")
    db.insert_product(product_data)
    print(f"  Product: {product_data['Product_Name']}")
    print(f"  Platform: Flipkart")
    print(f"  Price: Rs.{product_data['Price']}")
    print(f"  Rating: {product_data['Rating']}")

    # Process reviews
    print(f"\nAnalyzing {len(df)} reviews with AI...")
    print("(This will take about 2-3 minutes)\n")

    reviews_data = []
    sentiment_results = []

    for idx, row in df.iterrows():
        review_text = str(row['text'])
        rating = float(row['rating'])

        # Generate review date (last 3 months)
        days_ago = random.randint(1, 90)
        review_date = datetime.now() - timedelta(days=days_ago)

        review_id = f"IPHONE14_FLIP_review_{idx}"

        # Prepare review data
        review = {
            'product_asin': 'IPHONE14_FLIP',
            'review_id': review_id,
            'reviewer_name': f"Customer_{random.randint(1000, 9999)}",
            'rating': rating,
            'title': review_text[:50] + "..." if len(review_text) > 50 else review_text,
            'text': review_text,
            'date': review_date.strftime("%Y-%m-%d"),
            'verified_purchase': True,
            'helpful_count': random.randint(0, 20),
            'scraped_at': datetime.now().isoformat()
        }

        reviews_data.append(review)

        # Analyze sentiment with AI
        progress = f"[{idx+1}/{len(df)}]"
        print(f"{progress} Analyzing review (Rating: {rating})... ", end='', flush=True)

        sentiment = analyzer.analyze_sentiment(review_text)

        sentiment_result = {
            'review_id': review_id,
            'sentiment': sentiment['sentiment'],
            'confidence': sentiment.get('confidence', 0.9),
            'response_time': sentiment.get('response_time', 0),
            'tokens_used': sentiment.get('tokens_used', 0),
            'timestamp': datetime.now().isoformat(),
            'error': sentiment.get('error')
        }

        sentiment_results.append(sentiment_result)

        print(f"AI: {sentiment['sentiment']}")

    # Save to database
    print("\n\nSaving to database...")
    db.insert_reviews(reviews_data)
    db.insert_sentiment_results(sentiment_results)

    # Calculate statistics
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE!")
    print("="*60)

    sentiment_counts = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0}
    for result in sentiment_results:
        if result['sentiment'] in sentiment_counts:
            sentiment_counts[result['sentiment']] += 1

    print(f"\nTotal reviews analyzed: {len(reviews_data)}")
    print(f"\nSentiment Distribution:")
    print(f"  POSITIVE: {sentiment_counts['POSITIVE']} ({sentiment_counts['POSITIVE']/len(reviews_data)*100:.1f}%)")
    print(f"  NEGATIVE: {sentiment_counts['NEGATIVE']} ({sentiment_counts['NEGATIVE']/len(reviews_data)*100:.1f}%)")
    print(f"  NEUTRAL: {sentiment_counts['NEUTRAL']} ({sentiment_counts['NEUTRAL']/len(reviews_data)*100:.1f}%)")

    print(f"\nRating Distribution:")
    rating_counts = df['rating'].value_counts().sort_index(ascending=False)
    for rating, count in rating_counts.items():
        print(f"  {int(rating)} stars: {count} reviews")

    print(f"\nAI Model Used: Llama 3.3 70B (Groq)")
    print(f"Total tokens processed: {sum(r.get('tokens_used', 0) for r in sentiment_results)}")

    print("\n" + "="*60)
    print("View results in dashboard: http://localhost:8501")
    print("="*60)

    # Show sample insights
    print("\n\nSample Reviews:")
    for i in range(min(3, len(reviews_data))):
        print(f"\n{i+1}. Rating: {reviews_data[i]['rating']} | AI Sentiment: {sentiment_results[i]['sentiment']}")
        print(f"   Text: {reviews_data[i]['text'][:100]}...")

if __name__ == "__main__":
    analyze_reviews()
