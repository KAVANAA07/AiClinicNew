#!/usr/bin/env python
"""
Check if GPS confirmation actually worked despite error message
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from api.models import Token
from django.utils import timezone

def check_recent_tokens():
    """Check recent tokens to see if any were confirmed"""
    today = timezone.now().date()
    recent_tokens = Token.objects.filter(date=today).order_by('-created_at')[:5]
    
    print("=== Recent Tokens ===")
    for token in recent_tokens:
        print(f"Token {token.id}:")
        print(f"  Patient: {token.patient.name}")
        print(f"  Status: {token.status}")
        print(f"  Created: {token.created_at}")
        print(f"  Confirmed: {token.arrival_confirmed_at}")
        print(f"  Distance: {token.distance_km}km")
        print()

if __name__ == "__main__":
    check_recent_tokens()