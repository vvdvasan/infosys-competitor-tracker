"""Configuration module for sentiment analysis system."""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the sentiment analysis system."""

    # Project paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    DATABASE_DIR = DATA_DIR / "database"

    # Create directories if they don't exist
    for dir_path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, DATABASE_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Groq API Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    # Available FREE models on Groq:
    # - llama-3.3-70b-versatile (Latest, most powerful! 128k context)
    # - mixtral-8x7b-32768 (Very accurate for sentiment)
    # - llama-3.1-8b-instant (Fast, good quality)
    GROQ_MODEL = "llama-3.3-70b-versatile"  # Using latest & most powerful!
    GROQ_RPM = int(os.getenv("GROQ_RPM", 30))
    GROQ_TPM = int(os.getenv("GROQ_TPM", 6000))

    # Database Configuration
    DATABASE_PATH = DATABASE_DIR / "sentiment_analysis.db"
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

    # Scraper Configuration
    SCRAPER_DELAY_MIN = int(os.getenv("SCRAPER_DELAY_MIN", 2))
    SCRAPER_DELAY_MAX = int(os.getenv("SCRAPER_DELAY_MAX", 5))
    USER_AGENT_ROTATION = os.getenv("USER_AGENT_ROTATION", "true").lower() == "true"

    # Amazon Login Configuration (Optional)
    AMAZON_EMAIL = os.getenv("AMAZON_EMAIL")
    AMAZON_PASSWORD = os.getenv("AMAZON_PASSWORD")

    # Sentiment Analysis Settings
    SENTIMENT_LABELS = ["POSITIVE", "NEGATIVE", "NEUTRAL"]
    MAX_REVIEW_LENGTH = 1000  # Characters
    BATCH_SIZE = 10  # Process reviews in batches

    # Dashboard Configuration
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 8501))
    DASHBOARD_REFRESH_INTERVAL = 60  # seconds
