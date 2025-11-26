"""
Simple manual test for prescription reminders
Run: python manage.py shell
Then paste this code
"""
from api.tasks import send_prescription_reminder_sms

# Test sending a prescription reminder
test_phone = "+1234567890"  # CHANGE THIS TO YOUR PHONE NUMBER
test_message = "Reminder: Take Paracetamol - 500mg (Morning dose)"

print(f"Sending test SMS to {test_phone}...")
send_prescription_reminder_sms(test_phone, test_message)
print("Done! Check your phone for the SMS.")
