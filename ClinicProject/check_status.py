import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token
from django.db.models import Count

status_counts = Token.objects.values('status').annotate(count=Count('id')).order_by('-count')
print('=== STATUS VALUES IN DATABASE ===')
for s in status_counts:
    print(f"Status: '{s['status']}' | Count: {s['count']}")

print('\n=== SAMPLE TOKENS ===')
for token in Token.objects.all()[:5]:
    print(f"Token {token.id}: status='{token.status}' (type: {type(token.status).__name__})")
