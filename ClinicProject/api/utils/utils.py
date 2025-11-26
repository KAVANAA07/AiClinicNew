# api/utils.py

from django.conf import settings
# REMOVED: from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

def send_sms_notification(to_number, message):
    """
    Sends real SMS via Twilio or simulates if credentials not configured.
    """
    # Clean phone number - remove spaces and ensure proper format
    to_number = str(to_number).strip().replace(' ', '')
    if not to_number.startswith('+'):
        to_number = '+' + to_number
    
    # Check if real Twilio credentials are configured
    if (settings.TWILIO_ACCOUNT_SID != 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' and 
        settings.TWILIO_AUTH_TOKEN != 'your_auth_token'):
        
        try:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            print(f"\n[REAL SMS] Sending to {to_number}...")
            
            message_obj = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to_number
            )
            
            print(f"SUCCESS: Real SMS sent! SID: {message_obj.sid}")
            logger.info(f"Real SMS sent to {to_number}: {message[:50]}...")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to send real SMS - {e}")
            logger.error(f"Failed to send SMS to {to_number}: {e}")
            return False
    
    else:
        # Simulation mode
        print(f"\n[SMS SIMULATION] To: {to_number}")
        print(f"Message: {message}")
        print(f"[SMS SIMULATION] Completed - Would send in production\n")
        
        logger.info(f"SMS simulated to {to_number}: {message[:50]}...")
        return True 


### **Step 1.2: Update `settings.py` for Render**