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
    """Generate highly realistic training data with real-world variability"""
    
    doctors = list(Doctor.objects.all()[:5])
    patients = list(Patient.objects.all())
    
    if not doctors or not patients:
        print("Need doctors and patients in database")
        return
    
    # Clear ALL tokens to start fresh
    Token.objects.all().delete()
    print("Cleared all existing tokens")
    
    start_date = timezone.now() - timedelta(days=90)
    tokens_created = 0
    token_counter = 0
    
    for day in range(90):
        current_date = start_date + timedelta(days=day)
        
        # Skip weekends and random days
        if current_date.weekday() >= 5 or random.random() < 0.10:
            continue
        
        for doctor in doctors:
            # Variable patients per day (6-18)
            num_patients = random.randint(6, 18)
            clinic_start = current_date.replace(hour=9, minute=0, second=0)
            
            # Doctor's efficiency varies by day
            doctor_speed_factor = random.uniform(0.7, 1.3)
            
            for i in range(num_patients):
                patient = random.choice(patients)
                
                # Appointments scheduled with varying intervals
                base_interval = random.randint(12, 25)
                appointment_time = clinic_start + timedelta(minutes=i * base_interval, seconds=token_counter)
                
                # Real-world arrival patterns with more variability
                arrival_type = random.choices(
                    ['very_early', 'early', 'ontime', 'slightly_late', 'late', 'very_late', 'walkin'],
                    weights=[0.10, 0.20, 0.35, 0.15, 0.10, 0.05, 0.05]
                )[0]
                
                if arrival_type == 'very_early':
                    actual_arrival = appointment_time - timedelta(minutes=random.randint(15, 30))
                elif arrival_type == 'early':
                    actual_arrival = appointment_time - timedelta(minutes=random.randint(5, 15))
                elif arrival_type == 'ontime':
                    actual_arrival = appointment_time + timedelta(minutes=random.randint(-2, 3))
                elif arrival_type == 'slightly_late':
                    actual_arrival = appointment_time + timedelta(minutes=random.randint(3, 10))
                elif arrival_type == 'late':
                    actual_arrival = appointment_time + timedelta(minutes=random.randint(10, 25))
                elif arrival_type == 'very_late':
                    actual_arrival = appointment_time + timedelta(minutes=random.randint(25, 45))
                else:  # walkin
                    actual_arrival = clinic_start + timedelta(minutes=random.randint(0, num_patients * 15))
                    appointment_time = actual_arrival
                
                # Queue dynamics - wait time depends on multiple factors
                queue_position = i + 1
                
                # Base wait calculation with high variability
                if i == 0:
                    # First patient usually quick
                    base_wait = random.randint(0, 8)
                elif i < 3:
                    # Early patients moderate wait
                    base_wait = random.randint(3, 15)
                else:
                    # Later patients more variable
                    base_wait = queue_position * random.randint(2, 10)
                
                # Add random factors
                random_factors = [
                    random.randint(-8, 12),  # Doctor running ahead/behind
                    random.randint(-5, 8) if random.random() < 0.3 else 0,  # Emergency interruption
                    random.randint(-3, 5) if random.random() < 0.4 else 0,  # Patient complexity
                ]
                
                total_wait = int(base_wait + sum(random_factors) * doctor_speed_factor)
                total_wait = max(0, total_wait)  # No negative waits
                
                consultation_start = actual_arrival + timedelta(minutes=total_wait)
                
                # Consultation duration varies significantly
                consultation_duration = random.choices(
                    [3, 5, 7, 10, 12, 15, 18, 20, 25, 30, 35, 40],
                    weights=[0.05, 0.10, 0.15, 0.20, 0.15, 0.12, 0.08, 0.06, 0.04, 0.03, 0.01, 0.01]
                )[0]
                
                completed_at = consultation_start + timedelta(minutes=consultation_duration)
                
                # Create token (don't store predicted_waiting_time - let model learn)
                try:
                    token = Token.objects.create(
                        patient=patient,
                        doctor=doctor,
                        token_number=f"TRAIN{token_counter:05d}",
                        status='Completed',
                        appointment_time=appointment_time,
                        consultation_start_time=consultation_start,
                        completed_at=completed_at
                    )
                    # Update created_at to bypass auto_now_add
                    Token.objects.filter(id=token.id).update(created_at=actual_arrival)
                    tokens_created += 1
                    token_counter += 1
                except Exception as e:
                    token_counter += 1
                    continue
    
    print(f"Created {tokens_created} realistic training tokens")
    
    # Show distribution
    completed_tokens = list(Token.objects.filter(status='Completed'))
    
    # Calculate actual wait times from timestamps
    wait_times = []
    for t in completed_tokens:
        if t.created_at and t.consultation_start_time:
            wait_min = (t.consultation_start_time - t.created_at).total_seconds() / 60
            wait_times.append(max(0, wait_min))
    
    short = sum(1 for w in wait_times if w <= 10)
    medium = sum(1 for w in wait_times if 10 < w <= 20)
    long = sum(1 for w in wait_times if w > 20)
    
    if wait_times:
        avg_wait = sum(wait_times) / len(wait_times)
        min_wait = min(wait_times)
        max_wait = max(wait_times)
        
        print(f"\nDistribution:")
        print(f"  Short (0-10 min): {short}")
        print(f"  Medium (11-20 min): {medium}")
        print(f"  Long (21+ min): {long}")
        print(f"  Total: {tokens_created}")
        print(f"\nWait Time Stats:")
        print(f"  Average: {avg_wait:.1f} min")
        print(f"  Range: {min_wait:.0f}-{max_wait:.0f} min")

if __name__ == '__main__':
    generate_realistic_training_data()
