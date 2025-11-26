from django.utils import timezone
from django.db.models import Avg, Count, Q
from .models import Token, Doctor
from .waiting_time_predictor import waiting_time_predictor
import logging
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

class AdvancedWaitPredictor:
    """Advanced wait time prediction combining ML model with real-time flow analysis"""
    
    def __init__(self):
        self.ml_predictor = waiting_time_predictor
    
    def get_predicted_wait_time(self, token_id):
        """Get predicted wait time for a pre-booked token"""
        try:
            token = Token.objects.get(id=token_id)
            
            # Only for pre-booked appointments (created 1+ days ago)
            if not self._is_prebooked_appointment(token):
                return self._get_current_queue_wait_time(token)
            
            # Combine ML prediction with real-time flow analysis
            ml_prediction = self._get_ml_prediction(token)
            flow_adjustment = self._get_realtime_flow_adjustment(token)
            
            # Weighted combination: 60% ML, 40% real-time flow
            final_prediction = (ml_prediction * 0.6) + (flow_adjustment * 0.4)
            
            return max(0, int(final_prediction))
            
        except Exception as e:
            logger.error(f"Error predicting wait time for token {token_id}: {e}")
            return 15  # Default fallback
    
    def _is_prebooked_appointment(self, token):
        """Check if appointment was booked 1+ days in advance"""
        booking_time = token.created_at
        appointment_date = token.date
        
        # Convert to same timezone for comparison
        if booking_time.date() < appointment_date:
            return True
        return False
    
    def _get_ml_prediction(self, token):
        """Get ML model prediction for the token"""
        try:
            prediction = self.ml_predictor.predict_waiting_time(
                doctor_id=token.doctor.id,
                for_appointment_time=token.appointment_time
            )
            return prediction
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return 20  # Fallback
    
    def _get_realtime_flow_adjustment(self, token):
        """Analyze current day flow and adjust prediction"""
        today = timezone.now().date()
        current_time = timezone.now().time()
        
        # Get today's completed consultations up to current time
        todays_completions = Token.objects.filter(
            date=today,
            status='completed',
            completed_at__isnull=False,
            appointment_time__lte=current_time
        )
        
        if not todays_completions.exists():
            return self._get_historical_baseline(token)
        
        # Calculate average delay for today
        total_delay = 0
        count = 0
        
        for completed_token in todays_completions:
            expected_time = datetime.combine(completed_token.date, completed_token.appointment_time)
            actual_time = completed_token.completed_at
            
            # Calculate delay in minutes (ensure both are timezone-aware)
            if expected_time.tzinfo is None:
                expected_time = timezone.make_aware(expected_time)
            delay = (actual_time - expected_time).total_seconds() / 60
            total_delay += delay
            count += 1
        
        if count == 0:
            return self._get_historical_baseline(token)
        
        avg_delay_today = total_delay / count
        
        # Factor in queue position and remaining appointments
        queue_factor = self._calculate_queue_impact(token)
        
        return max(0, avg_delay_today + queue_factor)
    
    def _calculate_queue_impact(self, token):
        """Calculate impact of current queue on wait time"""
        # Count tokens ahead in queue for same doctor
        tokens_ahead = Token.objects.filter(
            doctor=token.doctor,
            date=token.date,
            appointment_time__lt=token.appointment_time,
            status__in=['confirmed', 'in_progress']
        ).count()
        
        # Count current in-progress consultations
        in_progress = Token.objects.filter(
            doctor=token.doctor,
            date=token.date,
            status='in_progress'
        ).count()
        
        # Estimate 15 minutes per consultation + 5 minutes buffer
        queue_impact = (tokens_ahead * 15) + (in_progress * 10)
        
        return queue_impact
    
    def _get_historical_baseline(self, token):
        """Get historical baseline for similar appointments"""
        # Look at same doctor, same time slot, last 30 days
        historical_tokens = Token.objects.filter(
            doctor=token.doctor,
            appointment_time__range=(
                (datetime.combine(timezone.now().date(), token.appointment_time) - timedelta(minutes=30)).time(),
                (datetime.combine(timezone.now().date(), token.appointment_time) + timedelta(minutes=30)).time()
            ),
            date__gte=timezone.now().date() - timedelta(days=30),
            status='completed',
            completed_at__isnull=False
        )
        
        if not historical_tokens.exists():
            return 15  # Default baseline
        
        # Calculate average historical delay
        delays = []
        for hist_token in historical_tokens:
            expected = datetime.combine(hist_token.date, hist_token.appointment_time)
            if expected.tzinfo is None:
                expected = timezone.make_aware(expected)
            actual = hist_token.completed_at
            delay = (actual - expected).total_seconds() / 60
            delays.append(delay)
        
        return max(0, np.mean(delays)) if delays else 15
    
    def _get_current_queue_wait_time(self, token):
        """For same-day appointments, use simple queue-based calculation"""
        if token.status == 'in_consultancy':
            return 0  # Currently being seen
        
        # Count tokens ahead in queue
        from django.db import models
        tokens_ahead = Token.objects.filter(
            doctor=token.doctor,
            date=token.date,
            status__in=['confirmed', 'in_consultancy']
        ).filter(
            models.Q(appointment_time__lt=token.appointment_time) |
            models.Q(appointment_time=token.appointment_time, created_at__lt=token.created_at) |
            models.Q(appointment_time__isnull=True, created_at__lt=token.created_at)
        ).count()
        
        if tokens_ahead == 0:
            return 5  # Next in queue
        
        return min(tokens_ahead * 12, 60)  # Max 60 minutes
    
    def get_live_updates_data(self, doctor_id=None):
        """Get real-time data for dashboard updates"""
        today = timezone.now().date()
        current_time = timezone.now()
        
        # Base query
        query = Q(date=today, status__in=['confirmed', 'in_progress'])
        if doctor_id:
            query &= Q(doctor_id=doctor_id)
        
        upcoming_tokens = Token.objects.filter(query).order_by('appointment_time')
        
        live_data = []
        for token in upcoming_tokens:
            predicted_wait = self.get_predicted_wait_time(token.id)
            
            # Calculate expected completion time
            expected_start = datetime.combine(token.date, token.appointment_time)
            predicted_start = expected_start + timedelta(minutes=predicted_wait)
            
            live_data.append({
                'token_id': token.id,
                'token_number': token.token_number,
                'patient_name': token.patient.name,
                'doctor_name': token.doctor.name,
                'appointment_time': token.appointment_time.strftime('%H:%M'),
                'predicted_wait_minutes': predicted_wait,
                'predicted_start_time': predicted_start.strftime('%H:%M'),
                'status': token.status,
                'is_prebooked': self._is_prebooked_appointment(token)
            })
        
        return live_data
    
    def get_doctor_flow_analysis(self, doctor_id, date=None):
        """Analyze doctor's flow for specific date"""
        if not date:
            date = timezone.now().date()
        
        tokens = Token.objects.filter(
            doctor_id=doctor_id,
            date=date
        ).order_by('appointment_time')
        
        analysis = {
            'total_appointments': tokens.count(),
            'completed': tokens.filter(status='completed').count(),
            'in_progress': tokens.filter(status='in_progress').count(),
            'pending': tokens.filter(status='confirmed').count(),
            'average_delay': 0,
            'current_running_late': False
        }
        
        # Calculate average delay for completed appointments
        completed_tokens = tokens.filter(status='completed', completed_at__isnull=False)
        if completed_tokens.exists():
            total_delay = 0
            for token in completed_tokens:
                expected = datetime.combine(token.date, token.appointment_time)
                if expected.tzinfo is None:
                    expected = timezone.make_aware(expected)
                actual = token.completed_at
                delay = (actual - expected).total_seconds() / 60
                total_delay += delay
            
            analysis['average_delay'] = total_delay / completed_tokens.count()
        
        # Check if currently running late
        current_time = timezone.now()
        current_appointment = tokens.filter(
            appointment_time__lte=current_time.time(),
            status='in_progress'
        ).first()
        
        if current_appointment:
            expected_time = datetime.combine(date, current_appointment.appointment_time)
            if current_time > expected_time + timedelta(minutes=10):
                analysis['current_running_late'] = True
        
        return analysis

# Global instance
advanced_wait_predictor = AdvancedWaitPredictor()