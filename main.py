import sys
import logging
from scrapers.chittorgarh import ChittorgarhScraper
from scrapers.ipowatch import IPOWatchScraper
from scrapers.investorgain import InvestorGainScraper
import matcher
import notifier
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing IPO GMP Scraper automation task...")
    
    # 1. Run all scrapers independently
    chittorgarh_data = []
    ipowatch_data = []
    investorgain_data = []

    # Scraper 1: Chittorgarh
    try:
        scraper = ChittorgarhScraper()
        chittorgarh_data = scraper.scrape()
        logger.info(f"Chittorgarh Scraper returned {len(chittorgarh_data)} entries.")
    except Exception as e:
        logger.error(f"Chittorgarh scraper failed: {e}")

    # Scraper 2: IPOWatch
    try:
        scraper = IPOWatchScraper()
        ipowatch_data = scraper.scrape()
        logger.info(f"IPOWatch Scraper returned {len(ipowatch_data)} entries.")
    except Exception as e:
        logger.error(f"IPOWatch scraper failed: {e}")

    # Scraper 3: InvestorGain
    try:
        scraper = InvestorGainScraper()
        investorgain_data = scraper.scrape()
        logger.info(f"InvestorGain Scraper returned {len(investorgain_data)} entries.")
    except Exception as e:
        logger.error(f"InvestorGain scraper failed: {e}")

    # 2. Consolidate and calculate consensus math
    consolidated_ipos = matcher.consolidate_data(chittorgarh_data, ipowatch_data, investorgain_data)
    logger.info(f"Consolidated and matched {len(consolidated_ipos)} unique upcoming IPOs across all active sources.")

    # 3. Process and filter against threshold
    alerts_triggered = 0
    for ipo in consolidated_ipos:
        name = ipo['company']
        gain = ipo['listing_gain_pct']
        gmp = ipo['consensus_gmp']
        price = ipo['cutoff_price']
        
        logger.info(f"IPO: {name} | Consensus GMP: INR {gmp} | Cutoff: INR {price} | Est Gain: {gain}%")

        if gain >= config.THRESHOLD_GAIN_PCT:
            logger.info(f"-> THRESHOLD BREACHED: {gain}% >= {config.THRESHOLD_GAIN_PCT}%!")
            
            # Send alert
            success = notifier.send_alert(
                company_name=name,
                listing_gain_pct=gain,
                consensus_gmp=gmp,
                cutoff_price=price
            )
            if success:
                alerts_triggered += 1
        else:
            logger.info(f"-> Threshold not met: {gain}% < {config.THRESHOLD_GAIN_PCT}%")

    if alerts_triggered > 0:
        logger.info(f"Task completed successfully. {alerts_triggered} alert(s) sent.")
    else:
        # Exit completely silently in terms of communications
        logger.info("No IPOs met the notification threshold. Exiting silently.")

if __name__ == '__main__':
    main()
