import random
import re
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Mobile User Agent: Chrome on Android
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
]

class BaseScraper:
    def __init__(self, name, url):
        self.name = name
        self.url = url

    def fetch_html(self):
        """
        Fetches the HTML source with custom user agents and a 10-second timeout.
        Returns the response text or None if failed.
        """
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive'
        }
        try:
            logger.info(f"Fetching {self.name} GMP from: {self.url}")
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from {self.name} ({self.url}): {e}")
            return None

    def clean_number(self, text):
        """
        Cleans currency text: removes ₹, commas, spaces, percentages, and parses to float.
        Returns float, or 0.0 if parsing fails.
        """
        if not text:
            return 0.0
        
        # Strip whitespace
        text = text.strip()
        
        # Handle typical placeholder values
        if text in ['-', '--', 'N/A', 'na', 'null', '0', '']:
            return 0.0
            
        try:
            # Remove currency symbols (₹, Rs, Rs., INR), commas, and spaces
            cleaned = re.sub(r'[₹$€£\s,]', '', text)
            
            # If there's a range like "100-120", take the upper band (highest value)
            if '-' in cleaned:
                parts = cleaned.split('-')
                cleaned = parts[-1]  # Get upper bound
            
            # Extract the first float-like substring
            match = re.search(r'[-+]?\d*\.\d+|\d+', cleaned)
            if match:
                return float(match.group())
            return 0.0
        except Exception as e:
            logger.warning(f"Failed to clean number '{text}' on {self.name}: {e}")
            return 0.0

    def clean_price_band(self, text):
        """
        Specifically extracts the upper cutoff price from price band text (e.g. "120 to 125", "125", "120-125").
        Returns float.
        """
        if not text:
            return 0.0
        
        text = text.strip().lower()
        if text in ['-', '--', 'n/a', 'na', 'null', '']:
            return 0.0
            
        try:
            # Replace common range words with hyphen for standard parsing
            text = text.replace(' to ', '-').replace(' - ', '-')
            
            # Clean symbols except dot and hyphen
            cleaned = re.sub(r'[₹$€£\s,]', '', text)
            
            if '-' in cleaned:
                parts = cleaned.split('-')
                # Try parsing the second element as upper band, otherwise first
                upper = self.clean_number(parts[-1])
                if upper > 0:
                    return upper
                return self.clean_number(parts[0])
            
            return self.clean_number(cleaned)
        except Exception as e:
            logger.warning(f"Failed to extract cutoff price from '{text}' on {self.name}: {e}")
            return 0.0

    def scrape(self):
        """
        To be implemented by child scrapers.
        Returns a list of dicts: [{'company': str, 'gmp': float, 'price': float}]
        """
        raise NotImplementedError("Scrapers must implement the scrape method.")
