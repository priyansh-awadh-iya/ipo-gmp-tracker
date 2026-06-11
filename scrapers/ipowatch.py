from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
import logging

logger = logging.getLogger(__name__)

class IPOWatchScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            name="IPOWatch",
            url="https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"
        )

    def scrape(self):
        """
        Scrapes the IPOWatch GMP table.
        Returns a list of dicts: [{'company': str, 'gmp': float, 'price': float}]
        """
        html = self.fetch_html()
        if not html:
            logger.warning("No HTML returned for IPOWatch GMP scraper.")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        
        # IPOWatch displays upcoming/live IPOs in the first table
        tables = soup.find_all('table')
        if not tables:
            logger.warning("No tables found on IPOWatch GMP page.")
            return []

        # We target the first table (Table 0) for active/upcoming IPOs
        table = tables[0]
        rows = table.find_all('tr')
        if not rows:
            logger.warning("IPOWatch table has no rows.")
            return []

        # Find headers dynamically
        headers = []
        thead = table.find('thead')
        if thead:
            headers = [th.text.strip().lower() for th in thead.find_all(['th', 'td'])]
        
        # If no thead, use first row
        if not headers:
            headers = [td.text.strip().lower() for td in rows[0].find_all(['td', 'th'])]

        # Map column indexes dynamically based on headers
        company_idx = 0
        gmp_idx = 1
        price_idx = 3  # Price Band is typically column 3
        date_idx = 5   # Date is typically column 5

        for idx, h in enumerate(headers):
            if ('ipo name' in h or 'company' in h or 'name' in h or h == 'ipo') and 'gmp' not in h:
                company_idx = idx
            elif 'gmp' in h or 'premium' in h:
                gmp_idx = idx
            elif 'price' in h or 'band' in h or 'cutoff' in h or 'cut-off' in h:
                price_idx = idx
            elif ('date' in h or 'close' in h) and 'update' not in h:
                date_idx = idx

        logger.info(f"IPOWatch scraper mapped headers: Company index={company_idx}, GMP index={gmp_idx}, Price index={price_idx}, Date index={date_idx}")

        ipos = []
        # Skip the header row
        data_rows = rows[1:]

        for row in data_rows:
            cells = row.find_all('td')
            if not cells or len(cells) <= max(company_idx, gmp_idx, price_idx):
                continue

            cell_texts = [c.text.strip() for c in cells]
            
            # Check for header duplication or placeholders
            if any("ipo name" in text.lower() for text in cell_texts) or any("no data available" in text.lower() for text in cell_texts):
                continue

            company_name = cell_texts[company_idx]
            raw_gmp = cell_texts[gmp_idx]
            raw_price = cell_texts[price_idx]
            close_date = cell_texts[date_idx] if date_idx < len(cell_texts) else 'N/A'

            gmp_val = self.clean_number(raw_gmp)
            price_val = self.clean_price_band(raw_price)

            if company_name:
                ipos.append({
                    'company': company_name,
                    'gmp': gmp_val,
                    'price': price_val,
                    'close_date': close_date
                })

        logger.info(f"Successfully scraped {len(ipos)} IPO entries from IPOWatch.")
        return ipos
