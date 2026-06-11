from bs4 import BeautifulSoup
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
        Scrapes the InvestorGain IPO GMP dashboard.
        Returns a list of dicts: [{'company': str, 'gmp': float, 'price': float}]
        """
        html = self.fetch_html()
        if not html:
            logger.warning("No HTML returned for InvestorGain GMP scraper.")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find(id="reportTable")
        if not table:
            logger.warning("Could not find table 'reportTable' on InvestorGain GMP page.")
            return []

        rows = table.find_all('tr')
        if not rows:
            logger.warning("InvestorGain table has no rows.")
            return []

        # Find headers dynamically
        headers = []
        thead = table.find('thead')
        if thead:
            headers = [th.text.strip().lower() for th in thead.find_all(['th', 'td'])]
        
        # If no thead headers found, use first row
        if not headers:
            first_row = table.find('tr')
            if first_row:
                headers = [td.text.strip().lower() for td in first_row.find_all(['td', 'th'])]

        # Map column indexes dynamically based on headers
        company_idx = 0
        gmp_idx = 1
        price_idx = 2

        for idx, h in enumerate(headers):
            if ('ipo' in h or 'company' in h or 'name' in h) and 'gmp' not in h:
                company_idx = idx
            elif 'gmp' in h or 'premium' in h:
                gmp_idx = idx
            elif 'price' in h or 'band' in h or 'cutoff' in h or 'cut-off' in h:
                price_idx = idx

        logger.info(f"InvestorGain scraper mapped headers: Company index={company_idx}, GMP index={gmp_idx}, Price index={price_idx}")

        ipos = []
        tbody = table.find('tbody')
        data_rows = tbody.find_all('tr') if tbody else rows[1:]

        for row in data_rows:
            cells = row.find_all('td')
            if not cells or len(cells) <= max(company_idx, gmp_idx, price_idx):
                continue

            cell_texts = [c.text.strip() for c in cells]
            
            # Check for placeholders
            if any("no data available" in text.lower() for text in cell_texts):
                logger.info("InvestorGain GMP table contains 'No data available'.")
                continue

            company_name = cell_texts[company_idx]
            raw_gmp = cell_texts[gmp_idx]
            raw_price = cell_texts[price_idx]

            gmp_val = self.clean_number(raw_gmp)
            price_val = self.clean_price_band(raw_price)

            if company_name:
                ipos.append({
                    'company': company_name,
                    'gmp': gmp_val,
                    'price': price_val
                })

        logger.info(f"Successfully scraped {len(ipos)} IPO entries from InvestorGain.")
        return ipos
