from django.core.management.base import BaseCommand
from api.models import State, District, Clinic, Doctor

class Command(BaseCommand):
    help = 'Check IVR setup and data availability'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('IVR SETUP CHECK'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Check States
        states = State.objects.all()
        self.stdout.write(f'\n1. States: {states.count()}')
        if states.count() == 0:
            self.stdout.write(self.style.ERROR('   ✗ No states found! IVR will say "no clinics configured"'))
            self.stdout.write('   Fix: Add states via Django admin')
        else:
            for state in states:
                self.stdout.write(f'   ✓ {state.name}')
        
        # Check Districts
        districts = District.objects.all()
        self.stdout.write(f'\n2. Districts: {districts.count()}')
        if districts.count() == 0:
            self.stdout.write(self.style.ERROR('   ✗ No districts found!'))
        else:
            for district in districts[:5]:
                self.stdout.write(f'   ✓ {district.name} ({district.state.name})')
        
        # Check Clinics
        clinics = Clinic.objects.all()
        self.stdout.write(f'\n3. Clinics: {clinics.count()}')
        if clinics.count() == 0:
            self.stdout.write(self.style.ERROR('   ✗ No clinics found!'))
        else:
            for clinic in clinics[:5]:
                self.stdout.write(f'   ✓ {clinic.name}')
        
        # Check Doctors
        doctors = Doctor.objects.all()
        self.stdout.write(f'\n4. Doctors: {doctors.count()}')
        if doctors.count() == 0:
            self.stdout.write(self.style.ERROR('   ✗ No doctors found!'))
        else:
            for doctor in doctors[:5]:
                self.stdout.write(f'   ✓ Dr. {doctor.name} - {doctor.specialization}')
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        if states.count() > 0 and districts.count() > 0 and clinics.count() > 0 and doctors.count() > 0:
            self.stdout.write(self.style.SUCCESS('✓ IVR data is configured correctly!'))
            self.stdout.write('\nNext steps:')
            self.stdout.write('1. Start Django: python manage.py runserver')
            self.stdout.write('2. Start ngrok: ngrok http 8000')
            self.stdout.write('3. Update Twilio webhook with ngrok URL')
            self.stdout.write('4. Call your Twilio number')
        else:
            self.stdout.write(self.style.ERROR('✗ IVR data is incomplete!'))
            self.stdout.write('\nFix by adding data via Django admin:')
            self.stdout.write('python manage.py createsuperuser')
            self.stdout.write('python manage.py runserver')
            self.stdout.write('Visit: http://localhost:8000/admin')
        
        self.stdout.write('=' * 60)
