from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models import PrescriptionItem, PrescriptionReminder, Consultation
from api.utils.prescription_reminder import send_prescription_reminders

class Command(BaseCommand):
    help = 'Check and display prescription reminder status'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('PRESCRIPTION REMINDER STATUS'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        now = timezone.now()
        today = now.date()
        
        # Get active prescriptions
        active_prescriptions = PrescriptionItem.objects.filter(
            consultation__date__gte=today - timedelta(days=30)
        )
        
        self.stdout.write(f'\nTotal prescriptions (last 30 days): {active_prescriptions.count()}')
        
        # Show active prescriptions
        active_count = 0
        for prescription in active_prescriptions:
            consultation_date = prescription.consultation.date
            if hasattr(consultation_date, 'date'):
                prescription_start = consultation_date.date()
            else:
                prescription_start = consultation_date
            prescription_end = prescription_start + timedelta(days=prescription.duration_days)
            
            if today <= prescription_end:
                active_count += 1
                patient = prescription.consultation.patient
                self.stdout.write(f'\n  ✓ {prescription.medicine_name} - {prescription.dosage}')
                self.stdout.write(f'    Patient: {patient.name} ({patient.phone_number})')
                self.stdout.write(f'    Duration: {prescription_start} to {prescription_end}')
                self.stdout.write(f'    Timings: M:{prescription.timing_morning} A:{prescription.timing_afternoon} E:{prescription.timing_evening}')
        
        self.stdout.write(f'\nActive prescriptions: {active_count}')
        
        # Show reminders sent today
        todays_reminders = PrescriptionReminder.objects.filter(sent_date=today)
        self.stdout.write(f'\nReminders sent today: {todays_reminders.count()}')
        
        for reminder in todays_reminders:
            self.stdout.write(f'  - {reminder.prescription.medicine_name} at {reminder.reminder_time}')
        
        # Test sending reminders
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('Testing reminder sending...')
        result = send_prescription_reminders()
        self.stdout.write(self.style.SUCCESS(f'Result: {result}'))
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
