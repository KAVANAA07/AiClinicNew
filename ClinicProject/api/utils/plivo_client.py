"""
Plivo SMS/Voice client as alternative to Twilio
Sign up: https://www.plivo.com/
Free trial: $10 credit
"""
import plivo
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_sms_plivo(to_number, message):
    """Send SMS using Plivo"""
    try:
        client = plivo.RestClient(
            auth_id=settings.PLIVO_AUTH_ID,
            auth_token=settings.PLIVO_AUTH_TOKEN
        )
        
        response = client.messages.create(
            src=settings.PLIVO_PHONE_NUMBER,
            dst=to_number,
            text=message
        )
        
        logger.info(f"Plivo SMS sent to {to_number}: {response}")
        return True
    except Exception as e:
        logger.error(f"Plivo SMS failed: {e}")
        return False

def make_call_plivo(to_number, answer_url):
    """Make voice call using Plivo"""
    try:
        client = plivo.RestClient(
            auth_id=settings.PLIVO_AUTH_ID,
            auth_token=settings.PLIVO_AUTH_TOKEN
        )
        
        response = client.calls.create(
            from_=settings.PLIVO_PHONE_NUMBER,
            to_=to_number,
            answer_url=answer_url,
            answer_method='POST'
        )
        
        logger.info(f"Plivo call initiated to {to_number}: {response}")
        return True
    except Exception as e:
        logger.error(f"Plivo call failed: {e}")
        return False
