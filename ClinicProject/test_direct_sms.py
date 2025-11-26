from api.utils.utils import send_sms_notification

# Test direct SMS to 8217612080
phone_number = '+918217612080'
message = 'Test SMS from AI Clinic - Prescription reminder system is working!'

print(f"Testing SMS to: {phone_number}")
print(f"Message: {message}")

result = send_sms_notification(phone_number, message)

if result:
    print("✅ SMS sent successfully!")
else:
    print("❌ SMS failed - Check Twilio credentials")

print("Direct SMS test completed!")