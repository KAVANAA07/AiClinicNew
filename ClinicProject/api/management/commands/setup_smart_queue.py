from django.core.management.base import BaseCommand
from api.smart_queue_analytics import setup_daily_queue_check
from django_q.tasks import schedule
from django_q.models import Schedule

class Command(BaseCommand):
    help = 'Setup smart queue management schedules'

    def handle(self, *args, **options):
        self.stdout.write('Setting up smart queue management...')
        
        # Clear existing schedules
        Schedule.objects.filter(name__startswith='smart_queue_').delete()
        
        # Setup daily queue check at 8 AM
        setup_daily_queue_check()
        
        # Setup real-time queue monitoring every 2 minutes
        schedule(
            'api.smart_queue_analytics.SmartQueueAnalytics.activate_early_arrivals',
            schedule_type='I',  # Minutes
            minutes=2,
            name='smart_queue_monitor'
        )
        
        # Setup analytics update every 5 minutes
        schedule(
            'api.smart_queue_analytics.SmartQueueAnalytics.calculate_actual_wait_times',
            schedule_type='I',  # Minutes
            minutes=5,
            name='smart_queue_analytics'
        )
        
        self.stdout.write(
            self.style.SUCCESS('Smart queue management setup completed!')
        )