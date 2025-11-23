"""Main pipeline script for running the sentiment analysis system."""

import argparse
import logging
from typing import List
from sentiment_analysis.scraper.amazon_scraper import AmazonScraper
from sentiment_analysis.database.db_manager import DatabaseManager
from sentiment_analysis.api.groq_client import GroqSentimentAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scrape_and_analyze(product_urls: List[str], max_pages: int = 10):
    """
    Scrape products and reviews, then analyze sentiment.

    Args:
        product_urls: List of Amazon product URLs to scrape
        max_pages: Maximum number of review pages to scrape per product
    """
    # Initialize components
    scraper = AmazonScraper()
    db_manager = DatabaseManager()
    analyzer = GroqSentimentAnalyzer()

    try:
        for url in product_urls:
            logger.info(f"Processing product: {url}")

            # Step 1: Scrape product information
            logger.info("Scraping product information...")
            product_data = scraper.scrape_product(url)

            if not product_data or not product_data.get('Product_ASIN'):
                logger.error(f"Failed to scrape product: {url}")
                continue

            # Save product to database
            db_manager.insert_product(product_data)
            logger.info(f"Saved product: {product_data.get('Product_Name')}")

            # Step 2: Scrape reviews
            logger.info(f"Scraping reviews (max {max_pages} pages)...")
            reviews = scraper.scrape_reviews(url, max_pages=max_pages)

            if reviews:
                db_manager.insert_reviews(reviews)
                logger.info(f"Saved {len(reviews)} reviews")

                # Step 3: Analyze sentiment
                logger.info("Analyzing sentiment...")
                results = []
                for i, review in enumerate(reviews, 1):
                    logger.info(f"Analyzing review {i}/{len(reviews)}")

                    result = analyzer.analyze_sentiment(review['text'])
                    result['review_id'] = review['review_id']
                    results.append(result)

                # Save sentiment results
                db_manager.insert_sentiment_results(results)
                logger.info(f"Saved {len(results)} sentiment analysis results")

                # Print summary
                positive = sum(1 for r in results if r['sentiment'] == 'POSITIVE')
                negative = sum(1 for r in results if r['sentiment'] == 'NEGATIVE')
                neutral = sum(1 for r in results if r['sentiment'] == 'NEUTRAL')

                logger.info("\n" + "="*50)
                logger.info("SENTIMENT ANALYSIS SUMMARY")
                logger.info("="*50)
                logger.info(f"Product: {product_data.get('Product_Name')}")
                logger.info(f"Total Reviews Analyzed: {len(results)}")
                logger.info(f"Positive: {positive} ({positive/len(results)*100:.1f}%)")
                logger.info(f"Negative: {negative} ({negative/len(results)*100:.1f}%)")
                logger.info(f"Neutral: {neutral} ({neutral/len(results)*100:.1f}%)")
                logger.info("="*50 + "\n")
            else:
                logger.warning("No reviews found")

    except Exception as e:
        logger.error(f"Error in pipeline: {str(e)}")
        raise

    finally:
        # Clean up
        scraper.close()

def analyze_pending_reviews(limit: int = 100):
    """
    Analyze reviews that haven't been processed yet.

    Args:
        limit: Maximum number of reviews to analyze
    """
    db_manager = DatabaseManager()
    analyzer = GroqSentimentAnalyzer()

    # Get unanalyzed reviews
    logger.info(f"Fetching up to {limit} unanalyzed reviews...")
    pending_reviews = db_manager.get_unanalyzed_reviews(limit=limit)

    if not pending_reviews:
        logger.info("No pending reviews to analyze")
        return

    logger.info(f"Found {len(pending_reviews)} pending reviews")

    # Analyze sentiment
    results = []
    for i, review in enumerate(pending_reviews, 1):
        logger.info(f"Analyzing review {i}/{len(pending_reviews)}")

        result = analyzer.analyze_sentiment(review['text'])
        result['review_id'] = review['review_id']
        results.append(result)

    # Save results
    db_manager.insert_sentiment_results(results)
    logger.info(f"Saved {len(results)} sentiment analysis results")

    # Print summary
    positive = sum(1 for r in results if r['sentiment'] == 'POSITIVE')
    negative = sum(1 for r in results if r['sentiment'] == 'NEGATIVE')
    neutral = sum(1 for r in results if r['sentiment'] == 'NEUTRAL')

    logger.info("\n" + "="*50)
    logger.info("SENTIMENT ANALYSIS SUMMARY")
    logger.info("="*50)
    logger.info(f"Total Reviews Analyzed: {len(results)}")
    logger.info(f"Positive: {positive} ({positive/len(results)*100:.1f}%)")
    logger.info(f"Negative: {negative} ({negative/len(results)*100:.1f}%)")
    logger.info(f"Neutral: {neutral} ({neutral/len(results)*100:.1f}%)")
    logger.info("="*50 + "\n")

def main():
    """Main function to run the pipeline."""
    parser = argparse.ArgumentParser(
        description="E-commerce Sentiment Analysis Pipeline"
    )

    parser.add_argument(
        '--scrape',
        nargs='+',
        help='Amazon product URLs to scrape and analyze'
    )

    parser.add_argument(
        '--analyze-pending',
        action='store_true',
        help='Analyze pending reviews in the database'
    )

    parser.add_argument(
        '--max-pages',
        type=int,
        default=10,
        help='Maximum number of review pages to scrape (default: 10)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Maximum number of pending reviews to analyze (default: 100)'
    )

    args = parser.parse_args()

    if args.scrape:
        logger.info("Starting scrape and analyze pipeline...")
        scrape_and_analyze(args.scrape, max_pages=args.max_pages)

    elif args.analyze_pending:
        logger.info("Analyzing pending reviews...")
        analyze_pending_reviews(limit=args.limit)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
