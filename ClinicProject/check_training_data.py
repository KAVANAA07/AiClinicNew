#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token
from datetime import timedelta
from django.utils import timezone

def check_training_data():
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    print(f"Checking training data from {start_date} to {end_date}")
    
    # Check all completed tokens
    completed_tokens = Token.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lt=end_date,
        status='completed'
    )
    print(f"Found {completed_tokens.count()} completed tokens")
    
    # Check tokens with consultation_start_time
    tokens_with_start_time = completed_tokens.filter(consultation_start_time__isnull=False)
    print(f"Found {tokens_with_start_time.count()} tokens with consultation_start_time")
    
    # Show sample tokens
    print("\nSample tokens:")
    for token in tokens_with_start_time[:5]:
        waiting_time = None
        if token.consultation_start_time:
            waiting_time = (token.consultation_start_time - token.created_at).total_seconds() / 60
        print(f"Token {token.id}: created={token.created_at}, consultation_start={token.consultation_start_time}, waiting_time={waiting_time:.1f} min")
    
    return tokens_with_start_time.count()

if __name__ == "__main__":
    count = check_training_data()
    print(f"\nTraining data available: {count} tokens")
    if count >= 10:
        print("Sufficient data for training!")
    else:
        print("Need more training data (minimum 10 tokens)")