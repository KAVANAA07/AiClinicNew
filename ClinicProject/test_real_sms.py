from datetime import datetime, time
from django.utils import timezone
from api.models import Patient, Doctor, Consultation, PrescriptionItem
from api.utils.prescription_reminder import send_prescription_reminders

# Clean up previous test data
PrescriptionItem.objects.filter(medicine_name='Test Medicine').delete()
Patient.objects.filter(phone_number='+918217612080').delete()

# Create test data with the specified phone number
patient = Patient.objects.create(name='Test Patient', age=30, phone_number='+918217612080')
doctor = Doctor.objects.create(name='Dr. Test', specialization='General Medicine')
consultation = Consultation.objects.create(patient=patient, doctor=doctor, notes='Test consultation')

# Get current time for testing
now = timezone.now()
current_minute = now.replace(second=0, microsecond=0).time()

print(f"Current time: {current_minute}")
print(f"Sending SMS to: {patient.phone_number}")

# Create prescription with current time
prescription = PrescriptionItem.objects.create(
    consultation=consultation,
    medicine_name='Paracetamol',
    dosage='500mg',
    duration_days=3,
    timing_type='frequency',
    frequency_per_day=1,
    timing_1_time=current_minute,
    timing_1_food='after'
)

print(f"Created prescription: {prescription.medicine_name}")

# Test reminder system
result = send_prescription_reminders()
print(f"Reminder result: {result}")

print("Test completed!")