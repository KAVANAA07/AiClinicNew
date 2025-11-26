#!/usr/bin/env python3
"""
Test consultation creation with prescriptions to debug frontend issues.
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
    
    # Find a patient
    patient = Patient.objects.first()
    if not patient:
        print("No patient found!")
        return
    
    print(f"Using doctor: {doctor.name} (User: {doctor.user.username})")
    print(f"Using patient: {patient.name}")
    
    # Create test consultation data
    consultation_data = {
        'patient': patient.id,
        'notes': 'Test consultation notes from frontend debugging',
        'prescription_items': [
            {
                'medicine_name': 'Paracetamol',
                'dosage': '500mg',
                'duration_days': 5,
                'timing_type': 'M',
                'timing_morning': True,
                'timing_afternoon': False,
                'timing_evening': False,
                'timing_night': False,
                'morning_time': '08:00',
                'morning_food': 'after',
                'special_instructions': 'Take with water'
            },
            {
                'medicine_name': 'Cetirizine',
                'dosage': '10mg',
                'duration_days': 3,
                'timing_type': 'frequency',
                'frequency_per_day': 2,
                'timing_1_time': '09:00',
                'timing_1_food': 'after',
                'timing_2_time': '21:00',
                'timing_2_food': 'after'
            }
        ]
    }
    
    print(f"Test data: {json.dumps(consultation_data, indent=2)}")
    
    # Create a request
    factory = RequestFactory()
    request = factory.post('/api/consultations/create/', 
                          data=json.dumps(consultation_data),
                          content_type='application/json')
    request.user = doctor.user
    
    # Call the view
    view = ConsultationCreateView()
    response = view.post(request)
    
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
    
    if response.status_code == 201:
        consultation_id = response.data.get('id')
        print(f"\n[SUCCESS] Consultation {consultation_id} created successfully!")
        
        # Verify prescriptions were created
        consultation = Consultation.objects.get(id=consultation_id)
        prescriptions = PrescriptionItem.objects.filter(consultation=consultation)
        
        print(f"[SUCCESS] {prescriptions.count()} prescriptions created:")
        for i, prescription in enumerate(prescriptions, 1):
            print(f"  {i}. {prescription.medicine_name} - {prescription.dosage}")
            print(f"     Natural description: {prescription.get_natural_description()}")
        
        print("\n[SUCCESS] Frontend consultation creation should work!")
    else:
        print(f"[ERROR] Consultation creation failed: {response.data}")

if __name__ == "__main__":
    test_consultation_creation()