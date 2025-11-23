"""Populate database with sample data for demo purposes."""

import random
import sqlite3
from datetime import datetime, timedelta
from sentiment_analysis.database.db_manager import DatabaseManager

# Sample products (OnePlus Buds 3 and competitors)
SAMPLE_PRODUCTS = [
    {
        "name": "OnePlus Buds 3",
        "asin": "B0DFQ1R3W4",
        "price": 5999.00,
        "rating": 4.2,
        "reviews_count": 1247,
        "url": "https://www.amazon.in/dp/B0DFQ1R3W4"
    },
    {
        "name": "Samsung Galaxy Buds2 Pro",
        "asin": "B0B3R7Z8YZ",
        "price": 8999.00,
        "rating": 4.3,
        "reviews_count": 2156,
        "url": "https://www.amazon.in/dp/B0B3R7Z8YZ"
    },
    {
        "name": "Sony WF-1000XM5",
        "asin": "B0C33XXZ5B",
        "price": 19990.00,
        "rating": 4.5,
        "reviews_count": 892,
        "url": "https://www.amazon.in/dp/B0C33XXZ5B"
    },
    {
        "name": "JBL Wave Beam",
        "asin": "B0BZCWH6Q7",
        "price": 2999.00,
        "rating": 4.1,
        "reviews_count": 3421,
        "url": "https://www.amazon.in/dp/B0BZCWH6Q7"
    }
]

# Sample review templates
POSITIVE_REVIEWS = [
    "Excellent sound quality! The bass is amazing and the noise cancellation works really well.",
    "Best earbuds I've ever owned. Battery life is outstanding and they're super comfortable.",
    "Great value for money. Sound quality is crystal clear and they fit perfectly.",
    "Impressed with the build quality. These feel premium and the case is compact.",
    "Amazing product! The ANC is surprisingly good and call quality is excellent.",
    "Love these earbuds! They stay in my ears during workouts and sound fantastic.",
    "Perfect for daily use. Battery lasts all day and charging is super fast.",
    "Sound quality is incredible for the price. Highly recommended!",
    "Very happy with this purchase. The app works great and customization options are nice.",
    "Great design and even better performance. Worth every penny!"
]

NEGATIVE_REVIEWS = [
    "Disappointed with the battery life. Doesn't last as long as advertised.",
    "Sound quality is mediocre. Expected better at this price point.",
    "Connectivity issues constantly. They keep disconnecting from my phone.",
    "Not comfortable for long use. Started hurting my ears after an hour.",
    "The noise cancellation is practically useless. Very disappointed.",
    "Build quality feels cheap. One earbud stopped working after 2 weeks.",
    "Too expensive for what you get. There are better options available.",
    "App is buggy and crashes frequently. Very frustrating experience.",
    "Poor call quality. People can barely hear me during calls.",
    "The fit is terrible. They keep falling out of my ears."
]

NEUTRAL_REVIEWS = [
    "Decent earbuds. Nothing exceptional but they get the job done.",
    "They're okay for the price. Sound is average, battery life is acceptable.",
    "Not bad but not great either. Suitable for casual listening.",
    "Average product. Works fine but doesn't stand out in any way.",
    "It's an okay purchase. Some features work well, others could be better.",
    "Satisfactory performance overall. Nothing to complain about but nothing special.",
    "Fair quality for the money. Does what it's supposed to do.",
    "Standard earbuds. No major issues but no wow factor either.",
    "Acceptable sound quality. They serve their purpose adequately.",
    "Basic functionality works fine. Don't expect premium features."
]

def generate_sample_reviews(product, num_reviews=50):
    """Generate sample reviews for a product."""
    reviews = []

    # Distribution: 60% positive, 20% negative, 20% neutral
    for i in range(num_reviews):
        rand = random.random()

        if rand < 0.6:  # Positive
            review_text = random.choice(POSITIVE_REVIEWS)
            rating = random.choice([4, 5])
            sentiment = "POSITIVE"
        elif rand < 0.8:  # Negative
            review_text = random.choice(NEGATIVE_REVIEWS)
            rating = random.choice([1, 2])
            sentiment = "NEGATIVE"
        else:  # Neutral
            review_text = random.choice(NEUTRAL_REVIEWS)
            rating = 3
            sentiment = "NEUTRAL"

        # Random date within last 3 months
        days_ago = random.randint(1, 90)
        review_date = datetime.now() - timedelta(days=days_ago)

        reviews.append({
            "review_id": f"{product['asin']}_review_{i+1}",
            "asin": product['asin'],
            "rating": rating,
            "title": f"Review {i+1}",
            "text": review_text,
            "date": review_date.strftime("%Y-%m-%d"),
            "verified_purchase": random.choice([True, True, True, False]),  # 75% verified
            "helpful_count": random.randint(0, 50),
            "sentiment": sentiment,
            "confidence": round(random.uniform(0.85, 0.99), 2)
        })

    return reviews

