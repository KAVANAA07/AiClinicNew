from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta, time
from .models import Token, Doctor
from .utils.utils import send_sms_notification
from django_q.tasks import async_task, schedule
import logging

logger = logging.getLogger(__name__)

class SmartQueueAnalytics:
    """Real-time queue analytics and smart management"""
    
    @staticmethod
    def calculate_actual_wait_times():
        """Calculate actual wait times for completed tokens today"""
        today = timezone.now().date()
        completed_tokens = Token.objects.filter(
            date=today,
            status='completed',
            completed_at__isnull=False
        )
        
        analytics = {
            'total_completed': completed_tokens.count(),
            'avg_wait_minutes': 0,
            'doctor_performance': {},
            'hourly_completion_rate': {}
        }
        
        if completed_tokens.exists():
            total_wait = 0
            for token in completed_tokens:
                wait_time = (token.completed_at - token.created_at).total_seconds() / 60
                total_wait += wait_time
                
                # Doctor performance
                doctor_name = token.doctor.name
                if doctor_name not in analytics['doctor_performance']:
                    analytics['doctor_performance'][doctor_name] = {
                        'total_patients': 0,
                        'total_wait_time': 0,
                        'avg_wait_time': 0
                    }
                
                analytics['doctor_performance'][doctor_name]['total_patients'] += 1
                analytics['doctor_performance'][doctor_name]['total_wait_time'] += wait_time
            
            analytics['avg_wait_minutes'] = round(total_wait / completed_tokens.count(), 1)
            
            # Calculate doctor averages
            for doctor_data in analytics['doctor_performance'].values():
                if doctor_data['total_patients'] > 0:
                    doctor_data['avg_wait_time'] = round(
                        doctor_data['total_wait_time'] / doctor_data['total_patients'], 1
                    )
        
        return analytics
    
    @staticmethod
    def detect_early_slots():
        """Detect slots that finished early and can be filled"""
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        early_opportunities = []
        
        # Find completed tokens that finished before their scheduled time
        completed_early = Token.objects.filter(
            date=today,
            status='completed',
            appointment_time__isnull=False,
            completed_at__isnull=False
        )
        
        for token in completed_early:
            scheduled_datetime = timezone.make_aware(
                timezone.datetime.combine(today, token.appointment_time)
            )
            
            # If completed more than 10 minutes early
            if token.completed_at < (scheduled_datetime - timedelta(minutes=10)):
                early_opportunities.append({
                    'doctor_id': token.doctor.id,
                    'doctor_name': token.doctor.name,
                    'original_time': token.appointment_time,
                    'completed_at': token.completed_at,
                    'minutes_early': int((scheduled_datetime - token.completed_at).total_seconds() / 60)
                })
        
        return early_opportunities
    
    @staticmethod
    def activate_early_arrivals():
        """Activate early arrival for next patients when slots open up"""
        now = timezone.now()
        today = now.date()
        
        activated_count = 0
        
        for doctor in Doctor.objects.all():
            # Get next waiting patient for this doctor
            next_patient = Token.objects.filter(
                doctor=doctor,
                date=today,
                status='waiting',
                appointment_time__isnull=False
            ).order_by('appointment_time').first()
            
            if not next_patient:
                continue
            
            # Check if doctor is currently free (no in_consultancy tokens)
            doctor_busy = Token.objects.filter(
                doctor=doctor,
                date=today,
                status='in_consultancy'
            ).exists()
            
            if not doctor_busy:
                # Check if it's within 30 minutes of appointment time
                appointment_datetime = timezone.make_aware(
                    timezone.datetime.combine(today, next_patient.appointment_time)
                )
                
                time_until_appointment = (appointment_datetime - now).total_seconds() / 60
                
                if 0 <= time_until_appointment <= 30:
                    # DO NOT auto-confirm - only send notification
                    # Patient must still manually confirm arrival with GPS
                    
                    # Send notification - patient still needs GPS confirmation
                    if next_patient.patient.phone_number:
                        message = f"Good news! Dr. {doctor.name} is ready early. You can arrive now for your {next_patient.appointment_time.strftime('%I:%M %p')} appointment. Please confirm arrival with GPS when you reach the clinic."
                        try:
                            send_sms_notification(next_patient.patient.phone_number, message)
                            activated_count += 1
                            logger.info(f"Early arrival notification sent for token {next_patient.id} - GPS confirmation still required")
                        except Exception as e:
                            logger.error(f"Failed to send early arrival SMS: {e}")
        
        return activated_count  # Note: This counts notifications sent, not auto-confirmations

