#!/usr/bin/env python
"""
Check SMS delivery status from Twilio
"""

import os
from twilio.rest import Client

# Your Twilio credentials from environment variables
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')

# SMS SID from your logs
sms_sid = 'SMd02c6b70eae8b63c4f0484da677331cd'

try:
    client = Client(account_sid, auth_token)
    message = client.messages(sms_sid).fetch()
    
    print(f"SMS Status Check:")
    print(f"SID: {message.sid}")
    print(f"To: {message.to}")
    print(f"From: {message.from_}")
    print(f"Status: {message.status}")
    print(f"Error Code: {message.error_code}")
    print(f"Error Message: {message.error_message}")
    print(f"Date Sent: {message.date_sent}")
    print(f"Body: {message.body[:100]}...")
    
except Exception as e:
    print(f"Error checking SMS status: {e}")