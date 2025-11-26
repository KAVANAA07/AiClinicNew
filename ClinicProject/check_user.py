"""
Check user profile
Run: python manage.py shell < check_user.py
"""
from django.contrib.auth.models import User
from api.models import Patient, Doctor, Receptionist

username = "jas"

try:
    user = User.objects.get(username=username)
    print(f"\n✓ User found: {username}")
    print(f"  ID: {user.id}")
    print(f"  Email: {user.email}")
    print(f"  Is staff: {user.is_staff}")
    print(f"  Is active: {user.is_active}")
    
    # Check profiles
    print("\nProfiles:")
    
    if hasattr(user, 'patient'):
        print(f"  ✓ Patient: {user.patient.name}")
    else:
        print("  ✗ No Patient profile")
    
    if hasattr(user, 'doctor'):
        print(f"  ✓ Doctor: {user.doctor.name}")
    else:
        print("  ✗ No Doctor profile")
    
    if hasattr(user, 'receptionist'):
        print(f"  ✓ Receptionist at {user.receptionist.clinic.name}")
    else:
        print("  ✗ No Receptionist profile")
    
    print("\n" + "="*50)
    print("ISSUE: User has no profile!")
    print("="*50)
    print("\nTo fix, create a profile:")
    print(f"1. Patient: Patient.objects.create(user=user, name='Jas', age=25, phone_number='+1234567890')")
    print(f"2. Or login as a user with a profile")
    
except User.DoesNotExist:
    print(f"\n✗ User '{username}' not found")