def main():
    """Populate database with sample data."""
    print("="*60)
    print("POPULATING DATABASE WITH SAMPLE DATA")
    print("="*60)

    db = DatabaseManager()

    # Clear existing data
    print("\nClearing existing data...")
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sentiment_analysis")
        cursor.execute("DELETE FROM reviews")
        cursor.execute("DELETE FROM products")
        conn.commit()
    print("✅ Existing data cleared")

    total_products = 0
    total_reviews = 0
    total_sentiments = 0

    # Add products and reviews
    for product_data in SAMPLE_PRODUCTS:
        print(f"\nProcessing: {product_data['name']}")

        # Prepare product data for insertion
        product_db_data = {
            'Product_ASIN': product_data['asin'],
            'Product_Name': product_data['name'],
            'Brand': product_data['name'].split()[0],  # Extract brand from name
            'Price': product_data['price'],
            'MRP': product_data['price'],
            'Discount': '0%',
            'Stock_Status': 'In Stock',
            'Rating': product_data['rating'],
            'Reviews': product_data['reviews_count'],
            'Seller': 'Amazon',
            'Product_Link': product_data['url'],
            'Reviews_Link': f"https://www.amazon.in/product-reviews/{product_data['asin']}",
            'Scraped_At': datetime.now().isoformat()
        }

        # Save product
        db.insert_product(product_db_data)
        total_products += 1
        print(f"✅ Product added: {product_data['name']}")

        # Generate and save reviews
        reviews = generate_sample_reviews(product_data, num_reviews=50)

        # Prepare reviews for insertion
        reviews_db_data = []
        sentiment_results = []

        for review in reviews:
            reviews_db_data.append({
                'product_asin': review['asin'],
                'review_id': review['review_id'],
                'reviewer_name': f"Customer_{random.randint(1000, 9999)}",
                'rating': review['rating'],
                'title': review['title'],
                'text': review['text'],
                'date': review['date'],
                'verified_purchase': review['verified_purchase'],
                'helpful_count': review['helpful_count'],
                'scraped_at': datetime.now().isoformat()
            })

            sentiment_results.append({
                'review_id': review['review_id'],
                'sentiment': review['sentiment'],
                'confidence': review['confidence'],
                'response_time': 0.5,
                'tokens_used': 100,
                'timestamp': datetime.now().isoformat(),
                'error': None
            })

        # Insert reviews and sentiment results
        inserted = db.insert_reviews(reviews_db_data)
        total_reviews += inserted

        inserted_sentiments = db.insert_sentiment_results(sentiment_results)
        total_sentiments += inserted_sentiments

        print(f"✅ Added {inserted} reviews with sentiment analysis")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Total products added: {total_products}")
    print(f"✅ Total reviews added: {total_reviews}")
    print(f"✅ Total sentiment analyses: {total_sentiments}")

    # Display statistics
    stats = db.get_sentiment_statistics()
    sentiment_dist = stats.get('sentiment_distribution', {})
    print(f"\nSentiment Distribution:")
    print(f"  POSITIVE: {sentiment_dist.get('POSITIVE', 0)}")
    print(f"  NEGATIVE: {sentiment_dist.get('NEGATIVE', 0)}")
    print(f"  NEUTRAL: {sentiment_dist.get('NEUTRAL', 0)}")

    print("\n🎉 Sample data loaded successfully!")
    print("\nYou can now:")
    print("1. View the dashboard: streamlit run dashboard/app.py")
    print("2. The dashboard will show all sample products and reviews")
    print("3. Try filtering by product, sentiment, date range, etc.")
    print("\nNote: This is sample data for demonstration purposes.")
    print("="*60)

if __name__ == "__main__":
    main()
