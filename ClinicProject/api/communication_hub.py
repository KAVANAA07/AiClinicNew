from django.utils import timezone
from datetime import timedelta
from .models import Token, Patient
from .utils.utils import send_sms_notification
from django_q.tasks import async_task, schedule
import logging

logger = logging.getLogger(__name__)

class CommunicationHub:
    """Enhanced patient communication system"""
    
    @staticmethod
    def send_smart_notifications():
        """Send intelligent notifications based on queue status"""
        today = timezone.now().date()
        now = timezone.now()
        
        # Get all active tokens for today
        active_tokens = Token.objects.filter(
            date=today,
            status__in=['waiting', 'confirmed']
        ).select_related('patient', 'doctor', 'clinic')
        
        notifications_sent = 0
        
        for token in active_tokens:
            try:
                notification_sent = CommunicationHub._process_token_notification(token, now)
                if notification_sent:
                    notifications_sent += 1
            except Exception as e:
                logger.error(f"Failed to process notification for token {token.id}: {e}")
        
        return {"notifications_sent": notifications_sent}
    
    @staticmethod
    def _process_token_notification(token, current_time):
        """Process individual token for notifications"""
        if not token.patient.phone_number:
            return False
        
        # Calculate waiting time
        wait_minutes = (current_time - token.created_at).total_seconds() / 60
        
        # Appointment reminders (15 minutes before)
        if token.appointment_time:
            appointment_datetime = timezone.datetime.combine(token.date, token.appointment_time)
            appointment_datetime = timezone.make_aware(appointment_datetime)
            time_to_appointment = (appointment_datetime - current_time).total_seconds() / 60
            
            if 10 <= time_to_appointment <= 20 and token.status == 'waiting':
                message = (f"Reminder: Your appointment with Dr. {token.doctor.name} "
                          f"is in {int(time_to_appointment)} minutes. Please arrive soon.")
                CommunicationHub._send_notification(token.patient.phone_number, message, 'appointment_reminder')
                return True
        
        # Long wait notifications (every 30 minutes after 1 hour)
        if wait_minutes > 60 and int(wait_minutes) % 30 == 0:
            queue_position = CommunicationHub._get_queue_position(token)
            estimated_wait = CommunicationHub._estimate_remaining_wait(token)
            
            message = (f"Update: You are #{queue_position} in queue for Dr. {token.doctor.name}. "
                      f"Estimated wait: {estimated_wait} minutes. Reply CANCEL to cancel.")
            CommunicationHub._send_notification(token.patient.phone_number, message, 'wait_update')
            return True
        
        # Ready for consultation (when patient is next)
        if CommunicationHub._is_patient_next(token):
            message = (f"You're next! Please proceed to Dr. {token.doctor.name}'s "
                      f"consultation room. Token: {token.token_number}")
            CommunicationHub._send_notification(token.patient.phone_number, message, 'ready_for_consultation')
            return True
        
        return False
    
    @staticmethod
    def _get_queue_position(token):
        """Get current queue position for a token"""
        if token.appointment_time:
            # For scheduled appointments, count appointments before this time
            earlier_tokens = Token.objects.filter(
                doctor=token.doctor,
                date=token.date,
                appointment_time__lt=token.appointment_time,
                status__in=['waiting', 'confirmed']
            ).count()
        else:
            # For walk-ins, count by creation time
            earlier_tokens = Token.objects.filter(
                doctor=token.doctor,
                date=token.date,
                created_at__lt=token.created_at,
                status__in=['waiting', 'confirmed']
            ).count()
        
        return earlier_tokens + 1
    
    @staticmethod
    def _estimate_remaining_wait(token):
        """Estimate remaining wait time for a token"""
        try:
            from .waiting_time_predictor import waiting_time_predictor
            predicted_wait = waiting_time_predictor.predict_waiting_time(
                token.doctor.id,
                for_appointment_time=token.appointment_time
            )
            return predicted_wait or 15
        except:
            # Fallback calculation
            queue_position = CommunicationHub._get_queue_position(token)
            return queue_position * 10  # Assume 10 minutes per patient
    
    @staticmethod
    def _is_patient_next(token):
        """Check if patient is next in queue"""
        queue_position = CommunicationHub._get_queue_position(token)
        return queue_position == 1
    
    @staticmethod
    def _send_notification(phone_number, message, notification_type):
        """Send notification with logging"""
        try:
            send_sms_notification(phone_number, message)
            logger.info(f"Sent {notification_type} notification to {phone_number}")
        except Exception as e:
            logger.error(f"Failed to send {notification_type} notification to {phone_number}: {e}")
    
    @staticmethod
    def send_bulk_announcement(clinic_id, message, target_group='all'):
        """Send bulk announcements to patients"""
        today = timezone.now().date()
        
        # Define target groups
        if target_group == 'waiting':
            tokens = Token.objects.filter(
                clinic_id=clinic_id,
                date=today,
                status__in=['waiting', 'confirmed']
            )
        elif target_group == 'today':
            tokens = Token.objects.filter(
                clinic_id=clinic_id,
                date=today
            ).exclude(status__in=['cancelled', 'completed'])
        else:  # all
            tokens = Token.objects.filter(
                clinic_id=clinic_id,
                date=today
            )
        
        sent_count = 0
        phone_numbers = set()  # Avoid duplicate messages
        
        for token in tokens:
            if token.patient.phone_number and token.patient.phone_number not in phone_numbers:
                try:
                    send_sms_notification(token.patient.phone_number, message)
                    phone_numbers.add(token.patient.phone_number)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send bulk message to {token.patient.phone_number}: {e}")
        
        return {"messages_sent": sent_count, "target_group": target_group}
    
    @staticmethod
    def setup_automated_notifications():
        """Setup automated notification schedules"""
        from django_q.models import Schedule
        
        # Clear existing notification schedules
        Schedule.objects.filter(name__startswith='auto_notification_').delete()
        
        # Schedule smart notifications every 5 minutes during clinic hours
        schedule(
            'api.communication_hub.CommunicationHub.send_smart_notifications',
            schedule_type='I',  # Minutes
            minutes=5,
            name='auto_notification_smart'
        )
        
        # Schedule daily summary at end of day
        schedule(
            'api.communication_hub.CommunicationHub.send_daily_summary',
            schedule_type='D',  # Daily
            name='auto_notification_daily_summary'
        )
        
        logger.info("Automated notification schedules setup completed")
    
    @staticmethod
    def send_daily_summary():
        """Send daily summary to clinic staff"""
        # This would send summary reports to clinic administrators
        # Implementation depends on your specific requirements
        pass
    
    @staticmethod
    def get_communication_analytics(clinic_id, days=7):
        """Get communication analytics for the clinic"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # This would analyze SMS delivery rates, response rates, etc.
        # Implementation depends on your SMS provider's analytics API
        
        return {
            "period": f"{start_date} to {end_date}",
            "total_notifications": "Analytics not implemented",
            "delivery_rate": "95%",  # Placeholder
            "response_rate": "12%"   # Placeholder
        }