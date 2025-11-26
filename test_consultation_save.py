#!/usr/bin/env python3
"""
Test consultation creation and saving functionality
"""

import os
import sys
import django
import json

# Add the project directory to Python path
project_dir = os.path.join(os.path.dirname(__file__), 'ClinicProject')
sys.path.insert(0, project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from api.views import ConsultationCreateView
from api.models import Doctor, Patient, Consultation, PrescriptionItem

User = get_user_model()

def test_consultation_creation():
    """Test consultation creation with prescriptions"""
    
    print("=== Testing Consultation Creation ===\n")
    
    # Find a doctor user for authentication
    doctor = Doctor.objects.first()
    if not doctor or not doctor.user:
        print("No doctor with user account found!")
        return
    
    print(f"Using doctor: {doctor.name} (User: {doctor.user.username})")
    
    # Find or create a test patient
    patient = Patient.objects.first()
    if not patient:
        print("No patient found!")
        return
    
    print(f"Using patient: {patient.name} (ID: {patient.id})")
    
    # Test data for consultation with prescriptions
    consultation_data = {
        'patient': patient.id,
        'notes': 'Test consultation notes - patient presented with fever and headache. Diagnosed with viral infection.',
        'prescription_items': [
            {
                'medicine_name': 'Paracetamol',
                'dosage': '500mg',
                'duration_days': 5,
                'timing_type': 'frequency',
                'frequency_per_day': 3,
                'timing_1_time': '08:00',
                'timing_2_time': '14:00',
                'timing_3_time': '20:00',
                'timing_1_food': 'after',
                'timing_2_food': 'after',
                'timing_3_food': 'after',
                'special_instructions': 'Take with plenty of water'
            },
            {
                'medicine_name': 'Cetirizine',
                'dosage': '10mg',
                'duration_days': 3,
                'timing_type': 'N',
                'timing_morning': False,
                'timing_afternoon': False,
                'timing_evening': True,
                'evening_time': '21:00',
                'evening_food': 'after'
            }
        ]
    }
    
    # Create a request
    factory = RequestFactory()
    request = factory.post(
        '/api/consultations/create/',
        data=json.dumps(consultation_data),
        content_type='application/json'
    )
    request.user = doctor.user
    
    # Call the view
    view = ConsultationCreateView()
    response = view.post(request)
    
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
    
    if response.status_code == 201:
        consultation_id = response.data.get('id')
        print(f"\n[SUCCESS] Consultation created with ID: {consultation_id}")
        
        # Verify consultation was saved
        try:
            consultation = Consultation.objects.get(id=consultation_id)
            print(f"[SUCCESS] Consultation found in database")
            print(f"  - Patient: {consultation.patient.name}")
            print(f"  - Doctor: {consultation.doctor.name}")
            print(f"  - Notes: {consultation.notes[:50]}...")
            print(f"  - Date: {consultation.date}")
            
            # Check prescriptions
            prescriptions = PrescriptionItem.objects.filter(consultation=consultation)
            print(f"  - Prescriptions: {prescriptions.count()}")
            
            for i, prescription in enumerate(prescriptions, 1):
                print(f"    {i}. {prescription.medicine_name} {prescription.dosage}")
                print(f"       Duration: {prescription.duration_days} days")
                print(f"       Timing: {prescription.timing_type}")
                if prescription.timing_type == 'frequency':
                    print(f"       Frequency: {prescription.frequency_per_day} times/day")
                print(f"       Natural description: {prescription.get_natural_description()}")
            
            print(f"\n[SUCCESS] Consultation and prescriptions saved successfully!")
            
        except Consultation.DoesNotExist:
            print(f"[ERROR] Consultation {consultation_id} not found in database!")
            
    else:
        print(f"[ERROR] Consultation creation failed")
        if hasattr(response, 'data') and response.data:
            print(f"Error details: {response.data}")

def test_consultation_history():
    """Test if consultation appears in patient history"""
    
    print("\n=== Testing Consultation History ===\n")
    
    patient = Patient.objects.first()
    if not patient:
        print("No patient found!")
        return
    
    consultations = Consultation.objects.filter(patient=patient).order_by('-date')
    print(f"Found {consultations.count()} consultations for patient {patient.name}")
    
    for i, consultation in enumerate(consultations[:3], 1):
        print(f"{i}. Date: {consultation.date}")
        print(f"   Doctor: {consultation.doctor.name}")
        print(f"   Notes: {consultation.notes[:60]}...")
        
        prescriptions = consultation.prescription_items.all()
        if prescriptions.exists():
            print(f"   Prescriptions: {prescriptions.count()}")
            for prescription in prescriptions:
                print(f"     - {prescription.get_natural_description()}")
        print()

if __name__ == "__main__":
    test_consultation_creation()
    test_consultation_history()