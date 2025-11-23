# 🚀 Quick Setup Guide

This guide will help you set up the E-commerce Competitor Sentiment Tracker in 10 minutes.

## Step 1: Check Prerequisites

Before starting, ensure you have:

- ✅ Python 3.8 or higher installed
  ```bash
  python --version
  ```

- ✅ Google Chrome installed (for web scraping)

- ✅ Git installed (for cloning the repository)

## Step 2: Clone and Navigate

```bash
# Clone the repository
git clone https://github.com/vvdvasan/infosys-competitor-tracker.git

# Navigate to project directory
cd infosys-competitor-tracker
```

## Step 3: Set Up Virtual Environment

### Windows:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

### macOS/Linux:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

## Step 4: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

This will install:
- Streamlit (dashboard)
- Groq (AI API)
- Selenium (web scraping)
- BeautifulSoup4 (HTML parsing)
- Pandas (data analysis)
- Plotly (visualizations)
- And more...

## Step 5: Get Your Groq API Key

### 5.1 Create Groq Account

1. Visit: [https://console.groq.com](https://console.groq.com)
2. Click **"Sign Up"**
3. Use your Google/GitHub account or email
4. Verify your email

### 5.2 Generate API Key

1. Go to **API Keys** section in the dashboard
2. Click **"Create API Key"**
3. Give it a name (e.g., "Sentiment Analysis")
4. Click **"Create"**
5. **IMPORTANT**: Copy the key immediately (you won't see it again!)

### 5.3 Note About Free Tier

The Groq free tier includes:
- ✅ 30 requests per minute
- ✅ 6,000 tokens per minute
- ✅ Access to Llama 3 models
- ✅ No credit card required

## Step 6: Configure Environment

```bash
# Create .env file from template
copy .env.example .env     # Windows
# or
cp .env.example .env       # macOS/Linux
```

Open `.env` in any text editor and update:

```env
# Replace 'your_groq_api_key_here' with your actual API key
GROQ_API_KEY=gsk_abc123xyz...

# Keep other settings as default
GROQ_RPM=30
GROQ_TPM=6000
SCRAPER_DELAY_MIN=2
SCRAPER_DELAY_MAX=5
USER_AGENT_ROTATION=true
DASHBOARD_PORT=8501
```

## Step 7: Test the Installation

### 7.1 Test Python Import

```bash
python -c "from sentiment_analysis.config import Config; print('✅ Setup successful!')"
```

### 7.2 Test Groq API Connection

```bash
python -c "from sentiment_analysis.api.groq_client import GroqSentimentAnalyzer; analyzer = GroqSentimentAnalyzer(); print('✅ Groq API connected!')"
```

If you see ✅ messages, you're all set!

## Step 8: Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

Your browser should automatically open to:
```
http://localhost:8501
```

If not, manually navigate to that URL.

## Step 9: Try Your First Analysis

### In the Dashboard:

1. **Scrape a Product**:
   - Find any Amazon India product
   - Copy the URL (e.g., `https://www.amazon.in/dp/B0ABC123`)
   - Paste it in the sidebar input
   - Click **"Scrape Product"**

2. **Analyze Sentiment**:
   - Wait for scraping to complete
   - Click **"Analyze Pending Reviews"**
   - Watch the magic happen! 🎉

3. **Explore Results**:
   - Check the **Overview** tab for statistics
   - View **Sentiment Analysis** for trends
   - Browse **Reviews** with sentiment labels

### Or Use Command Line:

```bash
python run_pipeline.py --scrape "https://www.amazon.in/dp/YOUR_PRODUCT_ASIN" --max-pages 2
```

## Step 10: Verify Everything Works

Check that these files were created:

```bash
# Database should exist
ls data/database/sentiment_analysis.db

# Should see data in tables
python -c "from sentiment_analysis.database.db_manager import DatabaseManager; db = DatabaseManager(); print(db.get_sentiment_statistics())"
```

## 🎊 Congratulations!

You've successfully set up the sentiment analysis system!

## Common Setup Issues

### Issue 1: "Module not found" Error

**Solution**:
```bash
# Ensure you're in the virtual environment
# You should see (venv) in your prompt

# Reinstall requirements
pip install -r requirements.txt
```

### Issue 2: "GROQ_API_KEY not found"

**Solution**:
```bash
# Check if .env exists
ls .env

# Verify content
cat .env  # macOS/Linux
type .env # Windows

# Ensure no extra spaces around = sign
GROQ_API_KEY=your_key_here  # ✅ Correct
GROQ_API_KEY = your_key_here # ❌ Wrong
```

### Issue 3: ChromeDriver Issues

**Solution**:
```bash
# Update webdriver manager
pip install --upgrade webdriver-manager

# Run this test
python -c "from selenium import webdriver; from webdriver_manager.chrome import ChromeDriverManager; from selenium.webdriver.chrome.service import Service; service = Service(ChromeDriverManager().install()); print('✅ ChromeDriver ready!')"
```

### Issue 4: Port Already in Use

**Solution**:
```bash
# Change port in .env
DASHBOARD_PORT=8502

# Or run Streamlit on different port
streamlit run dashboard/app.py --server.port 8502
```

### Issue 5: Slow Scraping

**Expected Behavior**:
- Scraping is intentionally slow to be respectful to Amazon
- Each page has 2-5 seconds delay
- This is normal and recommended

## Next Steps

1. **Read the Full Documentation**: Check [README.md](README.md)
2. **Explore Features**: Try different products and compare
3. **Customize**: Modify settings in `.env`
4. **Contribute**: Add new features or scrapers

## Getting Help

If you encounter issues:

1. **Check Logs**: Look at terminal output for errors
2. **GitHub Issues**: Search existing issues or create new one
3. **Documentation**: Read README.md for detailed info

## Quick Reference Commands

```bash
# Activate virtual environment
venv\Scripts\activate           # Windows
source venv/bin/activate        # macOS/Linux

# Run dashboard
streamlit run dashboard/app.py

# Run pipeline
python run_pipeline.py --scrape "URL"

# Analyze pending
python run_pipeline.py --analyze-pending

# Deactivate virtual environment
deactivate
```

---

Happy analyzing! 🚀📊
