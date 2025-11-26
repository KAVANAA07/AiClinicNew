"""
Test script for prescription reminder tasks
Run this with: python manage.py shell < test_prescription_reminders.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.utils import timezone
from datetime import datetime, timedelta, time
from api.models import Patient, Doctor, Consultation, PrescriptionItem, Clinic
from api.tasks import send_prescription_reminder_sms
from django_q.tasks import async_task, fetch
from django_q.models import Schedule
import time as time_module

print("=" * 60)
print("PRESCRIPTION REMINDER TEST")
print("=" * 60)

# 1. Check if Django-Q is running
print("\n1. Checking Django-Q cluster status...")
try:
    from django_q.cluster import Cluster
    print("   ✓ Django-Q is available")
    print("   NOTE: Make sure to run 'python manage.py qcluster' in another terminal")
except Exception as e:
    print(f"   ✗ Django-Q error: {e}")

# 2. Get or create test patient
print("\n2. Setting up test patient...")
test_phone = "+1234567890"  # Change this to your test phone number
patient, created = Patient.objects.get_or_create(
    phone_number=test_phone,
    defaults={'name': 'Test Patient', 'age': 30}
)
print(f"   Patient: {patient.name} ({patient.phone_number})")

# 3. Get or create test doctor and clinic
print("\n3. Setting up test doctor...")
clinic = Clinic.objects.first()
if not clinic:
    clinic = Clinic.objects.create(name="Test Clinic", address="123 Test St", city="Test City")
    print(f"   Created clinic: {clinic.name}")

doctor = Doctor.objects.filter(clinic=clinic).first()
if not doctor:
    doctor = Doctor.objects.create(name="Dr. Test", specialization="General", clinic=clinic)
    print(f"   Created doctor: {doctor.name}")
else:
    print(f"   Doctor: {doctor.name}")

# 4. Create test consultation with prescription
print("\n4. Creating test consultation with prescription...")
consultation = Consultation.objects.create(
    patient=patient,
    doctor=doctor,
    notes="Test consultation for prescription reminders"
)
print(f"   Consultation ID: {consultation.id}")

# 5. Create prescription items
print("\n5. Creating prescription items...")
prescription_items = [
    {
        'medicine_name': 'Paracetamol',
        'dosage': '500mg',
        'duration_days': 3,
        'timing_morning': True,
        'timing_afternoon': False,
        'timing_evening': True
    },
    {
        'medicine_name': 'Vitamin C',
        'dosage': '1000mg',
        'duration_days': 2,
        'timing_morning': True,
        'timing_afternoon': True,
        'timing_evening': False
    }
]

for item_data in prescription_items:
    item = PrescriptionItem.objects.create(
        consultation=consultation,
        **item_data
    )
    print(f"   ✓ {item.medicine_name} - {item.dosage} for {item.duration_days} days")

# 6. Test immediate SMS sending
print("\n6. Testing immediate SMS sending...")
test_message = "TEST: This is a prescription reminder test message."
try:
    send_prescription_reminder_sms(test_phone, test_message)
    print(f"   ✓ Immediate SMS sent to {test_phone}")
except Exception as e:
    print(f"   ✗ Failed to send immediate SMS: {e}")

# 7. Schedule future reminders (for testing)
print("\n7. Scheduling test reminders...")
MORNING_TIME = time(8, 0)
AFTERNOON_TIME = time(13, 0)
EVENING_TIME = time(20, 0)

# Schedule a reminder 1 minute from now for testing
test_schedule_time = timezone.now() + timedelta(minutes=1)
test_reminder_message = f"TEST REMINDER: Take Paracetamol - 500mg (scheduled for {test_schedule_time.strftime('%I:%M %p')})"

try:
    task_id = async_task(
        'api.tasks.send_prescription_reminder_sms',
        test_phone,
        test_reminder_message,
        schedule=test_schedule_time
    )
    print(f"   ✓ Scheduled test reminder for {test_schedule_time.strftime('%I:%M %p')}")
    print(f"   Task ID: {task_id}")
except Exception as e:
    print(f"   ✗ Failed to schedule reminder: {e}")

# 8. Check scheduled tasks
print("\n8. Checking scheduled tasks in Django-Q...")
try:
    from django_q.models import Schedule as QSchedule
    scheduled_tasks = QSchedule.objects.all()
    print(f"   Total scheduled tasks: {scheduled_tasks.count()}")
    
    # Show recent tasks
    recent_tasks = scheduled_tasks.order_by('-id')[:5]
    for task in recent_tasks:
        print(f"   - {task.func} | Next run: {task.next_run}")
except Exception as e:
    print(f"   ✗ Error checking scheduled tasks: {e}")

# 9. Check task queue
print("\n9. Checking task queue...")
try:
    from django_q.models import Task
    pending_tasks = Task.objects.filter(success__isnull=True)
    print(f"   Pending tasks: {pending_tasks.count()}")
    
    completed_tasks = Task.objects.filter(success=True).order_by('-stopped')[:5]
    print(f"   Recent completed tasks: {completed_tasks.count()}")
    for task in completed_tasks:
        print(f"   - {task.func} | Completed: {task.stopped}")
except Exception as e:
    print(f"   ✗ Error checking task queue: {e}")

# 10. Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print(f"Patient: {patient.name} ({patient.phone_number})")
print(f"Consultation ID: {consultation.id}")
print(f"Prescription items: {PrescriptionItem.objects.filter(consultation=consultation).count()}")
print(f"Test reminder scheduled for: {test_schedule_time.strftime('%Y-%m-%d %I:%M %p')}")
print("\nNEXT STEPS:")
print("1. Make sure Django-Q cluster is running: python manage.py qcluster")
print("2. Wait 1 minute to receive the test reminder SMS")
print("3. Check Django-Q logs for task execution")
print("4. Check your phone for the test SMS")
print("=" * 60)
