"""Alert manager for monitoring price and sentiment changes."""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from .email_notifier import EmailNotifier

class AlertManager:
    """Manage and check alert conditions."""

    def __init__(self, db_path='data/database/sentiment_analysis.db',
                 state_path='notifications/alert_state.json'):
        """Initialize alert manager."""
        self.db_path = db_path
        self.state_path = state_path
        self.notifier = EmailNotifier()
        self.state = self._load_state()

    def _load_state(self):
        """Load previous alert state."""
        if os.path.exists(self.state_path):
            with open(self.state_path, 'r') as f:
                return json.load(f)
        return {
            "last_prices": {},
            "last_sentiments": {},
            "last_check": None,
            "alerts_sent": []
        }

    def _save_state(self):
        """Save current alert state."""
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        with open(self.state_path, 'w') as f:
            json.dump(self.state, f, indent=4)

    def check_price_alerts(self, product_id='iphone14_128gb', threshold_percentage=5.0):
        """Check for price drops and send alerts."""
        alerts_sent = []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get current prices from price_history
        try:
            from price_tracker.price_history_manager import PriceHistoryManager
            price_manager = PriceHistoryManager()

            for platform in ['amazon', 'flipkart']:
                stats = price_manager.get_price_statistics(product_id, platform, days=1)

                if not stats:
                    continue

                current_price = stats['current_price']
                platform_key = f"{product_id}_{platform}"

                # Get previous price from state
                previous_price = self.state['last_prices'].get(platform_key)

                if previous_price and current_price < previous_price:
                    # Calculate drop percentage
                    drop_pct = ((previous_price - current_price) / previous_price) * 100

                    if drop_pct >= threshold_percentage:
                        # Get deal score and recommendation
                        recommendation_data = price_manager.get_buy_recommendation(
                            product_id, platform, days=90
                        )

                        # Send alert
                        success = self.notifier.send_price_drop_alert(
                            product_name="Apple iPhone 14 (128GB)",
                            platform=platform.title(),
                            old_price=previous_price,
                            new_price=current_price,
                            drop_percentage=drop_pct,
                            deal_score=recommendation_data['deal_score'],
                            recommendation=recommendation_data['recommendation']
                        )

                        if success:
                            alert = {
                                "type": "price_drop",
                                "product": product_id,
                                "platform": platform,
                                "old_price": previous_price,
                                "new_price": current_price,
                                "drop_percentage": drop_pct,
                                "timestamp": datetime.now().isoformat()
                            }
                            alerts_sent.append(alert)
                            self.state['alerts_sent'].append(alert)

                # Update state with current price
                self.state['last_prices'][platform_key] = current_price

        except Exception as e:
            print(f"[ERROR] Price alert check failed: {e}")

        conn.close()
        return alerts_sent

    def check_sentiment_alerts(self, product_asin=None, threshold_percentage=10.0):
        """Check for significant sentiment changes and send alerts."""
        alerts_sent = []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get current sentiment distribution by platform
            query = """
                SELECT
                    CASE
                        WHEN p.product_link LIKE '%amazon%' THEN 'Amazon'
                        WHEN p.product_link LIKE '%flipkart%' THEN 'Flipkart'
                        ELSE 'Other'
                    END as platform,
                    COUNT(CASE WHEN sa.sentiment = 'POSITIVE' THEN 1 END) * 100.0 / COUNT(*) as positive_pct,
                    COUNT(*) as total_reviews
                FROM sentiment_analysis sa
                JOIN reviews r ON sa.review_id = r.review_id
                JOIN products p ON r.product_asin = p.product_asin
                WHERE sa.sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL')
                AND p.product_name LIKE '%iPhone 14%'
                GROUP BY platform
            """

            cursor.execute(query)
            results = cursor.fetchall()

            for platform, current_positive_pct, total_reviews in results:
                if total_reviews < 5:  # Skip if not enough data
                    continue

                platform_key = f"iphone14_{platform.lower()}"

                # Get previous sentiment from state
                previous_positive_pct = self.state['last_sentiments'].get(platform_key)

                if previous_positive_pct is not None:
                    sentiment_change = current_positive_pct - previous_positive_pct

                    # Check if change is significant
                    if abs(sentiment_change) >= threshold_percentage:
                        trend = "improving" if sentiment_change > 0 else "declining"

                        # Send alert
                        success = self.notifier.send_sentiment_change_alert(
                            product_name="Apple iPhone 14 (128GB)",
                            platform=platform,
                            old_sentiment_pct=previous_positive_pct,
                            new_sentiment_pct=current_positive_pct,
                            sentiment_change=sentiment_change,
                            trend=trend
                        )

                        if success:
                            alert = {
                                "type": "sentiment_change",
                                "product": "iphone14",
                                "platform": platform,
                                "old_sentiment": previous_positive_pct,
                                "new_sentiment": current_positive_pct,
                                "change": sentiment_change,
                                "trend": trend,
                                "timestamp": datetime.now().isoformat()
                            }
                            alerts_sent.append(alert)
                            self.state['alerts_sent'].append(alert)

                # Update state with current sentiment
                self.state['last_sentiments'][platform_key] = current_positive_pct

        except Exception as e:
            print(f"[ERROR] Sentiment alert check failed: {e}")

        conn.close()
        return alerts_sent

    def check_all_alerts(self, price_threshold=5.0, sentiment_threshold=10.0):
        """Check all alert types and send notifications."""
        print("[INFO] Checking for alerts...")

        price_alerts = self.check_price_alerts(threshold_percentage=price_threshold)
        sentiment_alerts = self.check_sentiment_alerts(threshold_percentage=sentiment_threshold)

        total_alerts = len(price_alerts) + len(sentiment_alerts)

        if total_alerts > 0:
            print(f"[OK] Sent {total_alerts} alerts:")
            print(f"  - Price alerts: {len(price_alerts)}")
            print(f"  - Sentiment alerts: {len(sentiment_alerts)}")
        else:
            print("[INFO] No alerts triggered")

        # Update state
        self.state['last_check'] = datetime.now().isoformat()
        self._save_state()

        return {
            "price_alerts": price_alerts,
            "sentiment_alerts": sentiment_alerts,
            "total": total_alerts
        }

    def get_alert_history(self, limit=10):
        """Get recent alert history."""
        alerts = self.state.get('alerts_sent', [])
        return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def clear_alert_history(self):
        """Clear all alert history."""
        self.state['alerts_sent'] = []
        self._save_state()
        print("[OK] Alert history cleared")
