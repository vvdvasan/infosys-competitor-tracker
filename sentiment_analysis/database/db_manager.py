"""Database manager for storing scraped data and sentiment analysis results."""

import sqlite3
import re
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
import logging
from sentiment_analysis.config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manage SQLite database operations."""

    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        self.db_path = db_path or str(Config.DATABASE_PATH)
        self.init_database()

    def init_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_asin TEXT UNIQUE,
                    product_name TEXT,
                    brand TEXT,
                    price REAL,
                    mrp REAL,
                    discount TEXT,
                    stock_status TEXT,
                    rating REAL,
                    review_count INTEGER,
                    seller TEXT,
                    product_link TEXT,
                    reviews_link TEXT,
                    scraped_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Reviews table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_asin TEXT,
                    review_id TEXT UNIQUE,
                    reviewer_name TEXT,
                    rating REAL,
                    title TEXT,
                    text TEXT,
                    date TEXT,
                    verified_purchase BOOLEAN,
                    helpful_count INTEGER,
                    scraped_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_asin) REFERENCES products(product_asin)
                )
            """)

            # Sentiment analysis results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    review_id TEXT,
                    sentiment TEXT,
                    confidence REAL,
                    response_time REAL,
                    tokens_used INTEGER,
                    analyzed_at TIMESTAMP,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (review_id) REFERENCES reviews(review_id)
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_asin ON products(product_asin)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_product ON reviews(product_asin)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_review ON sentiment_analysis(review_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_label ON sentiment_analysis(sentiment)")

            conn.commit()
            logger.info("Database initialized successfully")

    def insert_product(self, product_data: Dict) -> int:
        """Insert or update product information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Convert price strings to floats
            price = self._parse_price(product_data.get('Price', ''))
            mrp = self._parse_price(product_data.get('MRP', ''))
            rating = self._parse_float(product_data.get('Rating', ''))
            review_count = self._parse_int(product_data.get('Reviews', ''))

            cursor.execute("""
                INSERT OR REPLACE INTO products (
                    product_asin, product_name, brand, price, mrp, discount,
                    stock_status, rating, review_count, seller, product_link,
                    reviews_link, scraped_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_data.get('Product_ASIN'),
                product_data.get('Product_Name'),
                product_data.get('Brand'),
                price,
                mrp,
                product_data.get('Discount'),
                product_data.get('Stock_Status'),
                rating,
                review_count,
                product_data.get('Seller'),
                product_data.get('Product_Link'),
                product_data.get('Reviews_Link'),
                product_data.get('Scraped_At'),
                datetime.now()
            ))

            conn.commit()
            return cursor.lastrowid

    def insert_reviews(self, reviews: List[Dict]) -> int:
        """Insert multiple reviews."""
        inserted = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for review in reviews:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO reviews (
                            product_asin, review_id, reviewer_name, rating,
                            title, text, date, verified_purchase, helpful_count,
                            scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        review.get('product_asin'),
                        review.get('review_id'),
                        review.get('reviewer_name'),
                        self._parse_float(review.get('rating', '')),
                        review.get('title'),
                        review.get('text'),
                        review.get('date'),
                        review.get('verified_purchase', False),
                        review.get('helpful_count', 0),
                        review.get('scraped_at')
                    ))

                    if cursor.rowcount > 0:
                        inserted += 1

                except Exception as e:
                    logger.error(f"Error inserting review: {str(e)}")

            conn.commit()

        logger.info(f"Inserted {inserted} new reviews")
        return inserted

    def insert_sentiment_results(self, results: List[Dict]) -> int:
        """Insert sentiment analysis results."""
        inserted = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for result in results:
                try:
                    cursor.execute("""
                        INSERT INTO sentiment_analysis (
                            review_id, sentiment, confidence, response_time,
                            tokens_used, analyzed_at, error
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        result.get('review_id'),
                        result.get('sentiment'),
                        result.get('confidence'),
                        result.get('response_time'),
                        result.get('tokens_used'),
                        result.get('timestamp'),
                        result.get('error')
                    ))

                    inserted += 1

                except Exception as e:
                    logger.error(f"Error inserting sentiment result: {str(e)}")

            conn.commit()

        logger.info(f"Inserted {inserted} sentiment results")
        return inserted

    def get_unanalyzed_reviews(self, limit: int = 100) -> List[Dict]:
        """Get reviews that haven't been analyzed yet."""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT r.review_id, r.text, r.product_asin
                FROM reviews r
                LEFT JOIN sentiment_analysis sa ON r.review_id = sa.review_id
                WHERE sa.id IS NULL AND r.text IS NOT NULL AND r.text != ''
                LIMIT ?
            """

            df = pd.read_sql_query(query, conn, params=[limit])
            return df.to_dict('records')

    def get_sentiment_statistics(self) -> Dict:
        """Get sentiment analysis statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Overall statistics
            cursor.execute("""
                SELECT
                    COUNT(*) as total_reviews,
                    COUNT(DISTINCT product_asin) as total_products,
                    AVG(rating) as avg_rating
                FROM reviews
            """)
            overall_stats = cursor.fetchone()

            # Sentiment distribution
            cursor.execute("""
                SELECT sentiment, COUNT(*) as count
                FROM sentiment_analysis
                WHERE sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL')
                GROUP BY sentiment
            """)
            sentiment_dist = cursor.fetchall()

            # Product-wise sentiment
            cursor.execute("""
                SELECT
                    p.product_name,
                    p.brand,
                    sa.sentiment,
                    COUNT(*) as count
                FROM sentiment_analysis sa
                JOIN reviews r ON sa.review_id = r.review_id
                JOIN products p ON r.product_asin = p.product_asin
                WHERE sa.sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL')
                GROUP BY p.product_asin, sa.sentiment
            """)
            product_sentiment = cursor.fetchall()

            return {
                'overall': {
                    'total_reviews': overall_stats[0],
                    'total_products': overall_stats[1],
                    'avg_rating': overall_stats[2]
                },
                'sentiment_distribution': {row[0]: row[1] for row in sentiment_dist},
                'product_sentiment': product_sentiment
            }

    def _parse_price(self, price_str: str) -> Optional[float]:
        """Parse price string to float."""
        if not price_str:
            return None
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[₹$,]', '', str(price_str))
            return float(cleaned)
        except:
            return None

    def _parse_float(self, value: str) -> Optional[float]:
        """Parse string to float."""
        try:
            return float(value) if value else None
        except:
            return None

    def _parse_int(self, value: str) -> Optional[int]:
        """Parse string to integer."""
        try:
            # Remove commas from numbers
            cleaned = str(value).replace(',', '')
            return int(cleaned) if cleaned else None
        except:
            return None
