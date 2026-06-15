# IPO GMP Tracker & Alerter

A clean, production-ready, and error-resilient Python web scraping tool designed to monitor Grey Market Premium (GMP) data for upcoming Mainboard and SME IPOs in India. It consolidates data from **Chittorgarh** (via InvestorGain), **IPOWatch**, and **InvestorGain**, computes a consensus average, and fires a Telegram alert to your phone only when a specific expected listing gain threshold is breached.

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
│   ├── chittorgarh.py       # Scraper for Chittorgarh (via InvestorGain API)
│   ├── ipowatch.py          # Scraper for IPOWatch
│   └── investorgain.py      # Scraper for InvestorGain (via backend API)
│
├── config.py                # Loads environment variables & threshold configuration
├── matcher.py               # Fuzzy name matching & consensus listing gain calculations
├── notifier.py              # Compiles and dispatches Telegram Bot messages
├── main.py                  # Entrypoint orchestrator
├── requirements.txt         # Package dependencies
└── .gitignore               # Excludes python cache & local virtual environments
```

---

## ✨ Features & Resilience

*   **API-First Aggregation**: InvestorGain and Chittorgarh scrapers connect directly to the site's private backend JSON APIs, bypassing client-side JavaScript rendering issues and ensuring fast, headless performance.
*   **Stricter Consensus Validation**: Consensus math and expected listing gains are calculated dynamically. Alerts are triggered **only if the IPO is successfully found and scraped on all three websites**, ensuring you never receive false alerts based on incomplete data.
*   **Rotating User-Agents**: Uses randomized, realistic browser footprints to prevent IP blocking.
*   **Fuzzy Token Matcher**: Standardizes and matches company names (e.g. "Horizon Reclaim Ltd" matches "Horizon Reclaim (India) IPO") across different sources.

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
Export the required Telegram credentials on your machine:

**Windows (PowerShell)**:
```powershell
$env:DELIVERY_METHOD="telegram"
$env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
$env:TELEGRAM_CHAT_ID="your_chat_id_here"
```

**macOS/Linux (Bash/Zsh)**:
```bash
export DELIVERY_METHOD="telegram"
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### 3. Run the Tool
Run the script manually:
```bash
python main.py
```

---

## 🤖 Telegram Bot Setup Guide

To set up a free, permanent bot channel that never expires:

1.  **Create the Telegram Bot**:
    *   Open Telegram, search for the official account **`@BotFather`**, and start a chat.
    *   Send the command `/newbot`.
    *   Follow the instructions to name your bot and choose a username.
    *   Copy the **API Token** provided (looks like `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). This is your `TELEGRAM_BOT_TOKEN`.

2.  **Get Your Chat ID**:
    *   Find your newly created bot on Telegram using its username, start a chat, and send a dummy message (e.g., `hi`).
    *   Search for **`@userinfobot`** on Telegram and start a chat. It will immediately reply with your personal **Id** (a number like `987654321`). This is your `TELEGRAM_CHAT_ID`.

3.  **Group Chat Setup (Optional - Alert Multiple People)**:
    *   To send alerts to both you and your brother (or any other users) simultaneously, create a Telegram Group chat.
    *   Add your Bot and your brother to the group.
    *   Send a message in the group, then check the group's ID (which always starts with a negative sign, e.g. `-100123456789`). Use this Group ID as your `TELEGRAM_CHAT_ID`.
    *   Alternatively, you can provide a comma-separated list of individual chat IDs in the environment: `TELEGRAM_CHAT_ID="987654321,123456789"`.

---

## 🔒 GitHub Actions Automation

To run the script automatically once a day (at **02:30 UTC / 8:00 AM IST**):

1.  Go to your GitHub repository > **Settings** > **Secrets and variables** > **Actions**.
2.  Click **New repository secret** and add the following:
    *   `DELIVERY_METHOD` = `telegram`
    *   `TELEGRAM_BOT_TOKEN` = `<Your Bot API Token>`
    *   `TELEGRAM_CHAT_ID` = `<Your Chat ID or comma-separated Chat IDs>`
3.  The workflow inside `.github/workflows/daily-scraper.yml` will automatically detect these secrets, pull the latest GMP data, calculate the consensus, and alert you on Telegram when threshold conditions are met.
