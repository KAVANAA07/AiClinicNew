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

def generate_excellent_training_data():
    """Generate high-quality data with clear patterns for excellent model performance"""
    
    doctors = list(Doctor.objects.all()[:5])
    patients = list(Patient.objects.all())
    
    if not doctors or not patients:
        print("Need doctors and patients in database")
        return
    
    Token.objects.all().delete()
    print("Cleared all existing tokens")
    
    start_date = timezone.now() - timedelta(days=90)
    tokens_created = 0
    token_counter = 0
    
    for day in range(90):
        current_date = start_date + timedelta(days=day)
        
        # Skip weekends
        if current_date.weekday() >= 5:
            continue
        
        for doctor in doctors:
            # Consistent patient load
            num_patients = random.randint(12, 16)
            clinic_start = current_date.replace(hour=9, minute=0, second=0)
            
            for i in range(num_patients):
                patient = random.choice(patients)
                
                # Regular 15-minute appointment slots
                appointment_time = clinic_start + timedelta(minutes=i * 15, seconds=token_counter)
                
                # Realistic arrival patterns
                arrival_minutes = random.choices(
                    [-10, -5, 0, 5, 10],
                    weights=[0.15, 0.25, 0.35, 0.20, 0.05]
                )[0]
                actual_arrival = appointment_time + timedelta(minutes=arrival_minutes)
                
                # Wait time based on clear patterns
                queue_position = i + 1
                hour = actual_arrival.hour
                
                # Pattern 1: Early morning = shorter waits
                if hour < 10:
                    base_wait = random.randint(2, 8)
                # Pattern 2: Mid-morning = medium waits
                elif hour < 12:
                    base_wait = random.randint(8, 18)
                # Pattern 3: Afternoon = longer waits
                else:
                    base_wait = random.randint(15, 30)
                
                # Pattern 4: Queue position impact (predictable)
                if queue_position <= 3:
                    wait_time = base_wait + random.randint(0, 3)
                elif queue_position <= 8:
                    wait_time = base_wait + random.randint(3, 8)
                else:
                    wait_time = base_wait + random.randint(8, 15)
                
                # Pattern 5: Day of week impact
                if current_date.weekday() == 0:  # Monday busier
                    wait_time += random.randint(3, 8)
                elif current_date.weekday() == 4:  # Friday lighter
                    wait_time -= random.randint(2, 5)
                
                wait_time = max(1, min(60, wait_time))  # Keep in reasonable range
                
                consultation_start = actual_arrival + timedelta(minutes=wait_time)
                
                # Consistent consultation duration
                consultation_duration = random.choices(
                    [8, 10, 12, 15],
                    weights=[0.25, 0.35, 0.25, 0.15]
                )[0]
                
                completed_at = consultation_start + timedelta(minutes=consultation_duration)
                
                # Create token
                try:
                    token = Token.objects.create(
                        patient=patient,
                        doctor=doctor,
                        token_number=f"EXCEL{token_counter:05d}",
                        status='Completed',
                        appointment_time=appointment_time,
                        consultation_start_time=consultation_start,
                        completed_at=completed_at
                    )
                    Token.objects.filter(id=token.id).update(created_at=actual_arrival)
                    tokens_created += 1
                    token_counter += 1
                except Exception:
                    token_counter += 1
                    continue
    
    print(f"Created {tokens_created} high-quality training tokens")
    
    # Show distribution
    completed_tokens = list(Token.objects.filter(status='Completed'))
    
    wait_times = []
    for t in completed_tokens:
        if t.created_at and t.consultation_start_time:
            wait_min = (t.consultation_start_time - t.created_at).total_seconds() / 60
            wait_times.append(max(0, wait_min))
    
    short = sum(1 for w in wait_times if w <= 15)
    medium = sum(1 for w in wait_times if 15 < w <= 30)
    long = sum(1 for w in wait_times if w > 30)
    
    if wait_times:
        avg_wait = sum(wait_times) / len(wait_times)
        min_wait = min(wait_times)
        max_wait = max(wait_times)
        
        print(f"\nDistribution:")
        print(f"  Short (0-15 min): {short} ({short/len(wait_times)*100:.1f}%)")
        print(f"  Medium (16-30 min): {medium} ({medium/len(wait_times)*100:.1f}%)")
        print(f"  Long (31+ min): {long} ({long/len(wait_times)*100:.1f}%)")
        print(f"  Total: {tokens_created}")
        print(f"\nWait Time Stats:")
        print(f"  Average: {avg_wait:.1f} min")
        print(f"  Range: {min_wait:.0f}-{max_wait:.0f} min")

if __name__ == '__main__':
    generate_excellent_training_data()
