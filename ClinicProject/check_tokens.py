import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token, Patient
from django.utils import timezone

today = timezone.now().date()

print('=== ALL TOKENS ===')
tokens = Token.objects.all()
print(f'Total tokens: {tokens.count()}')
for t in tokens:
    print(f'Token {t.id}: Patient={t.patient.name}, Phone={t.patient.phone_number}, Date={t.date}, Status={t.status}, Appt={t.appointment_time}')

print('\n=== ACTIVE TOKENS (not completed/cancelled) ===')
active = Token.objects.exclude(status__in=['completed', 'cancelled'])
print(f'Active tokens: {active.count()}')
for t in active:
    print(f'Token {t.id}: Patient={t.patient.name}, Phone={t.patient.phone_number}, Date={t.date}, Status={t.status}')

print('\n=== TODAY OR FUTURE ACTIVE TOKENS ===')
future_active = Token.objects.filter(
    date__gte=today,
    status__in=['waiting', 'confirmed']
)
print(f'Future active tokens: {future_active.count()}')
for t in future_active:
    print(f'Token {t.id}: Patient={t.patient.name}, Phone={t.patient.phone_number}, Date={t.date}, Status={t.status}')

print('\n=== ALL PATIENTS ===')
patients = Patient.objects.all()
for p in patients:
    print(f'Patient {p.id}: Name={p.name}, Phone={p.phone_number}, User={p.user_id}')
