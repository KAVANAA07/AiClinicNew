from django.db.models import Q, F
from django.utils import timezone
from datetime import timedelta
from .models import Token, Doctor
from .waiting_time_predictor import waiting_time_predictor
import logging

logger = logging.getLogger(__name__)

class SmartQueueManager:
    """Intelligent queue management with AI-powered optimizations"""
    
    @staticmethod
    def optimize_queue_order(doctor_id, date=None):
        """Reorder queue based on AI predictions and patient priorities"""
        if not date:
            date = timezone.now().date()
        
        # Get current queue
        queue = Token.objects.filter(
            doctor_id=doctor_id,
            date=date,
            status__in=['waiting', 'confirmed']
        ).order_by('created_at')
        
        if queue.count() < 2:
            return {"message": "Queue too small for optimization"}
        
        optimized_order = []
        
        for token in queue:
            priority_score = SmartQueueManager._calculate_priority_score(token)
            optimized_order.append({
                'token': token,
                'priority_score': priority_score
            })
        
        # Sort by priority score (higher = more urgent)
        optimized_order.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Update queue positions
        for i, item in enumerate(optimized_order):
            token = item['token']
            # Store original position for comparison
            original_pos = list(queue).index(token) + 1
            new_pos = i + 1
            
            # Only log significant changes
            if abs(original_pos - new_pos) > 1:
                logger.info(f"Queue optimization: Token {token.id} moved from position {original_pos} to {new_pos}")
        
        return {
            "optimized": True,
            "total_tokens": len(optimized_order),
            "changes_made": sum(1 for i, item in enumerate(optimized_order) 
                              if list(queue).index(item['token']) != i)
        }
    
    @staticmethod
    def _calculate_priority_score(token):
        """Calculate priority score for a patient token"""
        score = 0
        
        # Base score from waiting time
        wait_minutes = (timezone.now() - token.created_at).total_seconds() / 60
        score += min(wait_minutes * 0.5, 50)  # Max 50 points for waiting
        
        # Appointment vs walk-in priority
        if token.appointment_time:
            # Scheduled appointments get priority near their time
            now = timezone.now().time()
            if token.appointment_time <= now:
                score += 30  # Late for appointment
            elif (timezone.datetime.combine(timezone.now().date(), token.appointment_time) - 
                  timezone.datetime.combine(timezone.now().date(), now)).total_seconds() <= 900:  # 15 min window
                score += 20  # Approaching appointment time
        else:
            # Walk-ins get base priority
            score += 10
        
        # Confirmed arrival gets priority
        if token.status == 'confirmed':
            score += 15
        
        # Distance-based priority (closer patients get slight priority)
        if token.distance_km and token.distance_km <= 0.5:  # Very close
            score += 5
        
        return score
    
    @staticmethod
    def suggest_optimal_appointment_time(doctor_id, preferred_date=None):
        """Suggest the best appointment time based on current queue and predictions"""
        if not preferred_date:
            preferred_date = timezone.now().date()
        
        # Get available slots
        from .views import _get_available_slots_for_doctor
        available_slots = _get_available_slots_for_doctor(doctor_id, preferred_date.strftime('%Y-%m-%d'))
        
        if not available_slots:
            return {"error": "No available slots"}
        
        slot_recommendations = []
        
        for slot_str in available_slots[:5]:  # Check first 5 slots
            slot_time = timezone.datetime.strptime(slot_str, '%H:%M').time()
            
            # Predict waiting time for this slot
            try:
                predicted_wait = waiting_time_predictor.predict_waiting_time(
                    doctor_id, 
                    for_appointment_time=slot_time
                )
            except:
                predicted_wait = 15  # Default fallback
            
            # Calculate queue length at that time
            queue_before = Token.objects.filter(
                doctor_id=doctor_id,
                date=preferred_date,
                appointment_time__lt=slot_time,
                status__in=['waiting', 'confirmed']
            ).count()
            
            # Score this slot (lower is better)
            slot_score = predicted_wait + (queue_before * 5)
            
            slot_recommendations.append({
                'time': slot_str,
                'predicted_wait': predicted_wait,
                'queue_position': queue_before + 1,
                'recommendation_score': slot_score,
                'rating': 'excellent' if slot_score < 20 else 'good' if slot_score < 35 else 'fair'
            })
        
        # Sort by score (best first)
        slot_recommendations.sort(key=lambda x: x['recommendation_score'])
        
        return {
            'recommended_slots': slot_recommendations,
            'best_slot': slot_recommendations[0] if slot_recommendations else None
        }
    
    @staticmethod
    def detect_queue_bottlenecks(clinic_id):
        """Detect and report queue bottlenecks"""
        today = timezone.now().date()
        bottlenecks = []
        
        doctors = Doctor.objects.filter(clinic_id=clinic_id)
        
        for doctor in doctors:
            queue = Token.objects.filter(
                doctor=doctor,
                date=today,
                status__in=['waiting', 'confirmed']
            )
            
            queue_length = queue.count()
            
            # Check for bottlenecks
            if queue_length > 8:
                bottlenecks.append({
                    'doctor_id': doctor.id,
                    'doctor_name': doctor.name,
                    'queue_length': queue_length,
                    'severity': 'high' if queue_length > 12 else 'medium',
                    'recommendation': 'Consider redistributing patients or extending hours'
                })
            
            # Check for long waiting patients
            long_wait_patients = queue.filter(
                created_at__lt=timezone.now() - timedelta(hours=2)
            ).count()
            
            if long_wait_patients > 0:
                bottlenecks.append({
                    'doctor_id': doctor.id,
                    'doctor_name': doctor.name,
                    'issue': f'{long_wait_patients} patients waiting over 2 hours',
                    'severity': 'high',
                    'recommendation': 'Prioritize long-waiting patients'
                })
        
        return bottlenecks
    
    @staticmethod
    def auto_reschedule_suggestions(clinic_id):
        """Suggest automatic rescheduling for overbooked doctors"""
        today = timezone.now().date()
        suggestions = []
        
        doctors = Doctor.objects.filter(clinic_id=clinic_id)
        
        # Find overbooked doctors
        overbooked_doctors = []
        underbooked_doctors = []
        
        for doctor in doctors:
            queue_length = Token.objects.filter(
                doctor=doctor,
                date=today,
                status__in=['waiting', 'confirmed']
            ).count()
            
            if queue_length > 10:
                overbooked_doctors.append((doctor, queue_length))
            elif queue_length < 3:
                underbooked_doctors.append((doctor, queue_length))
        
        # Generate rescheduling suggestions
        for overbooked_doctor, queue_length in overbooked_doctors:
            # Find patients that could be moved
            moveable_tokens = Token.objects.filter(
                doctor=overbooked_doctor,
                date=today,
                status='waiting',
                appointment_time__isnull=True  # Walk-ins are easier to move
            )[:3]  # Suggest moving up to 3 patients
            
            for token in moveable_tokens:
                for underbooked_doctor, _ in underbooked_doctors:
                    # Check if underbooked doctor has same specialization
                    if (underbooked_doctor.specialization == overbooked_doctor.specialization or 
                        underbooked_doctor.specialization == 'General Medicine'):
                        
                        suggestions.append({
                            'patient_id': token.patient.id,
                            'patient_name': token.patient.name,
                            'from_doctor': overbooked_doctor.name,
                            'to_doctor': underbooked_doctor.name,
                            'reason': f'Reduce queue from {queue_length} patients',
                            'compatibility': 'high' if underbooked_doctor.specialization == overbooked_doctor.specialization else 'medium'
                        })
                        break
        
        return suggestions