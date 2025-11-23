from django.db.models import Count, Avg, Q, F, Sum
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Token, Doctor, Clinic, Consultation, Patient
import json

class AdvancedReports:
    """Comprehensive reporting and analytics system"""
    
    @staticmethod
    def generate_clinic_performance_report(clinic_id, start_date=None, end_date=None):
        """Generate comprehensive clinic performance report"""
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        clinic = Clinic.objects.get(id=clinic_id)
        
        # Basic metrics
        total_tokens = Token.objects.filter(
            clinic=clinic,
            date__range=[start_date, end_date]
        )
        
        completed_tokens = total_tokens.filter(status='completed')
        cancelled_tokens = total_tokens.filter(status='cancelled')
        
        # Calculate averages
        avg_wait_time = 0
        if completed_tokens.exists():
            wait_times = []
            for token in completed_tokens.filter(completed_at__isnull=False):
                wait_duration = (token.completed_at - token.created_at).total_seconds() / 60
                wait_times.append(wait_duration)
            avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
        
        # Doctor performance
        doctor_stats = []
        for doctor in clinic.doctors.all():
            doctor_tokens = total_tokens.filter(doctor=doctor)
            doctor_completed = doctor_tokens.filter(status='completed')
            
            doctor_stats.append({
                'doctor_name': doctor.name,
                'specialization': doctor.specialization,
                'total_patients': doctor_tokens.count(),
                'completed_consultations': doctor_completed.count(),
                'completion_rate': (doctor_completed.count() / doctor_tokens.count() * 100) if doctor_tokens.count() > 0 else 0,
                'avg_consultation_time': AdvancedReports._calculate_avg_consultation_time(doctor, start_date, end_date)
            })
        
        # Daily trends
        daily_trends = []
        current_date = start_date
        while current_date <= end_date:
            day_tokens = total_tokens.filter(date=current_date)
            daily_trends.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'total_patients': day_tokens.count(),
                'completed': day_tokens.filter(status='completed').count(),
                'cancelled': day_tokens.filter(status='cancelled').count(),
                'no_shows': day_tokens.filter(status='skipped').count()
            })
            current_date += timedelta(days=1)
        
        # Peak hours analysis
        peak_hours = AdvancedReports._analyze_peak_hours(clinic_id, start_date, end_date)
        
        return {
            'clinic_name': clinic.name,
            'report_period': f"{start_date} to {end_date}",
            'summary': {
                'total_patients': total_tokens.count(),
                'completed_consultations': completed_tokens.count(),
                'cancelled_appointments': cancelled_tokens.count(),
                'completion_rate': (completed_tokens.count() / total_tokens.count() * 100) if total_tokens.count() > 0 else 0,
                'avg_waiting_time_minutes': round(avg_wait_time, 1),
                'patient_satisfaction_score': AdvancedReports._calculate_satisfaction_score(clinic_id, start_date, end_date)
            },
            'doctor_performance': doctor_stats,
            'daily_trends': daily_trends,
            'peak_hours': peak_hours,
            'recommendations': AdvancedReports._generate_recommendations(clinic_id, start_date, end_date)
        }
    
    @staticmethod
    def _calculate_avg_consultation_time(doctor, start_date, end_date):
        """Calculate average consultation time for a doctor"""
        consultations = Token.objects.filter(
            doctor=doctor,
            date__range=[start_date, end_date],
            status='completed',
            consultation_start_time__isnull=False,
            completed_at__isnull=False
        )
        
        if not consultations.exists():
            return 0
        
        total_time = 0
        count = 0
        
        for consultation in consultations:
            duration = (consultation.completed_at - consultation.consultation_start_time).total_seconds() / 60
            if 0 < duration < 120:  # Reasonable consultation time (0-2 hours)
                total_time += duration
                count += 1
        
        return round(total_time / count, 1) if count > 0 else 0
    
    @staticmethod
    def _analyze_peak_hours(clinic_id, start_date, end_date):
        """Analyze peak hours for the clinic"""
        hourly_data = {}
        
        tokens = Token.objects.filter(
            clinic_id=clinic_id,
            date__range=[start_date, end_date]
        )
        
        for token in tokens:
            hour = token.created_at.hour
            if hour not in hourly_data:
                hourly_data[hour] = 0
            hourly_data[hour] += 1
        
        # Convert to list and sort by patient count
        peak_hours = [
            {'hour': f"{hour}:00", 'patient_count': count}
            for hour, count in hourly_data.items()
        ]
        peak_hours.sort(key=lambda x: x['patient_count'], reverse=True)
        
        return peak_hours[:5]  # Top 5 peak hours
    
    @staticmethod
    def _calculate_satisfaction_score(clinic_id, start_date, end_date):
        """Calculate patient satisfaction score based on various metrics"""
        # This is a simplified calculation - in reality, you'd want patient feedback
        tokens = Token.objects.filter(
            clinic_id=clinic_id,
            date__range=[start_date, end_date]
        )
        
        if not tokens.exists():
            return 0
        
        # Factors affecting satisfaction
        completion_rate = tokens.filter(status='completed').count() / tokens.count()
        cancellation_rate = tokens.filter(status='cancelled').count() / tokens.count()
        
        # Simple scoring algorithm (0-100)
        score = 100
        score -= (cancellation_rate * 30)  # High cancellations reduce score
        score += (completion_rate * 20)    # High completions increase score
        
        return max(0, min(100, round(score, 1)))
    
    @staticmethod
    def _generate_recommendations(clinic_id, start_date, end_date):
        """Generate actionable recommendations based on data"""
        recommendations = []
        
        tokens = Token.objects.filter(
            clinic_id=clinic_id,
            date__range=[start_date, end_date]
        )
        
        # High cancellation rate
        cancellation_rate = tokens.filter(status='cancelled').count() / tokens.count() if tokens.count() > 0 else 0
        if cancellation_rate > 0.15:  # More than 15%
            recommendations.append({
                'type': 'cancellation_reduction',
                'priority': 'high',
                'message': f'Cancellation rate is {cancellation_rate*100:.1f}%. Consider implementing reminder systems.',
                'action': 'Setup automated appointment reminders'
            })
        
        # Long waiting times
        completed_tokens = tokens.filter(status='completed', completed_at__isnull=False)
        if completed_tokens.exists():
            avg_wait = sum(
                (token.completed_at - token.created_at).total_seconds() / 60
                for token in completed_tokens
            ) / completed_tokens.count()
            
            if avg_wait > 45:  # More than 45 minutes
                recommendations.append({
                    'type': 'wait_time_reduction',
                    'priority': 'medium',
                    'message': f'Average waiting time is {avg_wait:.1f} minutes. Consider optimizing schedules.',
                    'action': 'Review doctor schedules and slot durations'
                })
        
        # Uneven doctor workload
        doctors = Doctor.objects.filter(clinic_id=clinic_id)
        if doctors.count() > 1:
            workloads = []
            for doctor in doctors:
                doctor_tokens = tokens.filter(doctor=doctor).count()
                workloads.append(doctor_tokens)
            
            if max(workloads) - min(workloads) > 20:  # Significant difference
                recommendations.append({
                    'type': 'workload_balancing',
                    'priority': 'medium',
                    'message': 'Uneven workload distribution among doctors detected.',
                    'action': 'Consider redistributing appointments or adjusting schedules'
                })
        
        return recommendations
    
    @staticmethod
    def generate_financial_report(clinic_id, start_date=None, end_date=None):
        """Generate financial performance report"""
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # This would integrate with your billing system
        # For now, we'll provide a template structure
        
        completed_consultations = Token.objects.filter(
            clinic_id=clinic_id,
            date__range=[start_date, end_date],
            status='completed'
        ).count()
        
        # Placeholder calculations - replace with actual billing data
        avg_consultation_fee = 500  # Replace with actual fee structure
        total_revenue = completed_consultations * avg_consultation_fee
        
        return {
            'period': f"{start_date} to {end_date}",
            'completed_consultations': completed_consultations,
            'estimated_revenue': total_revenue,
            'avg_consultation_fee': avg_consultation_fee,
            'note': 'Financial calculations are estimates. Integrate with billing system for accurate data.'
        }
    
    @staticmethod
    def export_report_data(report_data, format='json'):
        """Export report data in various formats"""
        if format == 'json':
            return json.dumps(report_data, indent=2, default=str)
        elif format == 'csv':
            # Implement CSV export logic
            return "CSV export not implemented yet"
        else:
            return str(report_data)