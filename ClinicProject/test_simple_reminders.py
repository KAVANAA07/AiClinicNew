from datetime import datetime, time
from api.models import Patient, Doctor, Consultation, PrescriptionItem
from api.utils.prescription_reminder import send_prescription_reminders

# Create test data
patient = Patient.objects.create(name='Test Patient', age=30, phone_number='+919876543210')
doctor = Doctor.objects.create(name='Dr. Test', specialization='General Medicine')
consultation = Consultation.objects.create(patient=patient, doctor=doctor, notes='Test consultation')

# Create prescription with current time for testing
current_time = datetime.now().time()
prescription = PrescriptionItem.objects.create(
    consultation=consultation,
    medicine_name='Paracetamol',
    dosage='500mg',
    duration_days=3,
    timing_type='frequency',
    frequency_per_day=1,
    timing_1_time=current_time,
    timing_1_food='after'
)

print(f"Created prescription: {prescription.medicine_name}")
print(f"Reminder time: {current_time}")
print(f"Description: {prescription.get_natural_description()}")

# Test reminder system
result = send_prescription_reminders()
print(f"Reminder result: {result}")