from api.models import Patient, Token
from django.utils import timezone

# Check tokens for both patients
patient_ids = [7, 29]  # jasmith and IVR Patient 2080
today = timezone.now().date()

print(f'Today: {today}')
print('All tokens for these patients:')

for patient_id in patient_ids:
    tokens = Token.objects.filter(patient_id=patient_id)
    print(f'Patient {patient_id} tokens:')
    for t in tokens:
        print(f'  Token {t.id}: {t.date} {t.appointment_time} - {t.status}')

print('\nActive tokens (not completed/cancelled):')
active_tokens = Token.objects.filter(
    patient_id__in=patient_ids
).exclude(status__in=['completed', 'cancelled'])

for t in active_tokens:
    print(f'  Token {t.id}: {t.date} {t.appointment_time} - {t.status}')