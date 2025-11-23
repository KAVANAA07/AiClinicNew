#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.tasks_ml import setup_ml_schedules

if __name__ == "__main__":
    print("Setting up ML schedules...")
    result = setup_ml_schedules()
    print(f"Result: {result}")
    print("ML schedules setup completed!")