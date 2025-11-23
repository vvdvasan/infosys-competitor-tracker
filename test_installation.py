"""Test script to verify installation and setup."""

import sys
import os

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")

    try:
        import streamlit
        print("✅ Streamlit installed")
    except ImportError:
        print("❌ Streamlit not installed")
        return False

    try:
        import groq
        print("✅ Groq installed")
    except ImportError:
        print("❌ Groq not installed")
        return False

    try:
        import selenium
        print("✅ Selenium installed")
    except ImportError:
        print("❌ Selenium not installed")
        return False

    try:
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup4 installed")
    except ImportError:
        print("❌ BeautifulSoup4 not installed")
        return False

    try:
        import pandas
        print("✅ Pandas installed")
    except ImportError:
        print("❌ Pandas not installed")
        return False

    try:
        import plotly
        print("✅ Plotly installed")
    except ImportError:
        print("❌ Plotly not installed")
        return False

    return True

def test_project_structure():
    """Test if project structure is correct."""
    print("\nTesting project structure...")

    required_files = [
        'sentiment_analysis/config.py',
        'sentiment_analysis/api/groq_client.py',
        'sentiment_analysis/scraper/base_scraper.py',
        'sentiment_analysis/scraper/amazon_scraper.py',
        'sentiment_analysis/database/db_manager.py',
        'sentiment_analysis/utils/rate_limiter.py',
        'dashboard/app.py',
        'run_pipeline.py',
        'requirements.txt',
        '.env.example',
        'README.md',
    ]

    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} not found")
            all_exist = False

    return all_exist

def test_env_configuration():
    """Test environment configuration."""
    print("\nTesting environment configuration...")

    if not os.path.exists('.env'):
        print("⚠️  .env file not found. Please create it from .env.example")
        return False

    print("✅ .env file exists")

    try:
        from dotenv import load_dotenv
        load_dotenv()

        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key and groq_key != 'your_groq_api_key_here':
            print("✅ GROQ_API_KEY is configured")
            return True
        else:
            print("⚠️  GROQ_API_KEY not configured in .env")
            return False
    except Exception as e:
        print(f"❌ Error loading environment: {str(e)}")
        return False

def test_module_imports():
    """Test if custom modules can be imported."""
    print("\nTesting custom modules...")

    try:
        from sentiment_analysis.config import Config
        print("✅ Config module imported")
    except Exception as e:
        print(f"❌ Config import failed: {str(e)}")
        return False

    try:
        from sentiment_analysis.database.db_manager import DatabaseManager
        print("✅ DatabaseManager module imported")
    except Exception as e:
        print(f"❌ DatabaseManager import failed: {str(e)}")
        return False

    try:
        from sentiment_analysis.utils.rate_limiter import RateLimiter
        print("✅ RateLimiter module imported")
    except Exception as e:
        print(f"❌ RateLimiter import failed: {str(e)}")
        return False

    try:
        from sentiment_analysis.api.groq_client import GroqSentimentAnalyzer
        print("✅ GroqSentimentAnalyzer module imported")
    except Exception as e:
        print(f"❌ GroqSentimentAnalyzer import failed: {str(e)}")
        return False

    try:
        from sentiment_analysis.scraper.amazon_scraper import AmazonScraper
        print("✅ AmazonScraper module imported")
    except Exception as e:
        print(f"❌ AmazonScraper import failed: {str(e)}")
        return False

    return True

def test_database():
    """Test database initialization."""
    print("\nTesting database...")

    try:
        from sentiment_analysis.database.db_manager import DatabaseManager

        db = DatabaseManager()
        print("✅ Database initialized")

        stats = db.get_sentiment_statistics()
        print("✅ Database queries working")

        return True
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("INSTALLATION VERIFICATION TEST")
    print("="*60)

    results = []

    # Run tests
    results.append(("Package Installation", test_imports()))
    results.append(("Project Structure", test_project_structure()))
    results.append(("Environment Configuration", test_env_configuration()))
    results.append(("Module Imports", test_module_imports()))
    results.append(("Database Setup", test_database()))

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n🎉 All tests passed! Your installation is ready.")
        print("\nNext steps:")
        print("1. Make sure you've added your Groq API key to .env")
        print("2. Run: streamlit run dashboard/app.py")
        print("3. Or run: python run_pipeline.py --help")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\nCommon fixes:")
        print("1. Run: pip install -r requirements.txt")
        print("2. Create .env from .env.example")
        print("3. Add your Groq API key to .env")

    print()

if __name__ == "__main__":
    main()
