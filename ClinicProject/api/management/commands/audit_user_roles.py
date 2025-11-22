from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import Patient, Doctor, Receptionist

User = get_user_model()


class Command(BaseCommand):
    help = 'Audit users for role/profile conflicts and optionally fix is_staff flags for patient accounts.'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', help='Clear is_staff/is_superuser for conflicted users')

    def handle(self, *args, **options):
        fix = options.get('fix', False)
        conflicted = []
        for user in User.objects.all():
            has_patient = Patient.objects.filter(user=user).exists()
            has_doctor = Doctor.objects.filter(user=user).exists()
            has_receptionist = Receptionist.objects.filter(user=user).exists()
            if has_patient and (user.is_staff or has_doctor or has_receptionist):
                conflicted.append((user, has_patient, has_doctor, has_receptionist))

        if not conflicted:
            self.stdout.write(self.style.SUCCESS('No user role conflicts detected.'))
            return

        self.stdout.write(self.style.WARNING(f'Found {len(conflicted)} conflicted user(s):'))
        for user, has_patient, has_doctor, has_receptionist in conflicted:
            roles = []
            if user.is_staff: roles.append('is_staff')
            if has_doctor: roles.append('doctor')
            if has_receptionist: roles.append('receptionist')
            self.stdout.write(f'- User id={user.id} username={user.username} roles={roles} patient={has_patient}')
            if fix:
                if user.is_staff or user.is_superuser:
                    user.is_staff = False
                    user.is_superuser = False
                    user.save(update_fields=['is_staff', 'is_superuser'])
                    self.stdout.write(self.style.SUCCESS(f'  Cleared is_staff/is_superuser for {user.username}'))
                else:
                    self.stdout.write(f'  No is_staff/superuser flags to clear for {user.username}')

        if not fix:
            self.stdout.write('\nRun `python manage.py audit_user_roles --fix` to clear is_staff/is_superuser for these users.')
