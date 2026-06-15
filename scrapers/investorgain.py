import json
from bs4 import BeautifulSoup
from datetime import datetime
from scrapers.base import BaseScraper
import logging

logger = logging.getLogger(__name__)

class InvestorGainScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            name="InvestorGain",
            url="https://www.investorgain.com/report/ipo-gmp-live/331/"
        )

    def scrape(self):
        """
        Scrapes the InvestorGain IPO GMP dashboard by querying the backend JSON API.
        Returns a list of dicts: [{'company': str, 'gmp': float, 'price': float, 'close_date': str}]
        """
        now = datetime.utcnow()
        # Query the new backend API endpoint dynamically with the current month and year
        api_url = f"https://webnodejs.investorgain.com/cloud/v2/report/data-read/331/1/{now.month}/{now.year}/0/0/all"
        self.url = api_url

        html = self.fetch_html()
        if not html:
            logger.warning("No data returned for InvestorGain GMP scraper API.")
            return []

        try:
            data = json.loads(html)
        except Exception as e:
            logger.error(f"Failed to parse JSON response from InvestorGain API: {e}")
            return []

        report_data = data.get('reportTableData', [])
        if not report_data:
            logger.warning("InvestorGain API returned empty reportTableData.")
            return []

        ipos = []
        for item in report_data:
            raw_name = item.get('Name', '')
            if not raw_name:
                continue

            # Extract company name from the link inside the Name HTML snippet
            soup = BeautifulSoup(raw_name, 'html.parser')
            a_tag = soup.find('a')
            company_name = a_tag.text.strip() if a_tag else soup.text.strip()

            raw_gmp = item.get('GMP', '')
            raw_price = item.get('Price (₹)', '')
            raw_close = item.get('Close', '')

            # Parse Close Date (using first text child before any HTML breaks)
            close_soup = BeautifulSoup(raw_close, 'html.parser')
            close_date = next(close_soup.stripped_strings, 'N/A')

            # Parse GMP value
            gmp_soup = BeautifulSoup(raw_gmp, 'html.parser')
            gmp_text = next(gmp_soup.stripped_strings, '')
            gmp_val = self.clean_number(gmp_text)

            # Parse Price value
            price_val = self.clean_price_band(raw_price)

            if company_name:
                ipos.append({
                    'company': company_name,
                    'gmp': gmp_val,
                    'price': price_val,
                    'close_date': close_date
                })

        logger.info(f"Successfully scraped {len(ipos)} IPO entries from InvestorGain API.")
        return ipos
