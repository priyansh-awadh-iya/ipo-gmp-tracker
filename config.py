import os
from dotenv import load_dotenv

# Load local .env file if present
load_dotenv()

# Threshold expected listing gain percentage to trigger notifications
THRESHOLD_GAIN_PCT = 15.0

# Delivery method: 'whatsapp' or 'sms'
DELIVERY_METHOD = os.environ.get('DELIVERY_METHOD', 'whatsapp').lower()

# Twilio API credentials and phone configurations
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
MY_PHONE_NUMBER = os.environ.get('MY_PHONE_NUMBER')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')

def validate_config():
    """
    Validates that necessary Twilio config values are provided.
    Returns a list of missing environment variable names.
    """
    missing = []
    if not TWILIO_ACCOUNT_SID:
        missing.append('TWILIO_ACCOUNT_SID')
    if not TWILIO_AUTH_TOKEN:
        missing.append('TWILIO_AUTH_TOKEN')
    if not MY_PHONE_NUMBER:
        missing.append('MY_PHONE_NUMBER')
    if not TWILIO_FROM_NUMBER:
        missing.append('TWILIO_FROM_NUMBER')
    return missing
