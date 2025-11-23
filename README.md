# 🛍️ E-commerce Competitor Sentiment Tracker

A production-ready sentiment analysis system for e-commerce products using Groq API and web scraping. Track competitor products, analyze customer sentiment, and gain actionable insights from Amazon reviews.

## ✨ Features

- **🔍 Web Scraping**: Automated scraping of Amazon India products and reviews
- **🧠 AI-Powered Sentiment Analysis**: Groq API integration with Llama 3 model
- **💾 Database Management**: SQLite database for storing products, reviews, and analysis results
- **📊 Interactive Dashboard**: Beautiful Streamlit dashboard with real-time visualizations
- **⚡ Rate Limiting**: Smart rate limiting to stay within API limits
- **📈 Analytics**: Comprehensive sentiment trends and product comparisons

## 🏗️ Project Structure

```
infosys-competitor-tracker/
├── sentiment_analysis/
│   ├── api/
│   │   ├── __init__.py
│   │   └── groq_client.py          # Groq API client with rate limiting
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── base_scraper.py         # Abstract base scraper
│   │   └── amazon_scraper.py       # Amazon India scraper
│   ├── database/
│   │   ├── __init__.py
│   │   └── db_manager.py           # Database operations
│   ├── utils/
│   │   ├── __init__.py
│   │   └── rate_limiter.py         # API rate limiter
│   └── config.py                   # Configuration management
├── dashboard/
│   └── app.py                      # Streamlit dashboard
├── data/
│   ├── raw/                        # Raw scraped data
│   ├── processed/                  # Processed data
│   └── database/                   # SQLite database
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── run_pipeline.py                 # Main pipeline script
└── README.md                       # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- Google Chrome (for Selenium web scraping)
- Groq API key (free tier available)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/vvdvasan/infosys-competitor-tracker.git
cd infosys-competitor-tracker

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Get Your Groq API Key

1. Visit [https://console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key

### 4. Configure Environment Variables

```bash
# Copy the example environment file
copy .env.example .env  # Windows
# or
cp .env.example .env    # macOS/Linux

# Edit .env and add your Groq API key
# GROQ_API_KEY=your_actual_api_key_here
```

### 5. Run the System

#### Option A: Use the Interactive Dashboard

```bash
streamlit run dashboard/app.py
```

Then open your browser to `http://localhost:8501`

#### Option B: Use the Command Line Pipeline

```bash
# Scrape and analyze a product
python run_pipeline.py --scrape "https://www.amazon.in/dp/PRODUCT_ASIN"

# Analyze pending reviews
python run_pipeline.py --analyze-pending --limit 50
```

## 📖 Usage Guide

### Using the Streamlit Dashboard

1. **Scrape Products**:
   - Enter an Amazon India product URL in the sidebar
   - Click "Scrape Product"
   - Wait for the scraping to complete

2. **Analyze Sentiment**:
   - Click "Analyze Pending Reviews"
   - Watch the progress bar
   - View results in real-time

3. **Explore Analytics**:
   - **Overview Tab**: View overall statistics and sentiment distribution
   - **Sentiment Analysis Tab**: See trends and product-wise breakdown
   - **Products Tab**: Compare product prices and ratings
   - **Reviews Tab**: Read individual reviews with sentiment labels

### Using the Command Line

```bash
# Scrape multiple products
python run_pipeline.py --scrape \
  "https://www.amazon.in/dp/PRODUCT1" \
  "https://www.amazon.in/dp/PRODUCT2" \
  --max-pages 5

# Analyze up to 100 pending reviews
python run_pipeline.py --analyze-pending --limit 100
```

## 🔧 Configuration

Edit `.env` file to customize:

```env
# API Configuration
GROQ_API_KEY=your_api_key_here
GROQ_RPM=30                    # Requests per minute
GROQ_TPM=6000                  # Tokens per minute

# Scraping Settings
SCRAPER_DELAY_MIN=2            # Min delay between requests (seconds)
SCRAPER_DELAY_MAX=5            # Max delay between requests (seconds)
USER_AGENT_ROTATION=true       # Rotate user agents

# Dashboard
DASHBOARD_PORT=8501            # Streamlit port
```

## 📊 Database Schema

### Products Table
- Product information (ASIN, name, brand, price, ratings)
- Stock status and seller information
- Timestamps for tracking

### Reviews Table
- Review text, title, and rating
- Reviewer information
- Verified purchase status
- Helpful votes count

### Sentiment Analysis Table
- Sentiment labels (POSITIVE, NEGATIVE, NEUTRAL)
- Confidence scores
- Response time and token usage
- Error tracking

## 🎯 API Rate Limits

The system automatically handles Groq API rate limits:

- **Free Tier**: 30 requests/minute, 6000 tokens/minute
- Intelligent rate limiting with automatic throttling
- Token usage tracking
- Queue management for batch processing

## 🛠️ Development

### Adding New Scrapers

Create a new scraper by extending `BaseScraper`:

```python
from sentiment_analysis.scraper.base_scraper import BaseScraper

class FlipkartScraper(BaseScraper):
    def scrape_product(self, product_url: str):
        # Implementation
        pass

    def scrape_reviews(self, product_url: str, max_pages: int = 10):
        # Implementation
        pass
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black sentiment_analysis/
flake8 sentiment_analysis/
```

## 🚨 Important Notes

### Legal and Ethical Considerations

- **Respect robots.txt**: The scraper includes delays to be respectful
- **Terms of Service**: Review Amazon's ToS before large-scale scraping
- **Rate Limiting**: Built-in delays prevent server overload
- **Personal Use**: Recommended for research and personal projects

### Best Practices

1. **Start Small**: Test with 1-2 products first
2. **Monitor API Usage**: Check the dashboard for API limits
3. **Backup Data**: Regularly backup your database
4. **Update Regularly**: Keep dependencies up to date

## 📈 Features Roadmap

- [ ] Support for Flipkart scraping
- [ ] Email alerts for sentiment changes
- [ ] Comparative analysis across competitors
- [ ] Export reports to PDF/Excel
- [ ] Advanced NLP features (aspect-based sentiment)
- [ ] Multi-language support

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is for educational purposes. Please respect:
- Amazon's Terms of Service
- Groq's API usage policies
- Data privacy regulations

## 🆘 Troubleshooting

### Common Issues

**1. ChromeDriver Issues**
```bash
# The system auto-downloads ChromeDriver, but if issues occur:
pip install --upgrade webdriver-manager
```

**2. API Key Errors**
```bash
# Verify your .env file:
cat .env  # macOS/Linux
type .env  # Windows

# Ensure GROQ_API_KEY is set correctly
```

**3. Database Locked**
```bash
# Close all connections and restart:
# Delete data/database/sentiment_analysis.db and restart
```

**4. Scraping Failures**
- Check internet connection
- Verify Amazon URL is valid
- Try with a different product
- Check if Amazon's structure changed

## 📧 Support

For issues and questions:
- GitHub Issues: [Report a bug](https://github.com/vvdvasan/infosys-competitor-tracker/issues)
- Email: Your contact email

## 🙏 Acknowledgments

- **Groq** for providing fast LLM inference
- **Streamlit** for the amazing dashboard framework
- **Selenium** for web scraping capabilities
- **Amazon** as a data source

---

**Built with ❤️ for Infosys Internship Project**

*Last Updated: November 2024*
