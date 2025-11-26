from api.utils.utils import send_sms_notification

phone_number = '+918217612080'
message = 'Test SMS from AI Clinic'

print(f"Testing SMS to: {phone_number}")
result = send_sms_notification(phone_number, message)
print(f"Result: {result}")