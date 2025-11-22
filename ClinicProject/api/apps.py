from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        # Import here to avoid circular imports
        from django_q.models import Schedule
        
        # Auto-setup the missed appointment checker if it doesn't exist
        schedule_name = 'check_missed_appointments'
        if not Schedule.objects.filter(name=schedule_name).exists():
            try:
                Schedule.objects.create(
                    name=schedule_name,
                    func='api.tasks.check_and_cancel_missed_slots',
                    schedule_type=Schedule.MINUTES,
                    minutes=5,
                    repeats=-1  # Run indefinitely
                )
                print(f'✓ Created Django-Q schedule: {schedule_name} (every 5 minutes)')
            except Exception as e:
                print(f'⚠ Could not create schedule {schedule_name}: {e}')