@receiver(post_save, sender=Token)
def handle_token_completion(sender, instance, **kwargs):
    """Handle token completion and trigger smart queue actions"""
    if instance.status == 'completed' and instance.completed_at:
        # Trigger early arrival activation
        async_task('api.smart_queue_analytics.SmartQueueAnalytics.activate_early_arrivals')
        
        # Notify next patients about faster queue
        async_task('api.smart_queue_analytics.notify_queue_progress', instance.doctor.id)

def notify_queue_progress(doctor_id):
    """Notify waiting patients that queue is moving faster"""
    today = timezone.now().date()
    
    # Get all waiting patients for this doctor
    waiting_patients = Token.objects.filter(
        doctor_id=doctor_id,
        date=today,
        status__in=['waiting', 'confirmed']
    ).order_by('appointment_time')
    
    if waiting_patients.count() > 1:
        # Notify next 2-3 patients
        for i, token in enumerate(waiting_patients[:3]):
            if token.patient.phone_number:
                if i == 0:
                    message = f"You're next! Dr. {token.doctor.name} will see you shortly."
                else:
                    message = f"Queue moving fast! You're #{i+1} for Dr. {token.doctor.name}. Estimated wait: {(i+1)*10} minutes."
                
                try:
                    send_sms_notification(token.patient.phone_number, message)
                except Exception as e:
                    logger.error(f"Failed to send queue progress SMS: {e}")

def setup_daily_queue_check():
    """Setup daily morning queue optimization"""
    from django_q.models import Schedule
    
    # Clear existing schedules
    Schedule.objects.filter(name='daily_queue_check').delete()
    
    # Schedule daily at 8 AM
    schedule(
        'api.smart_queue_analytics.daily_queue_optimization',
        schedule_type='D',  # Daily
        name='daily_queue_check'
    )
    
    logger.info("Daily queue check scheduled for 8 AM")

def daily_queue_optimization():
    """Daily morning optimization of all tokens"""
    today = timezone.now().date()
    
    # Get all today's tokens
    todays_tokens = Token.objects.filter(date=today).exclude(status__in=['completed', 'cancelled'])
    
    optimizations = {
        'tokens_checked': todays_tokens.count(),
        'early_activations': 0,
        'no_shows_detected': 0,
        'walk_in_slots_created': 0
    }
    
    for doctor in Doctor.objects.all():
        doctor_tokens = todays_tokens.filter(doctor=doctor).order_by('appointment_time')
        
        for i, token in enumerate(doctor_tokens):
            if token.appointment_time:
                # Check for gaps (no-shows or early completions)
                if i > 0:
                    prev_token = doctor_tokens[i-1]
                    if prev_token.status in ['skipped', 'cancelled']:
                        # Previous slot is empty - can move this patient earlier
                        optimizations['early_activations'] += 1
                        
                        # Notify patient they can come early
                        if token.patient.phone_number:
                            message = f"Good news! You can come early for your appointment with Dr. {doctor.name}. Previous slot is available."
                            try:
                                send_sms_notification(token.patient.phone_number, message)
                            except Exception as e:
                                logger.error(f"Failed to send early notification: {e}")
    
    logger.info(f"Daily optimization completed: {optimizations}")
    return optimizations