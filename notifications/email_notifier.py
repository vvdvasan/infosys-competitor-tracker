"""Email notification system using SMTP."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
import os

class EmailNotifier:
    """Send email notifications for price drops and sentiment changes."""

    def __init__(self, config_path='notifications/email_config.json'):
        """Initialize email notifier with configuration."""
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """Load email configuration from JSON file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "your-email@gmail.com",
                "sender_password": "your-app-password",
                "recipient_emails": ["recipient@example.com"],
                "enabled": False
            }

    def save_config(self, config):
        """Save email configuration to JSON file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
        self.config = config

    def send_email(self, subject, body_html, body_text=None):
        """Send email notification."""
        if not self.config.get('enabled', False):
            print("[INFO] Email notifications disabled in config")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config['sender_email']
            msg['To'] = ', '.join(self.config['recipient_emails'])
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

            # Add text and HTML parts
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)

            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['sender_email'], self.config['sender_password'])
                server.send_message(msg)

            print(f"[OK] Email sent: {subject}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to send email: {e}")
            return False

    def send_price_drop_alert(self, product_name, platform, old_price, new_price,
                              drop_percentage, deal_score, recommendation):
        """Send price drop notification."""
        savings = old_price - new_price

        subject = f"Price Drop Alert: {product_name} - Save Rs.{savings:,.0f}!"

        # HTML body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .price-box {{ background-color: #f8f9fa; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }}
                .old-price {{ text-decoration: line-through; color: #dc3545; font-size: 18px; }}
                .new-price {{ color: #28a745; font-size: 28px; font-weight: bold; }}
                .savings {{ color: #28a745; font-size: 20px; font-weight: bold; }}
                .recommendation {{ background-color: #28a745; color: white; padding: 10px 20px;
                                  border-radius: 5px; display: inline-block; margin: 10px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center;
                           margin-top: 20px; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Price Drop Alert!</h1>
                <p>{product_name}</p>
            </div>

            <div class="content">
                <h2>Great News!</h2>
                <p>The price of <strong>{product_name}</strong> on <strong>{platform}</strong> has dropped!</p>

                <div class="price-box">
                    <p><span class="old-price">Rs.{old_price:,.0f}</span>
                       → <span class="new-price">Rs.{new_price:,.0f}</span></p>
                    <p class="savings">You save: Rs.{savings:,.0f} ({drop_percentage:.1f}% off!)</p>
                </div>

                <h3>Deal Analysis:</h3>
                <ul>
                    <li><strong>Deal Score:</strong> {deal_score:.0f}/100</li>
                    <li><strong>Price Position:</strong> {100-deal_score:.1f}% above historical lowest</li>
                    <li><strong>Recommendation:</strong> <span class="recommendation">{recommendation}</span></li>
                </ul>

                <h3>Why is this a good deal?</h3>
                <p>Based on 90 days of price history, this is one of the best prices we've seen!</p>

                <p style="margin-top: 30px;">
                    <a href="http://localhost:8501" style="background-color: #007bff; color: white;
                       padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                       View in Dashboard
                    </a>
                </p>
            </div>

            <div class="footer">
                <p>This is an automated alert from E-Commerce Sentiment Tracker</p>
                <p>Powered by AI | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """

        # Plain text version
        text_body = f"""
        PRICE DROP ALERT: {product_name}

        Platform: {platform}
        Old Price: Rs.{old_price:,.0f}
        New Price: Rs.{new_price:,.0f}
        You Save: Rs.{savings:,.0f} ({drop_percentage:.1f}% off!)

        Deal Score: {deal_score:.0f}/100
        Recommendation: {recommendation}

        View dashboard: http://localhost:8501

        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        return self.send_email(subject, html_body, text_body)

    def send_sentiment_change_alert(self, product_name, platform, old_sentiment_pct,
                                   new_sentiment_pct, sentiment_change, trend):
        """Send sentiment change notification."""

        if trend == "improving":
            color = "#28a745"
            emoji = "📈"
            alert_type = "Positive"
        else:
            color = "#dc3545"
            emoji = "📉"
            alert_type = "Warning"

        subject = f"{alert_type}: {product_name} Sentiment {trend.title()}"

        # HTML body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .sentiment-box {{ background-color: #f8f9fa; border-left: 4px solid {color};
                                  padding: 15px; margin: 20px 0; }}
                .metric {{ font-size: 32px; font-weight: bold; color: {color}; }}
                .change {{ font-size: 20px; color: {color}; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center;
                           margin-top: 20px; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{emoji} Sentiment {alert_type}!</h1>
                <p>{product_name}</p>
            </div>

            <div class="content">
                <h2>Customer Sentiment is {trend.title()}</h2>
                <p>The sentiment for <strong>{product_name}</strong> on <strong>{platform}</strong> has changed significantly.</p>

                <div class="sentiment-box">
                    <p>Positive Sentiment:</p>
                    <p class="metric">{old_sentiment_pct:.1f}% → {new_sentiment_pct:.1f}%</p>
                    <p class="change">Change: {sentiment_change:+.1f}%</p>
                </div>

                <h3>What does this mean?</h3>
                <ul>
                    {'<li>Product quality is improving - customers are happier!</li>' if trend == "improving" else
                     '<li>Warning: More negative reviews detected</li>'}
                    {'<li>Good time to consider purchasing</li>' if trend == "improving" else
                     '<li>Consider waiting for product improvements</li>'}
                    <li>Based on real-time AI sentiment analysis of customer reviews</li>
                </ul>

                <p style="margin-top: 30px;">
                    <a href="http://localhost:8501" style="background-color: #007bff; color: white;
                       padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                       View Details
                    </a>
                </p>
            </div>

            <div class="footer">
                <p>This is an automated alert from E-Commerce Sentiment Tracker</p>
                <p>AI-Powered by Llama 3.3 70B | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """

        # Plain text version
        text_body = f"""
        SENTIMENT {alert_type.upper()}: {product_name}

        Platform: {platform}
        Positive Sentiment: {old_sentiment_pct:.1f}% -> {new_sentiment_pct:.1f}%
        Change: {sentiment_change:+.1f}%
        Trend: {trend.title()}

        {'Product quality improving - good time to buy!' if trend == "improving" else
         'Warning: Negative reviews increasing - consider alternatives'}

        View dashboard: http://localhost:8501

        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        return self.send_email(subject, html_body, text_body)

    def test_connection(self):
        """Test email configuration by sending a test email."""
        subject = "Test: E-Commerce Sentiment Tracker Notifications"
        html_body = """
        <html>
        <body>
            <h2>Test Email Successful!</h2>
            <p>Your email notification system is configured correctly.</p>
            <p>You will now receive alerts for:</p>
            <ul>
                <li>Price drops</li>
                <li>Sentiment changes</li>
            </ul>
        </body>
        </html>
        """
        text_body = "Test email from E-Commerce Sentiment Tracker. Configuration successful!"

        return self.send_email(subject, html_body, text_body)
