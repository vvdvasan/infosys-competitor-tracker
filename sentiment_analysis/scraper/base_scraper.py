"""Base scraper class with common functionality."""

import time
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from sentiment_analysis.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Abstract base class for e-commerce scrapers."""

    def __init__(self, use_selenium: bool = False, headless: bool = True):
        """
        Initialize base scraper.

        Args:
            use_selenium: Whether to use Selenium for JavaScript-rendered pages
            headless: Whether to run browser in headless mode (False shows browser window)
        """
        self.use_selenium = use_selenium
        self.headless = headless
        self.ua = UserAgent() if Config.USER_AGENT_ROTATION else None
        self.session = requests.Session()
        self.driver = None

        if use_selenium:
            self._setup_selenium()

    def _setup_selenium(self):
        """Set up Selenium WebDriver."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"user-agent={self._get_user_agent()}")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def _get_user_agent(self) -> str:
        """Get a random user agent or default."""
        if Config.USER_AGENT_ROTATION and self.ua:
            return self.ua.random
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    def _random_delay(self):
        """Add random delay between requests."""
        delay = random.uniform(Config.SCRAPER_DELAY_MIN, Config.SCRAPER_DELAY_MAX)
        time.sleep(delay)

    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a web page.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            if self.use_selenium:
                self.driver.get(url)
                time.sleep(3)  # Wait for JavaScript to load
                html = self.driver.page_source
                return BeautifulSoup(html, 'html.parser')
            else:
                headers = {'User-Agent': self._get_user_agent()}
                response = self.session.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    @abstractmethod
    def scrape_product(self, product_url: str) -> Dict:
        """Scrape product information from URL."""
        pass

    @abstractmethod
    def scrape_reviews(self, product_url: str, max_pages: int = 10) -> List[Dict]:
        """Scrape reviews for a product."""
        pass

    def close(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
        self.session.close()
