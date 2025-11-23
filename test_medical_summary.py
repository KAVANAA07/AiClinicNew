#!/usr/bin/env python3
"""
Test script for the Medical Summary System
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(project_dir, 'ClinicProject'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ClinicProject.settings')
django.setup()

from api.models import Patient, Doctor, Consultation, PrescriptionItem, Clinic
from api.medical_summary_views import MedicalSummaryView
from django.test import RequestFactory
from django.contrib.auth.models import User
from unittest.mock import Mock

def create_test_data():
    """Create test data for medical summary"""
    print("Creating test data...")
    
    # Create clinic
    clinic, _ = Clinic.objects.get_or_create(
        name="Test Medical Center",
        defaults={
            'address': '123 Test St',
            'city': 'Test City'
        }
    )
    
    # Create doctor user and doctor
    doctor_user, _ = User.objects.get_or_create(
        username='testdoctor',
        defaults={
            'first_name': 'Dr. Test',
            'last_name': 'Doctor',
            'is_staff': True
        }
    )
    
    doctor, _ = Doctor.objects.get_or_create(
        user=doctor_user,
        defaults={
            'name': 'Dr. Test Doctor',
            'specialization': 'General Medicine',
            'clinic': clinic
        }
    )
    
    # Create patient
    patient, _ = Patient.objects.get_or_create(
        phone_number='+1234567890',
        defaults={
            'name': 'John Test Patient',
            'age': 35
        }
    )
    
    # Create consultations with medical data
    consultations_data = [
        {
            'notes': 'Patient presents with severe headache and fever. Blood pressure: 140/90. Temperature: 101.5F. Diagnosed with acute migraine. Prescribed pain medication. Patient has allergy to penicillin.',
            'prescriptions': [
                {'medicine_name': 'Ibuprofen', 'dosage': '400mg', 'duration_days': 5, 'timing_morning': True, 'timing_evening': True},
                {'medicine_name': 'Sumatriptan', 'dosage': '50mg', 'duration_days': 3, 'timing_morning': False, 'timing_afternoon': True, 'timing_evening': False}
            ]
        },
        {
            'notes': 'Follow-up visit. Patient reports improvement. Blood test ordered for complete blood count. Vital signs normal. Continue current medication.',
            'prescriptions': [
                {'medicine_name': 'Ibuprofen', 'dosage': '200mg', 'duration_days': 7, 'timing_morning': True, 'timing_afternoon': False, 'timing_evening': True}
            ]
        },
        {
            'notes': 'Patient complains of chest pain. ECG performed - normal. Blood pressure: 130/85. Diagnosed with anxiety-related chest pain. Prescribed anti-anxiety medication. Patient advised stress management.',
            'prescriptions': [
                {'medicine_name': 'Lorazepam', 'dosage': '0.5mg', 'duration_days': 10, 'timing_morning': False, 'timing_afternoon': False, 'timing_evening': True}
            ]
        }
    ]
    
    # Create consultations
    for i, consultation_data in enumerate(consultations_data):
        consultation_date = datetime.now() - timedelta(days=(len(consultations_data) - i) * 7)
        
        consultation, created = Consultation.objects.get_or_create(
            patient=patient,
            doctor=doctor,
            date=consultation_date,
            defaults={'notes': consultation_data['notes']}
        )
        
        if created:
            # Create prescriptions
            for prescription_data in consultation_data['prescriptions']:
                PrescriptionItem.objects.create(
                    consultation=consultation,
                    **prescription_data
                )
    
    print(f"Created test data:")
    print(f"- Clinic: {clinic.name}")
    print(f"- Doctor: {doctor.name}")
    print(f"- Patient: {patient.name} ({patient.phone_number})")
    print(f"- Consultations: {Consultation.objects.filter(patient=patient).count()}")
    print(f"- Prescriptions: {PrescriptionItem.objects.filter(consultation__patient=patient).count()}")
    
    return patient, doctor

def test_medical_summary_api():
    """Test the medical summary API"""
    print("\n" + "="*50)
    print("TESTING MEDICAL SUMMARY API")
    print("="*50)
    
    patient, doctor = create_test_data()
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get(f'/api/medical-summary/?phone={patient.phone_number}')
    
    # Mock authenticated user (doctor)
    request.user = doctor.user
    
    # Create view instance and test
    view = MedicalSummaryView()
    response = view.get(request)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.data
        print(f"\nPatient Info:")
        print(f"- Name: {data['patient_info']['name']}")
        print(f"- Age: {data['patient_info']['age']}")
        print(f"- Phone: {data['patient_info']['phone_number']}")
        print(f"- Total Consultations: {data['total_consultations']}")
        
        print(f"\nRisk Alerts: {len(data['risk_alerts'])}")
        for alert in data['risk_alerts']:
            print(f"- {alert['type']}: {alert['message']} (Severity: {alert['severity']})")
        
        print(f"\nMedical Categories:")
        for category, items in data['medical_categories'].items():
            if items:
                print(f"- {category.title()}: {len(items)} items")
                for item in items[:2]:  # Show first 2 items
                    if category == 'prescriptions':
                        print(f"  * {item['medicine_name']} - {item['dosage']} (Risk: {item['risk_level']})")
                    elif category == 'diagnoses':
                        print(f"  * {item['diagnosis']} (Severity: {item['severity']})")
                    elif category == 'allergies':
                        print(f"  * {item['allergen']} (Risk: {item['risk_level']})")
        
        print(f"\nRecent Consultations: {len(data['recent_consultations'])}")
        for consultation in data['recent_consultations'][:3]:
            print(f"- {consultation['date']}: {consultation['doctor_name']} ({consultation['doctor_specialization']})")
            print(f"  Preview: {consultation['notes_preview']}")
        
        print(f"\nConsultation Links: {len(data['consultation_links'])}")
        for link in data['consultation_links'][:3]:
            print(f"- {link['date']}: {link['doctor']} -> {link['link']}")
        
        print("\n✅ Medical Summary API test PASSED!")
        return True
    else:
        print(f"❌ Medical Summary API test FAILED!")
        print(f"Error: {response.data}")
        return False

def test_consultation_detail_api():
    """Test the consultation detail API"""
    print("\n" + "="*50)
    print("TESTING CONSULTATION DETAIL API")
    print("="*50)
    
    patient, doctor = create_test_data()
    consultation = Consultation.objects.filter(patient=patient).first()
    
    if not consultation:
        print("❌ No consultation found for testing")
        return False
    
    # Import the view
    from api.medical_summary_views import ConsultationDetailView
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get(f'/api/consultation/{consultation.id}/')
    request.user = doctor.user
    
    # Create view instance and test
    view = ConsultationDetailView()
    response = view.get(request, consultation.id)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.data
        print(f"\nConsultation Details:")
        print(f"- ID: {data['id']}")
        print(f"- Date: {data['date']}")
        print(f"- Doctor: {data['doctor']['name']}")
        print(f"- Patient: {data['patient']['name']}")
        print(f"- Notes: {data['notes'][:100]}...")
        
        if 'prescription_items' in data and data['prescription_items']:
            print(f"- Prescriptions: {len(data['prescription_items'])}")
            for item in data['prescription_items']:
                print(f"  * {item['medicine_name']} - {item['dosage']} ({item['duration_days']} days)")
        
        if 'medical_structure' in data:
            print(f"- Medical Structure: Available")
            structure = data['medical_structure']
            for section, content in structure.items():
                if content and section != 'prescriptions':
                    print(f"  * {section.replace('_', ' ').title()}: {str(content)[:50]}...")
        
        print("\n✅ Consultation Detail API test PASSED!")
        return True
    else:
        print(f"❌ Consultation Detail API test FAILED!")
        print(f"Error: {response.data}")
        return False

def main():
    """Run all tests"""
    print("🏥 MEDICAL SUMMARY SYSTEM TEST")
    print("="*60)
    
    try:
        # Test medical summary API
        summary_test = test_medical_summary_api()
        
        # Test consultation detail API
        detail_test = test_consultation_detail_api()
        
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Medical Summary API: {'✅ PASSED' if summary_test else '❌ FAILED'}")
        print(f"Consultation Detail API: {'✅ PASSED' if detail_test else '❌ FAILED'}")
        
        if summary_test and detail_test:
            print("\n🎉 ALL TESTS PASSED! Medical Summary System is working correctly.")
            print("\nNext steps:")
            print("1. Start the Django server: python manage.py runserver")
            print("2. Start the React frontend: npm start")
            print("3. Login as a doctor and test the Medical Summary feature")
            print("4. Use phone number: +1234567890 to test with sample data")
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()