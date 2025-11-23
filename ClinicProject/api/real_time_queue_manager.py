from django.utils import timezone
from datetime import timedelta
from .models import Token, Doctor
from .waiting_time_predictor import waiting_time_predictor
from .utils.utils import send_sms_notification
import logging

logger = logging.getLogger(__name__)

class RealTimeQueueManager:
    """Real-time queue management with AI-powered predictions"""
    
    @staticmethod
    def get_live_queue_status(doctor_id):
        """Get real-time queue status for a doctor"""
        today = timezone.now().date()
        now = timezone.now()
        
        # Get all active tokens for today
        active_tokens = Token.objects.filter(
            doctor_id=doctor_id,
            date=today,
            status__in=['waiting', 'confirmed', 'in_consultancy']
        ).order_by('appointment_time', 'created_at')
        
        queue_status = {
            'doctor_id': doctor_id,
            'current_time': now.strftime('%H:%M'),
            'total_waiting': active_tokens.count(),
            'current_patient': None,
            'next_patients': [],
            'estimated_completion_time': None,
            'can_accept_walkins': False
        }
        
        # Find current patient (in consultation)
        current = active_tokens.filter(status='in_consultancy').first()
        if current:
            queue_status['current_patient'] = {
                'token_number': current.token_number,
                'appointment_time': current.appointment_time.strftime('%H:%M') if current.appointment_time else 'Walk-in',
                'consultation_duration': int((now - current.consultation_start_time).total_seconds() / 60) if current.consultation_start_time else 0
            }
        
        # Get next 3 patients
        waiting_tokens = active_tokens.filter(status__in=['waiting', 'confirmed'])[:3]
        for i, token in enumerate(waiting_tokens):
            predicted_wait = RealTimeQueueManager._calculate_real_time_wait(token, i)
            
            queue_status['next_patients'].append({
                'position': i + 1,
                'token_number': token.token_number,
                'appointment_time': token.appointment_time.strftime('%H:%M') if token.appointment_time else 'Walk-in',
                'status': token.status,
                'predicted_wait_minutes': predicted_wait,
                'can_arrive_early': RealTimeQueueManager._can_arrive_early(token)
            })
        
        # Check if can accept walk-ins
        queue_status['can_accept_walkins'] = RealTimeQueueManager._can_accept_walkins(doctor_id)
        
        return queue_status
    
    @staticmethod
    def _calculate_real_time_wait(token, position_in_queue):
        """Calculate real-time wait based on current queue state"""
        now = timezone.now()
        
        # Base calculation: 12 minutes per person ahead + current consultation time
        base_wait = position_in_queue * 12
        
        # Add current consultation remaining time
        current_consultation = Token.objects.filter(
            doctor=token.doctor,
            date=token.date,
            status='in_consultancy'
        ).first()
        
        if current_consultation and current_consultation.consultation_start_time:
            consultation_duration = (now - current_consultation.consultation_start_time).total_seconds() / 60
            # Assume 15 minutes average consultation, subtract elapsed time
            remaining_current = max(0, 15 - consultation_duration)
            base_wait += remaining_current
        
        # If it's an appointment, consider scheduled time
        if token.appointment_time:
            appointment_datetime = timezone.make_aware(
                timezone.datetime.combine(token.date, token.appointment_time)
            )
            time_until_appointment = (appointment_datetime - now).total_seconds() / 60
            
            # If appointment is in future, use the later of calculated wait or time until appointment
            if time_until_appointment > 0:
                base_wait = max(base_wait, time_until_appointment)
        
        return max(5, int(base_wait))
    
    @staticmethod
    def _can_arrive_early(token):
        """Check if patient can arrive early"""
        now = timezone.now()
        
        if not token.appointment_time:
            return False  # Walk-ins can't arrive early
        
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(token.date, token.appointment_time)
        )
        
        # Can arrive early if:
        # 1. Within 30 minutes of appointment time
        # 2. No one currently in consultation with this doctor
        # 3. No confirmed patients ahead
        
        time_until_appointment = (appointment_datetime - now).total_seconds() / 60
        
        if 0 <= time_until_appointment <= 30:
            # Check if doctor is free
            doctor_busy = Token.objects.filter(
                doctor=token.doctor,
                date=token.date,
                status='in_consultancy'
            ).exists()
            
            if not doctor_busy:
                # Check if any confirmed patients are ahead
                earlier_confirmed = Token.objects.filter(
                    doctor=token.doctor,
                    date=token.date,
                    status='confirmed',
                    appointment_time__lt=token.appointment_time
                ).exists()
                
                return not earlier_confirmed
        
        return False
    
    @staticmethod
    def _can_accept_walkins(doctor_id):
        """Check if doctor can accept walk-in patients"""
        today = timezone.now().date()
        now = timezone.now()
        
        # Check current queue length
        current_queue = Token.objects.filter(
            doctor_id=doctor_id,
            date=today,
            status__in=['waiting', 'confirmed', 'in_consultancy']
        ).count()
        
        # Don't accept walk-ins if queue is too long
        if current_queue >= 8:
            return False
        
        # Check if doctor is currently free
        doctor_busy = Token.objects.filter(
            doctor_id=doctor_id,
            date=today,
            status='in_consultancy'
        ).exists()
        
        if doctor_busy:
            return False
        
        # Check if next appointment is more than 20 minutes away
        next_appointment = Token.objects.filter(
            doctor_id=doctor_id,
            date=today,
            status__in=['waiting', 'confirmed'],
            appointment_time__isnull=False
        ).order_by('appointment_time').first()
        
        if next_appointment:
            next_appointment_datetime = timezone.make_aware(
                timezone.datetime.combine(today, next_appointment.appointment_time)
            )
            time_until_next = (next_appointment_datetime - now).total_seconds() / 60
            
            return time_until_next > 20
        
        return True
    
    @staticmethod
    def activate_early_arrival(token_id):
        """Activate early arrival for a specific token"""
        try:
            token = Token.objects.get(id=token_id)
            
            if not RealTimeQueueManager._can_arrive_early(token):
                return False, "Cannot arrive early at this time"
            
            # Update token status
            token.status = 'confirmed'
            token.arrival_confirmed_at = timezone.now()
            token.save()
            
            # Send notification
            if token.patient.phone_number:
                message = f"You can now arrive early! Dr. {token.doctor.name} is ready to see you."
                send_sms_notification(token.patient.phone_number, message)
            
            # Notify other patients about queue movement
            RealTimeQueueManager._notify_queue_update(token.doctor.id)
            
            return True, "Early arrival activated"
            
        except Token.DoesNotExist:
            return False, "Token not found"
        except Exception as e:
            logger.error(f"Failed to activate early arrival: {e}")
            return False, str(e)
    
    @staticmethod
    def _notify_queue_update(doctor_id):
        """Notify other patients about queue updates"""
        today = timezone.now().date()
        
        waiting_patients = Token.objects.filter(
            doctor_id=doctor_id,
            date=today,
            status__in=['waiting', 'confirmed']
        ).order_by('appointment_time')[:3]
        
        for i, token in enumerate(waiting_patients):
            if token.patient.phone_number:
                if i == 0:
                    message = f"You're next! Dr. {token.doctor.name} will see you shortly."
                else:
                    estimated_wait = (i + 1) * 10
                    message = f"Queue update: You're #{i+1} for Dr. {token.doctor.name}. Estimated wait: {estimated_wait} min."
                
                try:
                    send_sms_notification(token.patient.phone_number, message)
                except Exception as e:
                    logger.error(f"Failed to send queue update SMS: {e}")
    
    @staticmethod
    def get_clinic_overview(clinic_id):
        """Get real-time overview of entire clinic"""
        today = timezone.now().date()
        
        doctors = Doctor.objects.filter(clinic_id=clinic_id)
        clinic_overview = {
            'clinic_id': clinic_id,
            'total_patients_today': 0,
            'total_waiting': 0,
            'total_completed': 0,
            'doctors_status': [],
            'can_accept_walkins': False
        }
        
        total_queue_length = 0
        
        for doctor in doctors:
            doctor_status = RealTimeQueueManager.get_live_queue_status(doctor.id)
            
            # Get doctor's stats for today
            doctor_tokens = Token.objects.filter(
                doctor=doctor,
                date=today
            )
            
            completed_today = doctor_tokens.filter(status='completed').count()
            waiting_count = doctor_tokens.filter(status__in=['waiting', 'confirmed']).count()
            
            clinic_overview['total_patients_today'] += doctor_tokens.count()
            clinic_overview['total_waiting'] += waiting_count
            clinic_overview['total_completed'] += completed_today
            
            total_queue_length += waiting_count
            
            clinic_overview['doctors_status'].append({
                'doctor_id': doctor.id,
                'doctor_name': doctor.name,
                'specialization': doctor.specialization,
                'patients_today': doctor_tokens.count(),
                'completed_today': completed_today,
                'current_waiting': waiting_count,
                'status': 'busy' if doctor_status['current_patient'] else 'available',
                'can_accept_walkins': doctor_status['can_accept_walkins']
            })
        
        # Clinic can accept walk-ins if any doctor can
        clinic_overview['can_accept_walkins'] = any(
            doc['can_accept_walkins'] for doc in clinic_overview['doctors_status']
        )
        
        return clinic_overview