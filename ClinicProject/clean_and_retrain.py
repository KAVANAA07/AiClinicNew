import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token
from django.utils import timezone

print("=== CLEANING DATABASE ===")
print(f"Total tokens before: {Token.objects.count()}")

# Delete all tokens (they're all bad quality - all 'Completed' with weird timestamps)
Token.objects.all().delete()

print(f"Total tokens after cleanup: {Token.objects.count()}")
print("\n=== DATABASE CLEANED ===")
print("\nNow run: python train_improved_model.py")
