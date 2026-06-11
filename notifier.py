import logging
from twilio.rest import Client
import config

logger = logging.getLogger(__name__)

def mask_phone_number(number_str):
    """
    Masks all but the last 4 digits of a phone number string (preserving the 'whatsapp:' prefix).
    """
    if not number_str:
        return "N/A"
    prefix = ""
    num = number_str
    if number_str.startswith("whatsapp:"):
        prefix = "whatsapp:"
        num = number_str[9:]
    if len(num) > 4:
        return f"{prefix}{'*' * (len(num) - 4)}{num[-4:]}"
    return number_str

def send_alert(company_name, listing_gain_pct, consensus_gmp, cutoff_price, close_date):
    """
    Compiles and sends a WhatsApp or SMS alert using the Twilio client.
    """
    missing_vars = config.validate_config()
    if missing_vars:
        logger.error(f"Cannot send alert. Missing environment variables: {', '.join(missing_vars)}")
        return False

    # Format the message body
    # *Consensus IPO Alert* triggers bold formatting in WhatsApp
    message_body = (
        f"*Consensus IPO Alert*\n"
        f"Company: {company_name}\n"
        f"Expected Premium: {listing_gain_pct}%\n"
        f"Consensus Avg GMP: INR {consensus_gmp}\n"
        f"Cut-off Price: INR {cutoff_price}\n"
        f"Last Date to Apply: {close_date}\n"
        f"Action: Threshold criteria breached. Ready for subscription review."
    )

    try:
        # Initialize Twilio Client
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        
        # Configure numbers based on delivery method
        if config.DELIVERY_METHOD == 'whatsapp':
            from_number = f"whatsapp:{config.TWILIO_FROM_NUMBER}"
            to_number = f"whatsapp:{config.MY_PHONE_NUMBER}"
        else:
            # Clean up number prefix in case user included 'whatsapp:' manually
            from_number = config.TWILIO_FROM_NUMBER.replace('whatsapp:', '')
            to_number = config.MY_PHONE_NUMBER.replace('whatsapp:', '')

        masked_from = mask_phone_number(from_number)
        masked_to = mask_phone_number(to_number)
        logger.info(f"Dispatching alert via {config.DELIVERY_METHOD.upper()}...")
        logger.info(f"Sender: {masked_from} -> Recipient: {masked_to}")

        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        
        logger.info(f"Alert sent successfully! Message SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Twilio message: {e}")
        return False
