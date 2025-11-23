#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from api.models import Token, Doctor, Patient, Clinic

def test_waiting_dashboard():
    """Test the waiting time dashboard APIs"""
    print("Testing Waiting Time Dashboard...")
    
    client = Client()
    
    # Test public dashboard (no auth required)
    print("\n1. Testing Public Dashboard...")
    response = client.get('/api/waiting-time/dashboard/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data.get('clinics', []))} clinics")
        
        for clinic in data.get('clinics', []):
            print(f"\nClinic: {clinic['clinic_name']}")
            print(f"Total Queue: {clinic['total_queue_length']}")
            print(f"Average Wait: {clinic['average_waiting_time_minutes']} minutes")
            
            for doctor in clinic.get('doctors', []):
                print(f"  Dr. {doctor['doctor_name']} ({doctor['specialization']})")
                print(f"    Queue: {doctor['current_queue_length']}")
                print(f"    Predicted Wait: {doctor['predicted_waiting_time_minutes']} min")
                print(f"    Today's Avg: {doctor['actual_avg_waiting_time_today']} min")
                if doctor['next_available_slot']:
                    print(f"    Next Slot: {doctor['next_available_slot']['display_text']}")
    
    # Test specific clinic dashboard
    print("\n2. Testing Specific Clinic Dashboard...")
    clinic = Clinic.objects.first()
    if clinic:
        response = client.get(f'/api/waiting-time/dashboard/{clinic.id}/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Specific clinic dashboard working!")
    
    # Test patient token waiting time (requires auth)
    print("\n3. Testing Patient Token Waiting Time...")
    
    # Create test user and patient
    user, created = User.objects.get_or_create(
        username='testpatient',
        defaults={'password': 'testpass'}
    )
    
    patient, created = Patient.objects.get_or_create(
        user=user,
        defaults={
            'name': 'Test Patient',
            'age': 30,
            'phone_number': '9999999999'
        }
    )
    
    # Create test token
    doctor = Doctor.objects.first()
    if doctor:
        token, created = Token.objects.get_or_create(
            patient=patient,
            doctor=doctor,
            date=django.utils.timezone.now().date(),
            defaults={'status': 'waiting'}
        )
        
        # Login and test
        client.force_login(user)
        response = client.get('/api/waiting-time/my-token/')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Token: {data.get('token_number')}")
            print(f"Queue Position: {data.get('queue_position')}")
            print(f"Expected Wait: {data.get('predicted_waiting_time_minutes')} min")
            print(f"Message: {data.get('message')}")
    
    print("\nDashboard API testing completed!")

def demo_api_calls():
    """Demo API calls for frontend integration"""
    print("\n" + "="*50)
    print("FRONTEND INTEGRATION EXAMPLES")
    print("="*50)
    
    base_url = "http://localhost:8000/api"
    
    print("\n1. Get All Clinics Waiting Times (Public)")
    print(f"GET {base_url}/waiting-time/dashboard/")
    print("Response: Clinic list with doctor waiting times")
    
    print("\n2. Get Specific Clinic Waiting Times")
    print(f"GET {base_url}/waiting-time/dashboard/1/")
    print("Response: Single clinic with detailed doctor info")
    
    print("\n3. Get My Token Waiting Time (Authenticated)")
    print(f"GET {base_url}/waiting-time/my-token/")
    print("Headers: Authorization: Token <user_token>")
    print("Response: Personal waiting time and queue position")
    
    print("\n4. Sample Frontend Code:")
    print("""
// Get clinic waiting times for home page
fetch('/api/waiting-time/dashboard/')
  .then(response => response.json())
  .then(data => {
    data.clinics.forEach(clinic => {
      console.log(`${clinic.clinic_name}: ${clinic.average_waiting_time_minutes} min wait`);
      clinic.doctors.forEach(doctor => {
        console.log(`Dr. ${doctor.doctor_name}: ${doctor.predicted_waiting_time_minutes} min`);
      });
    });
  });

// Get my token info (authenticated)
fetch('/api/waiting-time/my-token/', {
  headers: { 'Authorization': 'Token ' + userToken }
})
  .then(response => response.json())
  .then(data => {
    console.log(`You are #${data.queue_position} in queue`);
    console.log(`Expected wait: ${data.predicted_waiting_time_minutes} minutes`);
  });
    """)

if __name__ == "__main__":
    test_waiting_dashboard()
    demo_api_calls()