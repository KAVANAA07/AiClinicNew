from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import Token, Doctor, Clinic
from .waiting_time_predictor import waiting_time_predictor

class RealTimeDashboard:
    """Enhanced real-time analytics for clinic operations"""
    
    @staticmethod
    def get_clinic_metrics(clinic_id):
        """Get comprehensive real-time metrics for a clinic"""
        today = timezone.now().date()
        now = timezone.now()
        
        # Basic counts
        today_tokens = Token.objects.filter(clinic_id=clinic_id, date=today)
        
        metrics = {
            'total_patients_today': today_tokens.count(),
            'waiting_patients': today_tokens.filter(status='waiting').count(),
            'confirmed_patients': today_tokens.filter(status='confirmed').count(),
            'in_consultation': today_tokens.filter(status='in_consultancy').count(),
            'completed_today': today_tokens.filter(status='completed').count(),
            'cancelled_today': today_tokens.filter(status='cancelled').count(),
        }
        
        # Doctor workload
        doctor_stats = []
        doctors = Doctor.objects.filter(clinic_id=clinic_id)
        
        for doctor in doctors:
            doctor_tokens = today_tokens.filter(doctor=doctor)
            queue_length = doctor_tokens.filter(status__in=['waiting', 'confirmed']).count()
            
            # AI prediction
            try:
                predicted_wait = waiting_time_predictor.predict_waiting_time(doctor.id)
            except:
                predicted_wait = None
            
            doctor_stats.append({
                'doctor_id': doctor.id,
                'doctor_name': doctor.name,
                'specialization': doctor.specialization,
                'total_patients': doctor_tokens.count(),
                'queue_length': queue_length,
                'completed': doctor_tokens.filter(status='completed').count(),
                'predicted_wait_time': predicted_wait,
                'status': 'busy' if queue_length > 5 else 'available'
            })
        
        metrics['doctor_stats'] = doctor_stats
        
        # Hourly distribution
        hourly_data = []
        for hour in range(9, 18):  # 9 AM to 5 PM
            hour_start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            hour_tokens = today_tokens.filter(
                created_at__gte=hour_start,
                created_at__lt=hour_end
            ).count()
            
            hourly_data.append({
                'hour': f"{hour}:00",
                'patients': hour_tokens
            })
        
        metrics['hourly_distribution'] = hourly_data
        
        # Average waiting time
        completed_tokens = today_tokens.filter(
            status='completed',
            completed_at__isnull=False
        )
        
        if completed_tokens.exists():
            avg_wait = completed_tokens.aggregate(
                avg_wait=Avg('completed_at') - Avg('created_at')
            )['avg_wait']
            metrics['avg_waiting_time'] = int(avg_wait.total_seconds() / 60) if avg_wait else 0
        else:
            metrics['avg_waiting_time'] = 0
        
        return metrics
    
    @staticmethod
    def get_patient_flow_prediction(clinic_id):
        """Predict patient flow for next few hours"""
        # Historical analysis for prediction
        today = timezone.now().date()
        same_weekday_dates = []
        
        # Get last 4 weeks same weekday data
        for i in range(1, 5):
            past_date = today - timedelta(weeks=i)
            same_weekday_dates.append(past_date)
        
        predictions = []
        current_hour = timezone.now().hour
        
        for hour in range(current_hour + 1, min(current_hour + 4, 18)):
            # Average patients in this hour on same weekdays
            avg_patients = Token.objects.filter(
                clinic_id=clinic_id,
                date__in=same_weekday_dates,
                created_at__hour=hour
            ).count() / len(same_weekday_dates)
            
            predictions.append({
                'hour': f"{hour}:00",
                'predicted_patients': round(avg_patients),
                'confidence': 'medium' if avg_patients > 0 else 'low'
            })
        
        return predictions