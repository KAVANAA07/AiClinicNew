from datetime import datetime, time
from api.models import Patient, Doctor, Consultation, PrescriptionItem
from api.utils.prescription_reminder import send_prescription_reminders

def test_prescription_reminders():
    print("Testing Prescription Reminders...")
    
    # Get or create test patient
    patient, created = Patient.objects.get_or_create(
        phone_number='+919876543210',
        defaults={
            'name': 'Test Patient',
            'age': 30,
            'gender': 'M'
        }
    )
    print(f"Patient: {patient.name} ({'created' if created else 'existing'})")
    
    # Get or create test doctor
    doctor, created = Doctor.objects.get_or_create(
        name='Dr. Test',
        defaults={
            'specialization': 'General Medicine',
            'phone_number': '+919876543211'
        }
    )
    print(f"Doctor: {doctor.name} ({'created' if created else 'existing'})")
    
    # Create test consultation
    consultation = Consultation.objects.create(
        patient=patient,
        doctor=doctor,
        notes='Test consultation for prescription reminders'
    )
    print(f"Consultation created: ID {consultation.id}")
    
    # Create test prescriptions
    prescription1 = PrescriptionItem.objects.create(
        consultation=consultation,
        medicine_name='Paracetamol',
        dosage='500mg',
        duration_days=3,
        timing_type='frequency',
        frequency_per_day=3,
        timing_1_time=time(8, 0),
        timing_1_food='after',
        timing_2_time=time(14, 0),
        timing_2_food='after',
        timing_3_time=time(20, 0),
        timing_3_food='after'
    )
    print(f"Prescription 1: {prescription1.medicine_name}")
    print(f"  Description: {prescription1.get_natural_description()}")
    
    prescription2 = PrescriptionItem.objects.create(
        consultation=consultation,
        medicine_name='Vitamin D',
        dosage='1000 IU',
        duration_days=7,
        timing_type='M',
        timing_morning=True,
        morning_time=time(9, 0),
        morning_food='with'
    )
    print(f"Prescription 2: {prescription2.medicine_name}")
    print(f"  Description: {prescription2.get_natural_description()}")
    
    print("\n" + "="*50)
    print("TESTING REMINDER SYSTEM")
    print("="*50)
    
    # Test the reminder system
    try:
        result = send_prescription_reminders()
        print(f"Reminder system result: {result}")
        
    except Exception as e:
        print(f"Error testing reminders: {e}")
        import traceback
        traceback.print_exc()
    
    print("Test completed!")

if __name__ == '__main__':
    test_prescription_reminders()