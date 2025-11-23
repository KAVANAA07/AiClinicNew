#!/usr/bin/env python3
"""
Test the doctor consultation summarizer with real patient data.
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.join(os.path.dirname(__file__), 'ClinicProject')
sys.path.insert(0, project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from api.models import Doctor, Patient, Consultation
from rest_framework.authtoken.models import Token
import json

User = get_user_model()

def test_doctor_summarizer():
    """Test AI summarizer for doctor consultations"""
    
    print("=== Testing Doctor Consultation Summarizer ===\n")
    
    # Find a doctor user for authentication
    doctor = Doctor.objects.first()
    if not doctor or not doctor.user:
        print("No doctor with user account found!")
        return
    
    print(f"Using doctor: {doctor.name} (User: {doctor.user.username})")
    
    # Get or create auth token
    token, _ = Token.objects.get_or_create(user=doctor.user)
    
    # Create test client
    client = Client()
    
    # Find a patient with consultations
    patient_with_consultations = None
    for patient in Patient.objects.all():
        if Consultation.objects.filter(patient=patient).exists():
            patient_with_consultations = patient
            break
    
    if not patient_with_consultations:
        print("No patients with consultations found!")
        return
    
    print(f"Testing with patient: {patient_with_consultations.name} (Phone: {patient_with_consultations.phone_number})")
    
    # Get patient's consultation history
    consultations = Consultation.objects.filter(patient=patient_with_consultations).order_by('-date')
    print(f"Patient has {consultations.count()} consultations")
    
    # Build patient history text
    history_text = ""
    for consultation in consultations:
        history_text += f"Date: {consultation.date}\n"
        history_text += f"Doctor: {consultation.doctor.name}\n"
        history_text += f"Notes: {consultation.notes}\n\n"
    
    print(f"History text length: {len(history_text)} characters")
    
    # Test the AI summarizer
    print("\n--- Testing AI Summary Generation ---")
    
    response = client.post(
        '/api/ai-summary/',
        data=json.dumps({
            'patient_history': history_text,
            'phone': patient_with_consultations.phone_number
        }),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    
    print(f"AI Summary response: {response.status_code}")
    
    if response.status_code == 200:
        data = json.loads(response.content)
        summary = data.get('summary', '')
        model = data.get('model', '')
        
        print(f"Model used: {model}")
        print(f"Summary generated: {len(summary)} characters")
        print("\n--- Generated Summary ---")
        print(summary)
        print("\n--- End Summary ---")
        
        print(f"\n[SUCCESS] Doctor consultation summarizer is working!")
        print(f"[SUCCESS] Doctors can now get AI-powered patient history summaries")
        
    else:
        try:
            error_data = json.loads(response.content)
            print(f"[ERROR] Summarizer failed: {error_data}")
        except:
            print(f"[ERROR] Summarizer failed with status {response.status_code}")
            print(f"Response: {response.content}")

if __name__ == "__main__":
    test_doctor_summarizer()