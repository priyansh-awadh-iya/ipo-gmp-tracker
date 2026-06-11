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
    
    # 1. Fail-fast configuration validation at startup (before logging details or scraping)
    missing_vars = config.validate_config()
    if missing_vars:
        logger.critical(f"Startup failed: Missing required environment variables: {', '.join(missing_vars)}")
        logger.critical("Please set these variables in your environment or a local .env file.")
        sys.exit(1)

    # 2. Run all scrapers independently
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

    # 3. Fail Loudly: Check if ALL scrapers failed to find data (suspect layout shift/IP block)
    if len(chittorgarh_data) == 0 and len(ipowatch_data) == 0 and len(investorgain_data) == 0:
        logger.critical("SYSTEM FAILURE: All scrapers returned 0 results. Layout changes or IP blocks suspected.")
        notifier.send_alert(
            company_name="[CRITICAL] All Scrapers Failed",
            listing_gain_pct=0.0,
            consensus_gmp=0.0,
            cutoff_price=0.0,
            close_date="N/A"
        )
        sys.exit(1)

    # 4. Consolidate and calculate consensus math
    consolidated_ipos = matcher.consolidate_data(chittorgarh_data, ipowatch_data, investorgain_data)
    logger.info(f"Consolidated and matched {len(consolidated_ipos)} unique upcoming IPOs across all active sources.")

    # 5. Process and filter against threshold with billing rate-limiting
    alerts_triggered = 0
    max_alerts_per_run = 3  # Protect wallet against runaway API alerts
    for ipo in consolidated_ipos:
        name = ipo['company']
        gain = ipo['listing_gain_pct']
        gmp = ipo['consensus_gmp']
        price = ipo['cutoff_price']
        close_date = ipo.get('close_date', 'N/A')
        
        logger.info(f"IPO: {name} | Consensus GMP: INR {gmp} | Cutoff: INR {price} | Est Gain: {gain}% | Close: {close_date}")

        if gain >= config.THRESHOLD_GAIN_PCT:
            logger.info(f"-> THRESHOLD BREACHED: {gain}% >= {config.THRESHOLD_GAIN_PCT}%!")
            
            # Enforce Twilio send limit
            if alerts_triggered >= max_alerts_per_run:
                logger.warning(f"Wallet safeguard: Max alerts limit ({max_alerts_per_run}) reached. Skipping notification for {name}.")
                continue

            # Send alert
            success = notifier.send_alert(
                company_name=name,
                listing_gain_pct=gain,
                consensus_gmp=gmp,
                cutoff_price=price,
                close_date=close_date
            )
            if success:
                alerts_triggered += 1
        else:
            logger.info(f"-> Threshold not met: {gain}% < {config.THRESHOLD_GAIN_PCT}%")

    if alerts_triggered > 0:
        logger.info(f"Task completed successfully. {alerts_triggered} alert(s) sent.")
    else:
        logger.info("No IPOs met the notification threshold. Exiting silently.")

if __name__ == '__main__':
    main()
