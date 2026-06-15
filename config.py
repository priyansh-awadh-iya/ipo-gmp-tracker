import os
from dotenv import load_dotenv

# Load local .env file if present
load_dotenv()

# Threshold expected listing gain percentage to trigger notifications
THRESHOLD_GAIN_PCT = 15.0

# Delivery method: 'whatsapp', 'sms', or 'telegram'
DELIVERY_METHOD = (os.environ.get('DELIVERY_METHOD') or 'whatsapp').lower()

# Twilio API credentials and phone configurations
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
# Can contain a single number or multiple comma-separated numbers (e.g., +919999999999,+918888888888)
MY_PHONE_NUMBER = os.environ.get('MY_PHONE_NUMBER')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')

# Telegram Credentials
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
# Can contain a single chat ID or multiple comma-separated IDs (e.g., 12345678,98765432)
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def validate_config():
    """
    Validates that necessary config values are provided based on DELIVERY_METHOD.
    Returns a list of missing environment variable names.
    """
    missing = []
    if DELIVERY_METHOD == 'telegram':
        if not TELEGRAM_BOT_TOKEN:
            missing.append('TELEGRAM_BOT_TOKEN')
        if not TELEGRAM_CHAT_ID:
            missing.append('TELEGRAM_CHAT_ID')
    else:
        if not TWILIO_ACCOUNT_SID:
            missing.append('TWILIO_ACCOUNT_SID')
        if not TWILIO_AUTH_TOKEN:
            missing.append('TWILIO_AUTH_TOKEN')
        if not MY_PHONE_NUMBER:
            missing.append('MY_PHONE_NUMBER')
        if not TWILIO_FROM_NUMBER:
            missing.append('TWILIO_FROM_NUMBER')
    return missing
