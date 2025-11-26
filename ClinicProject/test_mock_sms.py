from datetime import datetime, time
from django.utils import timezone
from api.models import Patient, Doctor, Consultation, PrescriptionItem, PrescriptionReminder
from api.utils.prescription_reminder import send_prescription_reminders

# Mock SMS function for testing
def mock_send_sms(to_number, message):
    print(f"\n[MOCK SMS SUCCESS] To: {to_number}")
    print(f"Message: {message}")
    print("[MOCK SMS] Delivered successfully!\n")
    return True

# Patch the SMS function temporarily
import api.utils.prescription_reminder
original_send_sms = api.utils.prescription_reminder.send_sms_notification
api.utils.prescription_reminder.send_sms_notification = mock_send_sms

# Clean up previous test data
PrescriptionItem.objects.filter(medicine_name='Test Medicine').delete()
Patient.objects.filter(name='Test Patient').delete()

# Create test data
patient = Patient.objects.create(name='Test Patient', age=30, phone_number='+919876543210')
doctor = Doctor.objects.create(name='Dr. Test', specialization='General Medicine')
consultation = Consultation.objects.create(patient=patient, doctor=doctor, notes='Test consultation')

# Get current time and round to nearest minute for testing
now = timezone.now()
current_minute = now.replace(second=0, microsecond=0).time()

print(f"Current time: {current_minute}")

# Create prescription with current time
prescription = PrescriptionItem.objects.create(
    consultation=consultation,
    medicine_name='Test Medicine',
    dosage='500mg',
    duration_days=3,
    timing_type='frequency',
    frequency_per_day=1,
    timing_1_time=current_minute,
    timing_1_food='after'
)

print(f"Created prescription: {prescription.medicine_name}")
print(f"Reminder time: {prescription.timing_1_time}")

# Test reminder system with mock SMS
result = send_prescription_reminders()
print(f"Reminder result: {result}")

# Check if reminder was created
reminders = PrescriptionReminder.objects.filter(prescription=prescription)
print(f"Reminders created: {reminders.count()}")

for reminder in reminders:
    print(f"  - Reminder at {reminder.reminder_time} on {reminder.sent_date}")
    print(f"  - Dose info: {reminder.dose_info}")

# Restore original SMS function
api.utils.prescription_reminder.send_sms_notification = original_send_sms

print("Test completed with mock SMS!")