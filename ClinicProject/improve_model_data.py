import os
import sys
import django

sys.path.append('c:/Users/VITUS/AiClinicNew/ClinicProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token, Doctor, Patient, Clinic
from django.utils import timezone
from datetime import datetime, timedelta, time
import random

print("="*70)
print("IMPROVING MODEL WITH BALANCED TRAINING DATA")
print("="*70)

# Get or create doctors
doctors = list(Doctor.objects.all()[:3])
if not doctors:
    print("No doctors found. Please create doctors first.")
    sys.exit(1)

# Get or create patients
patients = list(Patient.objects.all()[:50])
if len(patients) < 10:
    print("Creating patients...")
    for i in range(50):
        patient, _ = Patient.objects.get_or_create(
            phone_number=f'+9198765432{i:02d}',
            defaults={
                'name': f'Patient {i+1}',
                'age': random.randint(20, 70),
                'gender': random.choice(['M', 'F'])
            }
        )
        patients.append(patient)

print(f"Using {len(doctors)} doctors and {len(patients)} patients")

# Generate realistic consultation data
print("\nGenerating balanced training data...")

# Define realistic wait time distributions
wait_time_scenarios = [
    # (wait_minutes, probability, category)
    (5, 0.10, 'Short'),    # Very quick
    (10, 0.15, 'Short'),   # Quick
    (15, 0.15, 'Short'),   # Normal short
    (20, 0.15, 'Medium'),  # Normal medium
    (25, 0.15, 'Medium'),  # Normal medium
    (30, 0.10, 'Medium'),  # Slightly delayed
    (35, 0.08, 'Long'),    # Delayed
    (40, 0.06, 'Long'),    # More delayed
    (45, 0.04, 'Long'),    # Very delayed
    (50, 0.02, 'Long'),    # Extremely delayed
]

# Generate data for past 30 days
start_date = timezone.now().date() - timedelta(days=30)
generated_count = 0

for day_offset in range(30):
    current_date = start_date + timedelta(days=day_offset)
    
    # Skip weekends (optional)
    if current_date.weekday() >= 5:  # Saturday, Sunday
        continue
    
    # Generate 5-15 consultations per day
    consultations_per_day = random.randint(5, 15)
    
    for _ in range(consultations_per_day):
        # Select random doctor and patient
        doctor = random.choice(doctors)
        patient = random.choice(patients)
        
        # Generate appointment time (9 AM to 5 PM)
        hour = random.randint(9, 16)
        minute = random.choice([0, 15, 30, 45])
        appointment_time = time(hour, minute)
        
        # Select wait time based on probability distribution
        wait_minutes = random.choices(
            [w[0] for w in wait_time_scenarios],
            weights=[w[1] for w in wait_time_scenarios]
        )[0]
        
        # Calculate times
        appointment_dt = timezone.make_aware(
            datetime.combine(current_date, appointment_time)
        )
        
        # Consultation starts after wait time
        consultation_start = appointment_dt + timedelta(minutes=wait_minutes)
        
        # Consultation duration (10-25 minutes)
        consultation_duration = random.randint(10, 25)
        completed_at = consultation_start + timedelta(minutes=consultation_duration)
        
        # Create token
        try:
            token = Token.objects.create(
                patient=patient,
                doctor=doctor,
                date=current_date,
                appointment_time=appointment_time,
                status='completed',
                consultation_start_time=consultation_start,
                completed_at=completed_at,
                predicted_waiting_time=wait_minutes
            )
            generated_count += 1
        except Exception as e:
            # Skip duplicates
            continue

print(f"\nGenerated {generated_count} new training samples")

# Verify data distribution
from django.db.models import Count

print("\nData distribution by wait time category:")
completed_tokens = Token.objects.filter(
    status='completed',
    completed_at__isnull=False,
    appointment_time__isnull=False,
    consultation_start_time__isnull=False
)

short_count = 0
medium_count = 0
long_count = 0

for token in completed_tokens:
    wait_time = (token.consultation_start_time - timezone.make_aware(
        datetime.combine(token.date, token.appointment_time)
    )).total_seconds() / 60
    
    if wait_time <= 15:
        short_count += 1
    elif wait_time <= 30:
        medium_count += 1
    else:
        long_count += 1

print(f"   Short (0-15 min):   {short_count} samples")
print(f"   Medium (16-30 min): {medium_count} samples")
print(f"   Long (31+ min):     {long_count} samples")
print(f"   Total:              {completed_tokens.count()} samples")

if short_count > 20 and medium_count > 20 and long_count > 20:
    print("\nSUCCESS: Balanced dataset created!")
    print("Now run: python manage.py evaluate_model")
else:
    print("\nWARNING: Dataset still imbalanced. Run script again.")

print("\n" + "="*70)
