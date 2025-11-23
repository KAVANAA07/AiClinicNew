from api.models import Patient, Token

# Check patients with phone +918888888888
patients = Patient.objects.filter(phone_number='+918888888888')
print(f'Found {patients.count()} patients with phone +918888888888')

for p in patients:
    print(f'  Patient {p.id}: {p.name}, User: {p.user}')

# Check tokens
tokens = Token.objects.filter(patient__phone_number='+918888888888')
print(f'Found {tokens.count()} tokens')

for t in tokens:
    print(f'  Token {t.id}: {t.date} {t.appointment_time}, Patient: {t.patient.name}')