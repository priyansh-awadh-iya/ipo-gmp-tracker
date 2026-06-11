# IPO GMP Tracker & Alerter

A clean, production-ready, and error-resilient Python web scraping tool designed to monitor Grey Market Premium (GMP) data for upcoming Mainboard and SME IPOs in India. It consolidates data from **Chittorgarh** (via InvestorGain) and **IPOWatch**, computes a consensus average, and fires a Twilio alert (WhatsApp or SMS) to your phone only when a specific expected listing gain threshold is breached.

Designed to run headless as a daily cron job via GitHub Actions.

---

## 🛠️ Project Structure

```
ipo-gmp-scraper/
│
├── .github/workflows/
│   └── daily-scraper.yml   # GitHub Actions automated daily cron task
│
├── scrapers/
│   ├── __init__.py
│   ├── base.py              # Base scraper (rotates User-Agents, handles HTTP errors)
│   ├── chittorgarh.py       # Scraper for Chittorgarh (targets InvestorGain Mainboard)
│   ├── ipowatch.py          # Scraper for IPOWatch
│   └── investorgain.py      # Scraper for InvestorGain
│
├── config.py                # Loads environment variables & threshold configuration
├── matcher.py               # Fuzzy name matching & consensus listing gain calculations
├── notifier.py              # Compiles and dispatches Twilio SMS/WhatsApp messages
├── main.py                  # Entrypoint orchestrator
├── requirements.txt         # Package dependencies
└── .gitignore               # Excludes python cache & local virtual environments
```

---

## ✨ Features & Resilience

*   **Header Overlap Protection**: Dynamically matches table headers (Company Name, GMP, Price Band) on every execution, making the scrapers resistant to website layout shifts.
*   **Rotating User-Agents**: Uses randomized, realistic browser footprints to prevent IP blocking.
*   **Fail-Safe Architecture**: Individual source scrapers run inside isolated `try-except` blocks. If one aggregator is down or blocked, the program continues matching with the remaining sources.
*   **Fuzzy Token Matcher**: Standardizes and matches company names (e.g. "Horizon Reclaim Ltd" matches "Horizon Reclaim (India) IPO") across sources.

---

## 🚀 Setup & Local Execution

### 1. Clone & Initialize Environment
Clone your repository and navigate into the folder:
```bash
git clone https://github.com/priyansh-awadh-iya/ipo-gmp-tracker.git
cd ipo-gmp-tracker
```

Create and activate a Python virtual environment:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

Install the required packages:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create or export the required Twilio credentials on your machine:

**Windows (PowerShell)**:
```powershell
$env:TWILIO_ACCOUNT_SID="your_account_sid"
$env:TWILIO_AUTH_TOKEN="your_auth_token"
$env:MY_PHONE_NUMBER="+919876543210"        # Your verified recipient number
$env:TWILIO_FROM_NUMBER="+14155238886"       # Your Twilio sandbox number
$env:DELIVERY_METHOD="whatsapp"              # Toggle to 'sms' or 'whatsapp'
```

**macOS/Linux (Bash/Zsh)**:
```bash
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token"
export MY_PHONE_NUMBER="+919876543210"
export TWILIO_FROM_NUMBER="+14155238886"
export DELIVERY_METHOD="whatsapp"
```

### 3. Run the Tool
Run the script manually:
```bash
python main.py
```

---

## 📲 Twilio Sandbox Configuration

To use Twilio's free tier for alerts:

### For WhatsApp Alerts:
1. Go to the **Twilio Console** > **Messaging** > **Try it out** > **Send a WhatsApp message**.
2. Scan the QR code or send the text code (e.g., `join <sandbox-keyword>`) to the Twilio sandbox number (typically `+1 415 523 8886`) from your personal phone.
3. Add your personal number under **Verified Caller IDs** in the console.

### For SMS Alerts:
1. Simply verify your personal number under **Verified Caller IDs** in the Twilio Console.
2. Toggle `DELIVERY_METHOD="sms"` in your runner configurations.

---

## 🔒 GitHub Actions Automation

To run the script automatically once a day (at **02:30 UTC / 8:00 AM IST**):

1. Go to your GitHub repository > **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret** and add the following:
   *   `TWILIO_ACCOUNT_SID`
   *   `TWILIO_AUTH_TOKEN`
   *   `MY_PHONE_NUMBER`
   *   `TWILIO_FROM_NUMBER`
3. You can toggle the delivery method directly in the workflow environment variables inside `.github/workflows/daily-scraper.yml`.
