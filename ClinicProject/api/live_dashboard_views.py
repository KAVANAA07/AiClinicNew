from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q
from django.db import models
from .models import Token, Doctor
from .advanced_wait_predictor import advanced_wait_predictor
from .serializers import TokenSerializer
import logging

logger = logging.getLogger(__name__)

class LiveWaitTimesView(APIView):
    """Real-time wait times for pre-booked appointments"""
    
    def get(self, request):
        try:
            doctor_id = request.query_params.get('doctor_id')
            
            # Get live updates data
            live_data = advanced_wait_predictor.get_live_updates_data(doctor_id)
            
            return Response({
                'success': True,
                'live_wait_times': live_data,
                'last_updated': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting live wait times: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TokenWaitTimeView(APIView):
    """Get predicted wait time for specific token"""
    
    def get(self, request, token_id):
        try:
            predicted_wait = advanced_wait_predictor.get_predicted_wait_time(token_id)
            
            # Get token details
            token = Token.objects.get(id=token_id)
            is_prebooked = advanced_wait_predictor._is_prebooked_appointment(token)
            
            # Get queue position - count tokens ahead that are still active
            if token.status == 'in_consultancy':
                queue_position = 0  # Currently being seen
            else:
                # Count confirmed tokens with earlier appointment times or creation times
                tokens_ahead = Token.objects.filter(
                    doctor=token.doctor,
                    date=token.date,
                    status__in=['confirmed', 'in_consultancy']
                ).filter(
                    models.Q(appointment_time__lt=token.appointment_time) |
                    models.Q(appointment_time=token.appointment_time, created_at__lt=token.created_at) |
                    models.Q(appointment_time__isnull=True, created_at__lt=token.created_at)
                ).count()
                queue_position = tokens_ahead + 1
            
            return Response({
                'success': True,
                'token_id': token_id,
                'predicted_wait_minutes': predicted_wait,
                'position_in_queue': queue_position,
                'is_prebooked': is_prebooked,
                'appointment_time': token.appointment_time.strftime('%H:%M') if token.appointment_time else None,
                'doctor_name': token.doctor.name,
                'prediction_method': 'ML + Real-time Flow' if is_prebooked else 'Queue Position'
            })
            
        except Token.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Token not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting token wait time: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DoctorFlowAnalysisView(APIView):
    """Real-time doctor flow analysis"""
    
    def get(self, request, doctor_id):
        try:
            date_str = request.query_params.get('date')
            date = None
            if date_str:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            
            analysis = advanced_wait_predictor.get_doctor_flow_analysis(doctor_id, date)
            
            return Response({
                'success': True,
                'doctor_id': doctor_id,
                'analysis_date': (date or timezone.now().date()).isoformat(),
                'flow_analysis': analysis
            })
            
        except Exception as e:
            logger.error(f"Error getting doctor flow analysis: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LiveDashboardOverviewView(APIView):
    """Complete dashboard overview with live updates"""
    
    def get(self, request):
        try:
            today = timezone.now().date()
            
            # Get all doctors with appointments today
            doctors_with_appointments = Doctor.objects.filter(
                token__appointment_date=today
            ).distinct()
            
            dashboard_data = {
                'clinic_overview': {
                    'total_appointments_today': Token.objects.filter(appointment_date=today).count(),
                    'completed_today': Token.objects.filter(appointment_date=today, status='completed').count(),
                    'in_progress': Token.objects.filter(appointment_date=today, status='in_progress').count(),
                    'pending': Token.objects.filter(appointment_date=today, status='confirmed').count(),
                },
                'doctors_status': [],
                'live_wait_times': advanced_wait_predictor.get_live_updates_data(),
                'last_updated': timezone.now().isoformat()
            }
            
            # Get status for each doctor
            for doctor in doctors_with_appointments:
                flow_analysis = advanced_wait_predictor.get_doctor_flow_analysis(doctor.id)
                
                dashboard_data['doctors_status'].append({
                    'doctor_id': doctor.id,
                    'doctor_name': doctor.name,
                    'specialization': doctor.specialization,
                    'total_appointments': flow_analysis['total_appointments'],
                    'completed': flow_analysis['completed'],
                    'in_progress': flow_analysis['in_progress'],
                    'pending': flow_analysis['pending'],
                    'average_delay_minutes': round(flow_analysis['average_delay'], 1),
                    'running_late': flow_analysis['current_running_late']
                })
            
            return Response({
                'success': True,
                'dashboard': dashboard_data
            })
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateTokenStatusView(APIView):
    """Update token status and recalculate wait times"""
    
    def post(self, request, token_id):
        try:
            token = Token.objects.get(id=token_id)
            new_status = request.data.get('status')
            
            if new_status not in ['confirmed', 'in_progress', 'completed', 'cancelled']:
                return Response({
                    'success': False,
                    'error': 'Invalid status'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            old_status = token.status
            token.status = new_status
            
            # Set completion time if completed
            if new_status == 'completed' and old_status != 'completed':
                token.completed_at = timezone.now()
            
            token.save()
            
            # Get updated wait times for affected tokens
            affected_tokens = Token.objects.filter(
                doctor=token.doctor,
                appointment_date=token.appointment_date,
                appointment_time__gt=token.appointment_time,
                status__in=['confirmed', 'in_progress']
            )
            
            updated_wait_times = []
            for affected_token in affected_tokens:
                new_wait_time = advanced_wait_predictor.get_predicted_wait_time(affected_token.id)
                updated_wait_times.append({
                    'token_id': affected_token.id,
                    'new_wait_time': new_wait_time
                })
            
            return Response({
                'success': True,
                'token_id': token_id,
                'new_status': new_status,
                'updated_wait_times': updated_wait_times
            })
            
        except Token.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Token not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating token status: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)