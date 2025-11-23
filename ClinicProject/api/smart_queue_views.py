from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Token, Doctor
from .real_time_queue_manager import RealTimeQueueManager
from .smart_queue_analytics import SmartQueueAnalytics
from .waiting_time_predictor import waiting_time_predictor
import logging

logger = logging.getLogger(__name__)

class RealTimeQueueView(APIView):
    """Real-time queue status API"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, doctor_id=None):
        user = request.user
        
        # Determine doctor_id based on user role
        if doctor_id is None:
            if hasattr(user, 'doctor'):
                doctor_id = user.doctor.id
            else:
                return Response({'error': 'Doctor ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            queue_status = RealTimeQueueManager.get_live_queue_status(doctor_id)
            analytics = SmartQueueAnalytics.calculate_actual_wait_times()
            
            return Response({
                'queue_status': queue_status,
                'analytics': analytics,
                'last_updated': timezone.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Real-time queue error: {e}")
            return Response({'error': 'Failed to get queue status'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EarlyArrivalView(APIView):
    """Activate early arrival for patients"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        token_id = request.data.get('token_id')
        
        if not token_id:
            return Response({'error': 'Token ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            success, message = RealTimeQueueManager.activate_early_arrival(token_id)
            
            if success:
                return Response({'success': True, 'message': message})
            else:
                return Response({'success': False, 'error': message}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Early arrival activation error: {e}")
            return Response({'error': 'Failed to activate early arrival'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClinicOverviewView(APIView):
    """Real-time clinic overview"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        clinic_id = None
        
        # Get clinic ID from user
        if hasattr(user, 'doctor') and user.doctor.clinic:
            clinic_id = user.doctor.clinic.id
        elif hasattr(user, 'receptionist') and user.receptionist.clinic:
            clinic_id = user.receptionist.clinic.id
        
        if not clinic_id:
            return Response({'error': 'User not associated with clinic'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            overview = RealTimeQueueManager.get_clinic_overview(clinic_id)
            early_opportunities = SmartQueueAnalytics.detect_early_slots()
            
            return Response({
                'clinic_overview': overview,
                'early_opportunities': early_opportunities,
                'last_updated': timezone.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Clinic overview error: {e}")
            return Response({'error': 'Failed to get clinic overview'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SmartQueueActionsView(APIView):
    """Smart queue management actions"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        action = request.data.get('action')
        
        if not action:
            return Response({'error': 'Action required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if action == 'activate_early_arrivals':
                activated = SmartQueueAnalytics.activate_early_arrivals()
                return Response({
                    'success': True,
                    'activated_count': activated,
                    'message': f'Activated early arrival for {activated} patients'
                })
            
            elif action == 'daily_optimization':
                from .smart_queue_analytics import daily_queue_optimization
                result = daily_queue_optimization()
                return Response({
                    'success': True,
                    'optimization_result': result
                })
            
            elif action == 'detect_early_slots':
                opportunities = SmartQueueAnalytics.detect_early_slots()
                return Response({
                    'success': True,
                    'early_opportunities': opportunities
                })
            
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Smart queue action error: {e}")
            return Response({'error': 'Action failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PatientQueueStatusView(APIView):
    """Patient's own queue status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'patient'):
            return Response({'error': 'Patient profile required'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            today = timezone.now().date()
            
            # Find patient's active token
            token = Token.objects.filter(
                patient=user.patient,
                date=today,
                status__in=['waiting', 'confirmed']
            ).first()
            
            if not token:
                return Response({'error': 'No active appointment found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get queue status for patient's doctor
            queue_status = RealTimeQueueManager.get_live_queue_status(token.doctor.id)
            
            # Find patient's position in queue
            patient_position = None
            can_arrive_early = False
            estimated_wait = None
            
            for i, patient_info in enumerate(queue_status['next_patients']):
                if patient_info['token_number'] == token.token_number:
                    patient_position = patient_info['position']
                    can_arrive_early = patient_info['can_arrive_early']
                    estimated_wait = patient_info['predicted_wait_minutes']
                    break
            
            return Response({
                'token_id': token.id,
                'token_number': token.token_number,
                'doctor_name': token.doctor.name,
                'appointment_time': token.appointment_time.strftime('%H:%M') if token.appointment_time else 'Walk-in',
                'status': token.status,
                'position_in_queue': patient_position,
                'estimated_wait_minutes': estimated_wait,
                'can_arrive_early': can_arrive_early,
                'queue_status': queue_status,
                'last_updated': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Patient queue status error: {e}")
            return Response({'error': 'Failed to get queue status'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WalkInAvailabilityView(APIView):
    """Check walk-in availability"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        clinic_id = None
        
        # Get clinic ID
        if hasattr(user, 'doctor') and user.doctor.clinic:
            clinic_id = user.doctor.clinic.id
        elif hasattr(user, 'receptionist') and user.receptionist.clinic:
            clinic_id = user.receptionist.clinic.id
        
        if not clinic_id:
            return Response({'error': 'Clinic not found'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            doctors = Doctor.objects.filter(clinic_id=clinic_id)
            availability = []
            
            for doctor in doctors:
                can_accept = RealTimeQueueManager._can_accept_walkins(doctor.id)
                queue_status = RealTimeQueueManager.get_live_queue_status(doctor.id)
                
                availability.append({
                    'doctor_id': doctor.id,
                    'doctor_name': doctor.name,
                    'specialization': doctor.specialization,
                    'can_accept_walkin': can_accept,
                    'current_queue_length': queue_status['total_waiting'],
                    'estimated_wait_minutes': queue_status['total_waiting'] * 12 if can_accept else None
                })
            
            return Response({
                'clinic_id': clinic_id,
                'walk_in_availability': availability,
                'last_updated': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Walk-in availability error: {e}")
            return Response({'error': 'Failed to check availability'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)