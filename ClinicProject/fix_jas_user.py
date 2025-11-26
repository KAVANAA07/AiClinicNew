"""
Quick fix script to add Patient profile for user 'jas'
Run this with: python manage.py shell < fix_jas_user.py
"""

from django.contrib.auth.models import User
from api.models import Patient

try:
    # Get the user
    user = User.objects.get(username='jas')
    print(f"Found user: {user.username} (ID: {user.id})")
    
    # Check if patient profile already exists
    if hasattr(user, 'patient'):
        print(f"User already has a patient profile: {user.patient.name}")
    else:
        # Create patient profile
        patient = Patient.objects.create(
            user=user,
            name='Jas',
            age=25,
            phone_number='+918217612080'
        )
        print(f"✓ Created patient profile for {user.username}")
        print(f"  Name: {patient.name}")
        print(f"  Phone: {patient.phone_number}")
        print(f"  Age: {patient.age}")
        print("\nUser can now login successfully!")
        
except User.DoesNotExist:
    print("ERROR: User 'jas' not found in database")
except Exception as e:
    print(f"ERROR: {e}")
