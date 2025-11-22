import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from api.models import Patient
User = get_user_model()
uname = 'testuser_ci'
pw = 'TestPass123!'
phone = '+911234567890'
if not User.objects.filter(username=uname).exists():
    u = User.objects.create_user(username=uname, password=pw)
    print('created user', u.username)
else:
    u = User.objects.get(username=uname)
    print('user exists', u.username)

if not Patient.objects.filter(phone_number=phone).exists():
    try:
        Patient.objects.create(user=u, name='Test User', age=30, phone_number=phone)
        print('patient created')
    except Exception as e:
        print('patient create error', e)
else:
    print('patient exists')
