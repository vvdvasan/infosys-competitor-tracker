"""Groq API client with rate limiting and error handling."""

import time
import json
from typing import List, Dict, Optional
from groq import Groq
from datetime import datetime, timedelta
import logging
from sentiment_analysis.config import Config
from sentiment_analysis.utils.rate_limiter import RateLimiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroqSentimentAnalyzer:
    """Groq API client for sentiment analysis with rate limiting."""

    def __init__(self):
        """Initialize Groq client with API key and rate limiter."""
        if not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=Config.GROQ_RPM,
            max_tokens_per_minute=Config.GROQ_TPM
        )
        self.model = Config.GROQ_MODEL

    def _create_prompt(self, review_text: str) -> str:
        """Create a structured prompt for sentiment analysis."""
        prompt = f"""Analyze the sentiment of the following product review and classify it as POSITIVE, NEGATIVE, or NEUTRAL.

Review: {review_text[:Config.MAX_REVIEW_LENGTH]}

Instructions:
1. POSITIVE: Customer is satisfied, recommends the product, expresses happiness
2. NEGATIVE: Customer is dissatisfied, complains, expresses frustration
3. NEUTRAL: Mixed feelings, factual description without clear emotion

Respond with ONLY one word: POSITIVE, NEGATIVE, or NEUTRAL."""
        return prompt

    def analyze_sentiment(self, review_text: str) -> Dict[str, any]:
        """
        Analyze sentiment of a single review.

        Args:
            review_text: The review text to analyze

        Returns:
            Dictionary with sentiment and metadata
        """
        if not review_text or len(review_text.strip()) < 10:
            return {
                "sentiment": "NEUTRAL",
                "confidence": 0.0,
                "error": "Review too short"
            }

        try:
            # Wait for rate limit
            self.rate_limiter.wait_if_needed()

            # Create completion
            prompt = self._create_prompt(review_text)

            start_time = time.time()
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert. Respond only with: POSITIVE, NEGATIVE, or NEUTRAL."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.1,  # Low temperature for consistency
                max_tokens=10
            )

            response_time = time.time() - start_time

            # Extract sentiment
            sentiment = response.choices[0].message.content.strip().upper()

            # Validate response
            if sentiment not in Config.SENTIMENT_LABELS:
                logger.warning(f"Invalid sentiment response: {sentiment}")
                sentiment = "NEUTRAL"

            # Update rate limiter
            tokens_used = response.usage.total_tokens if response.usage else 100
            self.rate_limiter.add_request(tokens_used)

            return {
                "sentiment": sentiment,
                "confidence": 0.95,  # Groq doesn't provide confidence scores
                "response_time": response_time,
                "tokens_used": tokens_used,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                "sentiment": "NEUTRAL",
                "confidence": 0.0,
                "error": str(e)
            }

    def analyze_batch(self, reviews: List[str], batch_size: int = 10) -> List[Dict]:
        """
        Analyze multiple reviews in batches.

        Args:
            reviews: List of review texts
            batch_size: Number of reviews to process at once

        Returns:
            List of sentiment results
        """
        results = []
        total_reviews = len(reviews)

        logger.info(f"Starting batch analysis of {total_reviews} reviews")

        for i in range(0, total_reviews, batch_size):
            batch = reviews[i:i + batch_size]
            batch_results = []

            for review in batch:
                result = self.analyze_sentiment(review)
                batch_results.append(result)

                # Small delay between requests
                time.sleep(0.5)

            results.extend(batch_results)
            logger.info(f"Processed {min(i + batch_size, total_reviews)}/{total_reviews} reviews")

        return results
