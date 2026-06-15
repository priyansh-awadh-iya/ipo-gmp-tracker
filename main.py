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

def generate_report(scraper_statuses, ipo_results, overall_status, error_message=None):
    """
    Generates a Markdown report summarizing the run.
    Writes to report.md and to GITHUB_STEP_SUMMARY if available.
    """
    import os
    from datetime import datetime
    
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    markdown = []
    markdown.append(f"# IPO GMP Scraper Run Report")
    markdown.append(f"**Run Date/Time:** {timestamp}")
    markdown.append(f"**Overall Status:** {overall_status}\n")
    
    if error_message:
        markdown.append(f"### ⚠️ Error Details\n```\n{error_message}\n```\n")
        
    markdown.append("## 🔍 Scraper Statuses")
    markdown.append("| Scraper Source | Status | Items Extracted | Error/Notes |")
    markdown.append("| :--- | :--- | :--- | :--- |")
    for scraper_name, status in scraper_statuses.items():
        status_icon = "✅ Success" if status['success'] else "❌ Failed"
        count = status['count']
        err = status.get('error', '-')
        markdown.append(f"| {scraper_name} | {status_icon} | {count} | {err} |")
    markdown.append("")
    
    markdown.append("## 📊 Consolidated IPO Analysis")
    markdown.append(f"**Notification Threshold:** `{config.THRESHOLD_GAIN_PCT}%` expected listing gain\n")
    markdown.append("| Company | Consensus GMP (INR) | Cut-off Price (INR) | Expected Listing Gain (%) | Status | Alert Action |")
    markdown.append("| :--- | :---: | :---: | :---: | :---: | :--- |")
    
    if not ipo_results:
        markdown.append("| - | - | - | - | - | No IPOs found or processed. |")
    else:
        for ipo in ipo_results:
            name = ipo['company']
            gmp = ipo['consensus_gmp']
            price = ipo['cutoff_price']
            gain = ipo['listing_gain_pct']
            
            # Status icon based on threshold
            if gain >= config.THRESHOLD_GAIN_PCT:
                status_str = "✅ Met Threshold"
            else:
                status_str = "❌ Below Threshold"
                
            alert_action = ipo.get('alert_action', 'N/A')
            
            markdown.append(f"| {name} | {gmp} | {price} | {gain}% | {status_str} | {alert_action} |")
        
    markdown.append("\n---\n*Report generated automatically by IPO GMP Scraper workflow.*")
    
    report_content = "\n".join(markdown)
    
    # Write to local file
    try:
        with open("report.md", "w", encoding="utf-8") as f:
            f.write(report_content)
        logger.info("Local report.md written successfully.")
    except Exception as e:
        logger.error(f"Failed to write local report.md: {e}")
        
    # Write to GITHUB_STEP_SUMMARY
    summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_file:
        try:
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write(report_content + "\n")
            logger.info("Written to GITHUB_STEP_SUMMARY.")
        except Exception as e:
            logger.error(f"Failed to write to GITHUB_STEP_SUMMARY: {e}")

