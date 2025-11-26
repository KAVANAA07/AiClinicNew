from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, time
from api.models import Patient, Doctor, Consultation, PrescriptionItem, Clinic
from api.tasks import send_prescription_reminder_sms
from django_q.tasks import async_task

class Command(BaseCommand):
    help = 'Test prescription reminder functionality'

    def add_arguments(self, parser):
        parser.add_argument('--phone', type=str, help='Phone number to send test SMS')
        parser.add_argument('--immediate', action='store_true', help='Send immediate test SMS')
        parser.add_argument('--schedule', action='store_true', help='Schedule a test reminder')

    def handle(self, *args, **options):
        phone = options.get('phone') or '+1234567890'
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('PRESCRIPTION REMINDER TEST'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Test immediate SMS
        if options.get('immediate'):
            self.stdout.write('\nTesting immediate SMS...')
            message = "TEST: Prescription reminder - Take Paracetamol 500mg"
            try:
                send_prescription_reminder_sms(phone, message)
                self.stdout.write(self.style.SUCCESS(f'✓ SMS sent to {phone}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))
        
        # Test scheduled SMS
        if options.get('schedule'):
            self.stdout.write('\nScheduling test reminder...')
            schedule_time = timezone.now() + timedelta(minutes=2)
            message = f"SCHEDULED TEST: Take medicine at {schedule_time.strftime('%I:%M %p')}"
            try:
                task_id = async_task(
                    'api.tasks.send_prescription_reminder_sms',
                    phone,
                    message,
                    schedule=schedule_time
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Scheduled for {schedule_time.strftime("%I:%M %p")}'))
                self.stdout.write(f'  Task ID: {task_id}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))
        
        # Show usage if no options
        if not options.get('immediate') and not options.get('schedule'):
            self.stdout.write('\nUsage:')
            self.stdout.write('  python manage.py test_prescription_reminders --phone +1234567890 --immediate')
            self.stdout.write('  python manage.py test_prescription_reminders --phone +1234567890 --schedule')
            self.stdout.write('  python manage.py test_prescription_reminders --immediate --schedule')
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
