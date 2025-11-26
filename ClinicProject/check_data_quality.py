import os
import sys
import django

sys.path.append('c:/Users/VITUS/AiClinicNew/ClinicProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token
from django.utils import timezone
from datetime import timedelta

print("="*70)
print("DATA QUALITY CHECK")
print("="*70)

# Check total completed tokens
total_tokens = Token.objects.filter(status='completed').count()
print(f"\nTotal completed consultations: {total_tokens}")

# Check tokens with required fields
valid_tokens = Token.objects.filter(
    status='completed',
    completed_at__isnull=False,
    appointment_time__isnull=False,
    consultation_start_time__isnull=False
).count()
print(f"Valid tokens (with all required fields): {valid_tokens}")

# Check recent data (last 60 days)
recent_date = timezone.now().date() - timedelta(days=60)
recent_tokens = Token.objects.filter(
    status='completed',
    date__gte=recent_date
).count()
print(f"Recent tokens (last 60 days): {recent_tokens}")

# Check data distribution by doctor
from django.db.models import Count
doctor_distribution = Token.objects.filter(
    status='completed'
).values('doctor__name').annotate(count=Count('id')).order_by('-count')

print(f"\nData distribution by doctor:")
for item in doctor_distribution[:5]:
    print(f"   {item['doctor__name']}: {item['count']} consultations")

# Recommendations
print("\n" + "="*70)
print("RECOMMENDATIONS:")
print("="*70)

if total_tokens < 50:
    print("CRITICAL: Need at least 50 completed consultations")
    print("   -> Add more historical data or generate synthetic data")
elif total_tokens < 100:
    print("WARNING: 50-100 samples is minimal")
    print("   -> Collect more data for better accuracy")
else:
    print("Good amount of data available")

if valid_tokens < total_tokens * 0.8:
    print(f"WARNING: Only {valid_tokens}/{total_tokens} have complete data")
    print("   -> Fix missing fields in database")

print("\n" + "="*70)
