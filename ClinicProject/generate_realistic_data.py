import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token, Doctor, Patient

def generate_realistic_training_data():
    """Generate realistic training data with real-world scenarios"""
    
    doctors = list(Doctor.objects.all()[:5])
    patients = list(Patient.objects.all())
    
    if not doctors or not patients:
        print("Need doctors and patients in database")
        return
    
    # Clear ALL tokens to start fresh
    Token.objects.all().delete()
    print("Cleared all existing tokens")
    
    start_date = timezone.now() - timedelta(days=60)
    tokens_created = 0
    token_counter = 0
    
    for day in range(60):
        current_date = start_date + timedelta(days=day)
        
        # Skip some random days (clinic closed)
        if random.random() < 0.15:
            continue
        
        for doctor in doctors:
            # Each doctor sees 8-15 patients per day
            num_patients = random.randint(8, 15)
            clinic_start = current_date.replace(hour=9, minute=0, second=0)
            
            for i in range(num_patients):
                patient = random.choice(patients)
                
                # Appointment scheduled every 15-20 minutes with seconds offset
                appointment_time = clinic_start + timedelta(minutes=i * random.randint(15, 20), seconds=i)
                
                # Real-world arrival patterns
                arrival_scenario = random.choices(
                    ['early', 'ontime', 'late', 'walkin'],
                    weights=[0.25, 0.45, 0.20, 0.10]
                )[0]
                
                if arrival_scenario == 'early':
                    actual_arrival = appointment_time - timedelta(minutes=random.randint(5, 20))
                elif arrival_scenario == 'ontime':
                    actual_arrival = appointment_time + timedelta(minutes=random.randint(-3, 5))
                elif arrival_scenario == 'late':
                    actual_arrival = appointment_time + timedelta(minutes=random.randint(10, 30))
                else:  # walkin
                    actual_arrival = appointment_time + timedelta(minutes=random.randint(-10, 20))
                    appointment_time = actual_arrival  # Walk-ins have same appointment and arrival
                
                # Queue position affects wait time
                queue_position = i + 1
                
                # Consultation start time based on queue and previous consultations
                if i == 0:
                    consultation_start = actual_arrival + timedelta(minutes=random.randint(0, 5))
                else:
                    # Previous patient consultation time affects next patient
                    base_wait = queue_position * random.randint(3, 8)
                    random_delay = random.randint(-5, 15)  # Doctor delays, early finishes
                    consultation_start = actual_arrival + timedelta(minutes=base_wait + random_delay)
                
                # Consultation duration varies by complexity
                consultation_duration = random.choices(
                    [5, 8, 10, 12, 15, 20, 25, 30],
                    weights=[0.05, 0.15, 0.25, 0.25, 0.15, 0.10, 0.03, 0.02]
                )[0]
                
                completed_at = consultation_start + timedelta(minutes=consultation_duration)
                
                # Calculate actual wait time
                wait_minutes = int((consultation_start - actual_arrival).total_seconds() / 60)
                wait_minutes = max(0, wait_minutes)  # No negative waits
                
                # Create token with unique number
                try:
                    Token.objects.create(
                        patient=patient,
                        doctor=doctor,
                        token_number=f"TRAIN{token_counter:05d}",
                        status='Completed',
                        appointment_time=appointment_time,
                        consultation_start_time=consultation_start,
                        completed_at=completed_at,
                        predicted_waiting_time=wait_minutes,
                        created_at=actual_arrival
                    )
                    tokens_created += 1
                    token_counter += 1
                except Exception as e:
                    token_counter += 1
                    continue
    
    print(f"Created {tokens_created} realistic training tokens")
    
    # Show distribution
    completed_tokens = Token.objects.filter(status='Completed')
    short = sum(1 for t in completed_tokens if t.predicted_waiting_time and t.predicted_waiting_time <= 10)
    medium = sum(1 for t in completed_tokens if t.predicted_waiting_time and 10 < t.predicted_waiting_time <= 20)
    long = sum(1 for t in completed_tokens if t.predicted_waiting_time and t.predicted_waiting_time > 20)
    
    print(f"\nDistribution:")
    print(f"  Short (0-10 min): {short}")
    print(f"  Medium (11-20 min): {medium}")
    print(f"  Long (21+ min): {long}")
    print(f"  Total: {tokens_created}")

if __name__ == '__main__':
    generate_realistic_training_data()
