from django.core.management.base import BaseCommand
from django_q.tasks import schedule
from django_q.models import Schedule

class Command(BaseCommand):
    help = 'Schedule prescription reminder tasks'

    def handle(self, *args, **options):
        # Remove existing reminder schedules
        Schedule.objects.filter(name='prescription_reminders').delete()
        
        # Schedule reminder check every 5 minutes
        schedule(
            'api.utils.prescription_reminder.send_prescription_reminders',
            name='prescription_reminders',
            schedule_type='I',  # Interval
            minutes=5,  # Every 5 minutes
        )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully scheduled prescription reminders every 5 minutes')
        )