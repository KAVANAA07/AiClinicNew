from django.utils import timezone
from django.db.models import Avg, Count
from .models import Token, Doctor, Clinic
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ClinicWaitStats:
    """Calculate average wait times for clinics and doctors"""
    
    @staticmethod
    def get_clinic_avg_wait_time(clinic_id):
        """Get average wait time for entire clinic"""
        try:
            tokens = Token.objects.filter(
                doctor__clinic_id=clinic_id,
                status='completed',
                completed_at__isnull=False,
                appointment_time__isnull=False,
                appointment_date__gte=timezone.now().date() - timedelta(days=30)
            )
            
            if not tokens.exists():
                return 15  # Default fallback
            
            total_wait = 0
            count = 0
            
            for token in tokens:
                expected = datetime.combine(token.appointment_date, token.appointment_time)
                actual = token.completed_at
                wait_time = (actual - expected).total_seconds() / 60
                
                if wait_time >= 0:  # Only positive wait times for clinic average
                    total_wait += wait_time
                    count += 1
            
            return int(total_wait / count) if count > 0 else 15
            
        except Exception as e:
            logger.error(f"Error calculating clinic wait time: {e}")
            return 15
    
    @staticmethod
    def get_doctor_avg_wait_time(doctor_id):
        """Get average wait time for specific doctor"""
        try:
            tokens = Token.objects.filter(
                doctor_id=doctor_id,
                status='completed',
                completed_at__isnull=False,
                appointment_time__isnull=False,
                appointment_date__gte=timezone.now().date() - timedelta(days=30)
            )
            
            if not tokens.exists():
                return 12  # Default fallback
            
            total_wait = 0
            count = 0
            
            for token in tokens:
                expected = datetime.combine(token.appointment_date, token.appointment_time)
                actual = token.completed_at
                wait_time = (actual - expected).total_seconds() / 60
                
                if wait_time >= 0:
                    total_wait += wait_time
                    count += 1
            
            return int(total_wait / count) if count > 0 else 12
            
        except Exception as e:
            logger.error(f"Error calculating doctor wait time: {e}")
            return 12
    
    @staticmethod
    def get_doctor_current_workload(doctor_id):
        """Get current workload for doctor today"""
        try:
            today = timezone.now().date()
            
            total_today = Token.objects.filter(
                doctor_id=doctor_id,
                appointment_date=today
            ).count()
            
            completed_today = Token.objects.filter(
                doctor_id=doctor_id,
                appointment_date=today,
                status='completed'
            ).count()
            
            pending_today = Token.objects.filter(
                doctor_id=doctor_id,
                appointment_date=today,
                status__in=['confirmed', 'in_progress']
            ).count()
            
            return {
                'total': total_today,
                'completed': completed_today,
                'pending': pending_today,
                'workload_factor': min(pending_today * 5, 30)  # Max 30 min extra
            }
            
        except Exception as e:
            logger.error(f"Error calculating workload: {e}")
            return {'total': 0, 'completed': 0, 'pending': 0, 'workload_factor': 0}