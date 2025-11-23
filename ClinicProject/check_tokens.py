from api.models import Patient, Token
from api.views import normalize_phone_number
from django.utils import timezone

# Check for tokens with normalized phone matching
target_phone = '8217612080'
patients = []
for p in Patient.objects.all():
    if normalize_phone_number(p.phone_number) == target_phone:
        patients.append(p)

print(f'Matching patients: {len(patients)}')
for p in patients:
    print(f'  Patient {p.id}: {p.name} ({p.phone_number})')

if patients:
    tokens = Token.objects.filter(
        patient__in=patients, 
        date__gte=timezone.now().date()
    ).exclude(status__in=['completed', 'cancelled'])
    
    print(f'Active tokens: {len(tokens)}')
    for t in tokens:
        print(f'  Token {t.id}: {t.date} {t.appointment_time} - {t.status}')