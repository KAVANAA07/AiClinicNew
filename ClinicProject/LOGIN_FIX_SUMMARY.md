# Login Issue Fixed - User "jas"

## Problem
User "jas" was unable to login despite having valid credentials. The authentication was successful, but the login failed with "Invalid Credentials" error.

## Root Cause
The LoginView in `api/views.py` requires users to have one of these profiles:
- Doctor profile (for staff/doctors)
- Receptionist profile (for staff/receptionists)  
- Patient profile (for patients)

User "jas" had a valid Django User account but no associated profile, causing the login to fail at the profile check stage.

## Solution Applied
Created a Patient profile for user "jas" with the following details:
- **Username**: jas
- **Name**: Jas
- **Age**: 25
- **Phone Number**: +918217612080

## Verification
```bash
User: jas
Has patient profile: True
Patient name: Jas
Patient phone: +918217612080
```

## How to Login Now
1. Go to the login page
2. Enter username: `jas`
3. Enter the password you set for this user
4. Login should now work successfully as a patient

## For Future Reference
If you encounter similar login issues:

1. **Check if user has a profile**:
```python
python manage.py shell -c "from django.contrib.auth.models import User; user = User.objects.get(username='USERNAME'); print(f'Has patient: {hasattr(user, \"patient\")}'); print(f'Has doctor: {hasattr(user, \"doctor\")}'); print(f'Has receptionist: {hasattr(user, \"receptionist\")}')"
```

2. **Create a patient profile**:
```python
python manage.py shell -c "from django.contrib.auth.models import User; from api.models import Patient; user = User.objects.get(username='USERNAME'); Patient.objects.create(user=user, name='NAME', age=AGE, phone_number='PHONE')"
```

3. **Create a doctor profile**:
```python
python manage.py shell -c "from django.contrib.auth.models import User; from api.models import Doctor, Clinic; user = User.objects.get(username='USERNAME'); clinic = Clinic.objects.first(); Doctor.objects.create(user=user, name='Dr. NAME', specialization='SPECIALTY', clinic=clinic)"
```

4. **Create a receptionist profile**:
```python
python manage.py shell -c "from django.contrib.auth.models import User; from api.models import Receptionist, Clinic; user = User.objects.get(username='USERNAME'); clinic = Clinic.objects.first(); Receptionist.objects.create(user=user, clinic=clinic)"
```

## Status
✅ **FIXED** - User "jas" can now login successfully as a patient
