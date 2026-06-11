from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
import logging

logger = logging.getLogger(__name__)

class ChittorgarhScraper(BaseScraper):
    def __init__(self):
        # Chittorgarh redirects its internal GMP page to InvestorGain's Mainboard tracker
        super().__init__(
            name="Chittorgarh (via InvestorGain)",
            url="https://www.investorgain.com/report/live-ipo-gmp/331/ipo/"
        )

    def scrape(self):
        """
        Scrapes the Chittorgarh IPO GMP dashboard (hosted on InvestorGain).
        Returns a list of dicts: [{'company': str, 'gmp': float, 'price': float}]
        """
        html = self.fetch_html()
        if not html:
            logger.warning("No HTML returned for Chittorgarh GMP scraper.")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find(id="reportTable")
        if not table:
            logger.warning("Could not find table 'reportTable' on Chittorgarh GMP page.")
            return []

        rows = table.find_all('tr')
        if not rows:
            logger.info("Chittorgarh GMP table has no rows.")
            return []

        # Find headers dynamically
        headers = []
        thead = table.find('thead')
        if thead:
            headers = [th.text.strip().lower() for th in thead.find_all(['th', 'td'])]
        
        # If headers are empty in thead, check the first row of table
        if not headers:
            first_row = table.find('tr')
            if first_row:
                headers = [td.text.strip().lower() for td in first_row.find_all(['td', 'th'])]

        # Map column indexes dynamically based on headers
        company_idx = 0
        gmp_idx = 1
        price_idx = 2
        close_idx = 7 # Close date is typically column 7

        for idx, h in enumerate(headers):
            if ('ipo' in h or 'company' in h or 'name' in h) and 'gmp' not in h:
                company_idx = idx
            elif 'gmp' in h or 'premium' in h:
                gmp_idx = idx
            elif 'price' in h or 'band' in h or 'cutoff' in h or 'cut-off' in h:
                price_idx = idx
            elif 'close' in h or 'date' in h:
                close_idx = idx

        logger.info(f"Chittorgarh scraper mapped headers: Company index={company_idx}, GMP index={gmp_idx}, Price index={price_idx}, Close index={close_idx}")

        ipos = []
        tbody = table.find('tbody')
        data_rows = tbody.find_all('tr') if tbody else rows[1:]

        for row in data_rows:
            cells = row.find_all('td')
            if not cells or len(cells) <= max(company_idx, gmp_idx, price_idx):
                continue

            cell_texts = [c.text.strip() for c in cells]
            
            # Check for placeholder rows
            if any("no data available" in text.lower() for text in cell_texts):
                logger.info("Chittorgarh GMP table contains 'No data available'.")
                continue

            company_name = cell_texts[company_idx]
            raw_gmp = cell_texts[gmp_idx]
            raw_price = cell_texts[price_idx]
            close_date = cell_texts[close_idx] if close_idx < len(cell_texts) else 'N/A'

            gmp_val = self.clean_number(raw_gmp)
            price_val = self.clean_price_band(raw_price)

            if company_name:
                ipos.append({
                    'company': company_name,
                    'gmp': gmp_val,
                    'price': price_val,
                    'close_date': close_date
                })

        logger.info(f"Successfully scraped {len(ipos)} IPO entries from Chittorgarh.")
        return ipos
