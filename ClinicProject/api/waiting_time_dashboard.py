from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.db.models import Avg, Count
from .models import Token, Doctor, Clinic
from .waiting_time_predictor import waiting_time_predictor
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ClinicWaitingTimeDashboardView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, clinic_id=None):
        """Get comprehensive waiting time dashboard for clinic"""
        try:
            today = timezone.now().date()
            current_time = timezone.now()
            
            if clinic_id:
                clinics = [Clinic.objects.get(id=clinic_id)]
            else:
                clinics = Clinic.objects.all()
            
            dashboard_data = []
            
            for clinic in clinics:
                doctors_data = []
                clinic_avg_wait = 0
                total_queue = 0
                
                for doctor in Doctor.objects.filter(clinic=clinic):
                    # Current queue length
                    current_queue = Token.objects.filter(
                        doctor=doctor,
                        date=today,
                        status__in=['waiting', 'confirmed', 'in_consultation']
                    ).count()
                    
                    # AI prediction for new patient
                    predicted_wait = None
                    try:
                        predicted_wait = waiting_time_predictor.predict_waiting_time(doctor.id)
                    except Exception as e:
                        logger.error(f"Prediction error for doctor {doctor.id}: {e}")
                    
                    # Today's average actual waiting time
                    today_completed = Token.objects.filter(
                        doctor=doctor,
                        date=today,
                        status='completed',
                        consultation_start_time__isnull=False
                    )
                    
                    actual_avg_wait = 0
                    if today_completed.exists():
                        total_wait = 0
                        count = 0
                        for token in today_completed:
                            wait_time = (token.consultation_start_time - token.created_at).total_seconds() / 60
                            if wait_time > 0:
                                total_wait += wait_time
                                count += 1
                        actual_avg_wait = round(total_wait / count) if count > 0 else 0
                    
                    # Next available slot time
                    next_slot_info = self._get_next_available_slot(doctor, current_time)
                    
                    # Expected consultation start for current queue
                    expected_start = self._calculate_expected_start_time(doctor, current_time)
                    
                    doctor_data = {
                        'doctor_id': doctor.id,
                        'doctor_name': doctor.name,
                        'specialization': doctor.specialization,
                        'current_queue_length': current_queue,
                        'predicted_waiting_time_minutes': predicted_wait,
                        'actual_avg_waiting_time_today': actual_avg_wait,
                        'next_available_slot': next_slot_info,
                        'expected_consultation_start': expected_start,
                        'status': 'available' if current_queue < 10 else 'busy'
                    }
                    
                    doctors_data.append(doctor_data)
                    total_queue += current_queue
                    if predicted_wait:
                        clinic_avg_wait += predicted_wait
                
                # Clinic overall stats
                clinic_avg_wait = round(clinic_avg_wait / len(doctors_data)) if doctors_data else 0
                
                clinic_data = {
                    'clinic_id': clinic.id,
                    'clinic_name': clinic.name,
                    'clinic_address': clinic.address,
                    'total_queue_length': total_queue,
                    'average_waiting_time_minutes': clinic_avg_wait,
                    'total_doctors': len(doctors_data),
                    'doctors': doctors_data,
                    'last_updated': current_time.isoformat()
                }
                
                dashboard_data.append(clinic_data)
            
            return Response({
                'success': True,
                'clinics': dashboard_data,
                'timestamp': current_time.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            return Response({'error': 'Failed to load waiting times'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_next_available_slot(self, doctor, current_time):
        """Get next available appointment slot for doctor"""
        from .views import _find_next_available_slot_for_doctor
        
        try:
            next_date, next_time = _find_next_available_slot_for_doctor(doctor.id)
            if next_date and next_time:
                slot_datetime = datetime.combine(next_date, datetime.strptime(next_time, '%H:%M').time())
                slot_datetime = timezone.make_aware(slot_datetime)
                
                if next_date == current_time.date():
                    date_text = "Today"
                elif next_date == current_time.date() + timedelta(days=1):
                    date_text = "Tomorrow"
                else:
                    date_text = next_date.strftime('%b %d')
                
                return {
                    'date': next_date.isoformat(),
                    'time': next_time,
                    'display_text': f"{date_text} at {datetime.strptime(next_time, '%H:%M').strftime('%I:%M %p')}",
                    'minutes_from_now': int((slot_datetime - current_time).total_seconds() / 60)
                }
        except Exception:
            pass
        
        return None
    
    def _calculate_expected_start_time(self, doctor, current_time):
        """Calculate when current queue will likely start consultation"""
        try:
            # Get current queue in order
            queue_tokens = Token.objects.filter(
                doctor=doctor,
                date=current_time.date(),
                status__in=['waiting', 'confirmed']
            ).order_by('created_at')
            
            if not queue_tokens.exists():
                return None
            
            # Estimate 15 minutes per consultation
            avg_consultation_time = 15
            
            # If doctor is currently consulting, add remaining time
            current_consultation = Token.objects.filter(
                doctor=doctor,
                date=current_time.date(),
                status='in_consultation'
            ).first()
            
            start_time = current_time
            if current_consultation:
                # Assume 10 minutes remaining for current consultation
                start_time = current_time + timedelta(minutes=10)
            
            # Calculate expected start for each token in queue
            expected_times = []
            for i, token in enumerate(queue_tokens):
                expected_start = start_time + timedelta(minutes=i * avg_consultation_time)
                expected_times.append({
                    'token_id': token.id,
                    'expected_start': expected_start.strftime('%I:%M %p'),
                    'minutes_from_now': int((expected_start - current_time).total_seconds() / 60)
                })
            
            return expected_times[:5]  # Return first 5 in queue
            
        except Exception as e:
            logger.error(f"Expected start calculation error: {e}")
            return None

class MyTokenWaitingTimeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get waiting time info for user's current token"""
        try:
            user = request.user
            if not hasattr(user, 'patient'):
                return Response({'error': 'Patient profile required'}, status=status.HTTP_400_BAD_REQUEST)
            
            today = timezone.now().date()
            current_time = timezone.now()
            
            # Find user's active token
            from .views import normalize_phone_number
            user_phone_normalized = normalize_phone_number(user.patient.phone_number)
            
            matching_patients = []
            from .models import Patient
            for patient in Patient.objects.all():
                if normalize_phone_number(patient.phone_number) == user_phone_normalized:
                    matching_patients.append(patient.id)
            
            token = Token.objects.filter(
                patient_id__in=matching_patients,
                date=today,
                status__in=['waiting', 'confirmed']
            ).first()
            
            if not token:
                return Response({'error': 'No active token found for today'}, status=status.HTTP_404_NOT_FOUND)
            
            # Calculate position in queue
            queue_position = Token.objects.filter(
                doctor=token.doctor,
                date=today,
                status__in=['waiting', 'confirmed'],
                created_at__lt=token.created_at
            ).count() + 1
            
            # Get AI prediction
            predicted_wait = None
            try:
                predicted_wait = waiting_time_predictor.predict_waiting_time(token.doctor.id)
            except Exception:
                pass
            
            # Calculate expected consultation start
            dashboard_view = ClinicWaitingTimeDashboardView()
            expected_times = dashboard_view._calculate_expected_start_time(token.doctor, current_time)
            
            my_expected_time = None
            if expected_times:
                for time_info in expected_times:
                    if time_info['token_id'] == token.id:
                        my_expected_time = time_info
                        break
            
            # If appointment time exists, calculate delay
            appointment_delay = None
            if token.appointment_time:
                scheduled_time = timezone.make_aware(
                    datetime.combine(token.date, token.appointment_time)
                )
                if my_expected_time:
                    expected_start = current_time + timedelta(minutes=my_expected_time['minutes_from_now'])
                    delay_minutes = int((expected_start - scheduled_time).total_seconds() / 60)
                    appointment_delay = max(0, delay_minutes)
            
            return Response({
                'token_id': token.id,
                'token_number': token.token_number,
                'doctor_name': token.doctor.name,
                'appointment_time': token.appointment_time.strftime('%I:%M %p') if token.appointment_time else None,
                'queue_position': queue_position,
                'predicted_waiting_time_minutes': predicted_wait,
                'expected_consultation_start': my_expected_time,
                'appointment_delay_minutes': appointment_delay,
                'status': token.status,
                'message': self._generate_waiting_message(token, queue_position, my_expected_time, appointment_delay)
            })
            
        except Exception as e:
            logger.error(f"My token waiting time error: {e}")
            return Response({'error': 'Failed to get waiting time info'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_waiting_message(self, token, queue_position, expected_time, delay):
        """Generate user-friendly waiting message"""
        messages = []
        
        if queue_position == 1:
            messages.append("You're next! Please be ready.")
        elif queue_position <= 3:
            messages.append(f"You're #{queue_position} in queue. Almost your turn!")
        else:
            messages.append(f"You're #{queue_position} in queue.")
        
        if expected_time:
            messages.append(f"Expected consultation: {expected_time['expected_start']}")
        
        if delay and delay > 5:
            messages.append(f"Running {delay} minutes behind schedule.")
        elif token.appointment_time:
            messages.append("On schedule.")
        
        return " ".join(messages)