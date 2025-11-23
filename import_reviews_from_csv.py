"""Import reviews from CSV and analyze with Groq AI."""

import sys
import io
import csv
import pandas as pd
from datetime import datetime
from sentiment_analysis.database.db_manager import DatabaseManager
from sentiment_analysis.api.groq_client import GroqSentimentAnalyzer

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def import_reviews_from_csv(csv_file_path):
    """Import reviews from CSV file and analyze sentiment."""
    print("="*60)
    print("CSV REVIEW IMPORTER & AI SENTIMENT ANALYZER")
    print("="*60)

    # Read CSV
    print(f"\nReading CSV file: {csv_file_path}")
    try:
        df = pd.read_csv(csv_file_path)
        print(f"Found {len(df)} reviews in CSV")
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")
        return

    # Initialize database and AI analyzer
    db = DatabaseManager()
    analyzer = GroqSentimentAnalyzer()

    # Group by product to save products first
    products = {}
    for _, row in df.iterrows():
        asin = str(row['product_asin'])
        if asin not in products:
            products[asin] = {
                'Product_ASIN': asin,
                'Product_Name': row['product_name'],
                'Brand': row['product_name'].split()[0],
                'Price': '',
                'MRP': '',
                'Discount': '',
                'Stock_Status': 'In Stock',
                'Rating': '',
                'Reviews': '',
                'Seller': row['platform'],
                'Product_Link': f"https://www.{row['platform'].lower()}.in/product/{asin}",
                'Reviews_Link': '',
                'Scraped_At': datetime.now().isoformat()
            }

    # Save products
    print("\nSaving products to database...")
    for asin, product_data in products.items():
        db.insert_product(product_data)
        print(f"  Saved: {product_data['Product_Name']} ({product_data['Seller']})")

    # Process reviews
    print("\nProcessing reviews and analyzing sentiment...")
    reviews_data = []
    sentiment_results = []

    for idx, row in df.iterrows():
        review_id = f"{row['platform']}_{row['product_asin']}_review_{idx}"

        # Prepare review data
        review = {
            'product_asin': str(row['product_asin']),
            'review_id': review_id,
            'reviewer_name': row['reviewer_name'],
            'rating': float(row['rating']),
            'title': row['review_title'],
            'text': row['review_text'],
            'date': row['date'],
            'verified_purchase': row['verified_purchase'].lower() == 'yes',
            'helpful_count': 0,
            'scraped_at': datetime.now().isoformat()
        }

        reviews_data.append(review)

        # Analyze sentiment with Groq AI
        print(f"\n  Review {idx+1}/{len(df)}: Analyzing with AI...")
        sentiment = analyzer.analyze_sentiment(review['text'])

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

        print(f"    Rating: {review['rating']} ⭐")
        print(f"    AI Sentiment: {sentiment['sentiment']}")
        print(f"    Platform: {row['platform']}")

    # Save to database
    print("\n\nSaving to database...")
    db.insert_reviews(reviews_data)
    db.insert_sentiment_results(sentiment_results)

    # Display statistics
    print("\n" + "="*60)
    print("IMPORT COMPLETE!")
    print("="*60)

    sentiment_counts = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0}
    for result in sentiment_results:
        if result['sentiment'] in sentiment_counts:
            sentiment_counts[result['sentiment']] += 1

    print(f"\nTotal reviews imported: {len(reviews_data)}")
    print(f"Total products: {len(products)}")
    print(f"\nSentiment Analysis:")
    print(f"  POSITIVE: {sentiment_counts['POSITIVE']} ({sentiment_counts['POSITIVE']/len(reviews_data)*100:.1f}%)")
    print(f"  NEGATIVE: {sentiment_counts['NEGATIVE']} ({sentiment_counts['NEGATIVE']/len(reviews_data)*100:.1f}%)")
    print(f"  NEUTRAL: {sentiment_counts['NEUTRAL']} ({sentiment_counts['NEUTRAL']/len(reviews_data)*100:.1f}%)")

    print(f"\nPlatform Distribution:")
    platform_counts = df['platform'].value_counts()
    for platform, count in platform_counts.items():
        print(f"  {platform}: {count} reviews")

    print("\n" + "="*60)
    print("View results in dashboard: http://localhost:8501")
    print("="*60)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = "reviews_template.csv"

    import_reviews_from_csv(csv_file)
