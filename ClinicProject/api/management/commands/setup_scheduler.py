from django.core.management.base import BaseCommand
from django_q.models import Schedule

class Command(BaseCommand):
    help = 'Setup Django-Q scheduled tasks'

    def handle(self, *args, **options):
        # Check if missed appointment checker already exists
        schedule_name = 'check_missed_appointments'
        
        if Schedule.objects.filter(name=schedule_name).exists():
            self.stdout.write(
                self.style.WARNING(f'Schedule "{schedule_name}" already exists')
            )
        else:
            # Create the schedule to run every 5 minutes
            Schedule.objects.create(
                name=schedule_name,
                func='api.tasks.check_and_cancel_missed_slots',
                schedule_type=Schedule.MINUTES,
                minutes=5,
                repeats=-1  # Run indefinitely
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created schedule "{schedule_name}" to run every 5 minutes')
            )