def main():
    logger.info("Initializing IPO GMP Scraper automation task...")
    
    scraper_statuses = {
        'Chittorgarh': {'success': False, 'count': 0, 'error': 'Not started'},
        'IPOWatch': {'success': False, 'count': 0, 'error': 'Not started'},
        'InvestorGain': {'success': False, 'count': 0, 'error': 'Not started'}
    }

    # 1. Fail-fast configuration validation at startup (before logging details or scraping)
    missing_vars = config.validate_config()
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.critical(f"Startup failed: {error_msg}")
        logger.critical("Please set these variables in your environment or a local .env file.")
        
        # Mark all scrapers as failed/skipped
        for s in scraper_statuses:
            scraper_statuses[s] = {'success': False, 'count': 0, 'error': 'Configuration Error'}
        generate_report(scraper_statuses, [], "FAILED (Config Error)", error_msg)
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
        scraper_statuses['Chittorgarh'] = {'success': True, 'count': len(chittorgarh_data), 'error': '-'}
    except Exception as e:
        logger.error(f"Chittorgarh scraper failed: {e}")
        scraper_statuses['Chittorgarh'] = {'success': False, 'count': 0, 'error': str(e)}

    # Scraper 2: IPOWatch
    try:
        scraper = IPOWatchScraper()
        ipowatch_data = scraper.scrape()
        logger.info(f"IPOWatch Scraper returned {len(ipowatch_data)} entries.")
        scraper_statuses['IPOWatch'] = {'success': True, 'count': len(ipowatch_data), 'error': '-'}
    except Exception as e:
        logger.error(f"IPOWatch scraper failed: {e}")
        scraper_statuses['IPOWatch'] = {'success': False, 'count': 0, 'error': str(e)}

    # Scraper 3: InvestorGain
    try:
        scraper = InvestorGainScraper()
        investorgain_data = scraper.scrape()
        logger.info(f"InvestorGain Scraper returned {len(investorgain_data)} entries.")
        scraper_statuses['InvestorGain'] = {'success': True, 'count': len(investorgain_data), 'error': '-'}
    except Exception as e:
        logger.error(f"InvestorGain scraper failed: {e}")
        scraper_statuses['InvestorGain'] = {'success': False, 'count': 0, 'error': str(e)}

    # 3. Fail Loudly: Check if ALL scrapers failed to find data (suspect layout shift/IP block)
    if len(chittorgarh_data) == 0 and len(ipowatch_data) == 0 and len(investorgain_data) == 0:
        logger.critical("SYSTEM FAILURE: All scrapers returned 0 results. Layout changes or IP blocks suspected.")
        success = notifier.send_alert(
            company_name="[CRITICAL] All Scrapers Failed",
            listing_gain_pct=0.0,
            consensus_gmp=0.0,
            cutoff_price=0.0,
            close_date="N/A"
        )
        alert_action = "Sent Critical Alert" if success else "Failed to Send Critical Alert"
        
        ipo_results = [{
            'company': '[CRITICAL] All Scrapers Failed',
            'consensus_gmp': 0.0,
            'cutoff_price': 0.0,
            'listing_gain_pct': 0.0,
            'alert_action': alert_action
        }]
        
        generate_report(
            scraper_statuses,
            ipo_results,
            "FAILED (Extraction Error)",
            "All scrapers returned 0 results. Layout changes or IP blocks suspected."
        )
        sys.exit(1)

    # 4. Consolidate and calculate consensus math
    consolidated_ipos = matcher.consolidate_data(chittorgarh_data, ipowatch_data, investorgain_data)
    logger.info(f"Consolidated and matched {len(consolidated_ipos)} unique upcoming IPOs across all active sources.")

    # 5. Process and filter against threshold with billing rate-limiting
    alerts_triggered = 0
    max_alerts_per_run = 3  # Protect wallet against runaway API alerts
    ipo_results = []
    
    for ipo in consolidated_ipos:
        name = ipo['company']
        gain = ipo['listing_gain_pct']
        gmp = ipo['consensus_gmp']
        price = ipo['cutoff_price']
        close_date = ipo.get('close_date', 'N/A')
        
        logger.info(f"IPO: {name} | Consensus GMP: INR {gmp} | Cutoff: INR {price} | Est Gain: {gain}% | Close: {close_date}")

        alert_action = "Skipped"
        if gain >= config.THRESHOLD_GAIN_PCT:
            logger.info(f"-> THRESHOLD BREACHED: {gain}% >= {config.THRESHOLD_GAIN_PCT}%!")
            
            # Enforce Twilio send limit
            if alerts_triggered >= max_alerts_per_run:
                logger.warning(f"Wallet safeguard: Max alerts limit ({max_alerts_per_run}) reached. Skipping notification for {name}.")
                alert_action = "Skipped (Wallet Safeguard)"
            else:
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
                    alert_action = "Sent Successfully"
                else:
                    alert_action = "Failed to Send"
        else:
            logger.info(f"-> Threshold not met: {gain}% < {config.THRESHOLD_GAIN_PCT}%")
            alert_action = "Skipped (Below Threshold)"

        ipo_results.append({
            'company': name,
            'consensus_gmp': gmp,
            'cutoff_price': price,
            'listing_gain_pct': gain,
            'alert_action': alert_action
        })

    # Generate the successful run report
    if alerts_triggered > 0:
        overall_status_msg = f"SUCCESS ({alerts_triggered} alert(s) sent)"
        logger.info(f"Task completed successfully. {alerts_triggered} alert(s) sent.")
    else:
        overall_status_msg = "SUCCESS (No alerts triggered)"
        logger.info("No IPOs met the notification threshold. Exiting silently.")
        
    generate_report(scraper_statuses, ipo_results, overall_status_msg)

if __name__ == '__main__':
    main()
