from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, timedelta
from .real_time_dashboard import RealTimeDashboard
from .smart_queue_manager import SmartQueueManager
from .communication_hub import CommunicationHub
from .advanced_reports import AdvancedReports
from .models import Clinic, Doctor
import logging

logger = logging.getLogger(__name__)

class RealTimeDashboardView(APIView):
    """Real-time dashboard metrics API"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        clinic_id = None
        
        # Determine clinic based on user role
        if hasattr(user, 'doctor'):
            clinic_id = user.doctor.clinic.id if user.doctor.clinic else None
        elif hasattr(user, 'receptionist'):
            clinic_id = user.receptionist.clinic.id if user.receptionist.clinic else None
        
        if not clinic_id:
            return Response({'error': 'User not associated with a clinic'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            metrics = RealTimeDashboard.get_clinic_metrics(clinic_id)
            predictions = RealTimeDashboard.get_patient_flow_prediction(clinic_id)
            
            return Response({
                'clinic_metrics': metrics,
                'flow_predictions': predictions,
                'last_updated': timezone.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            return Response({'error': 'Failed to load dashboard data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SmartQueueView(APIView):
    """Smart queue management API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        action = request.data.get('action')
        doctor_id = request.data.get('doctor_id')
        
        if not action or not doctor_id:
            return Response({'error': 'Action and doctor_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if action == 'optimize':
                result = SmartQueueManager.optimize_queue_order(doctor_id)
                return Response(result)
            
            elif action == 'suggest_appointment':
                preferred_date = request.data.get('date')
                if preferred_date:
                    preferred_date = datetime.strptime(preferred_date, '%Y-%m-%d').date()
                result = SmartQueueManager.suggest_optimal_appointment_time(doctor_id, preferred_date)
                return Response(result)
            
            elif action == 'detect_bottlenecks':
                # Get clinic from doctor
                doctor = Doctor.objects.get(id=doctor_id)
                clinic_id = doctor.clinic.id if doctor.clinic else None
                if not clinic_id:
                    return Response({'error': 'Doctor not associated with clinic'}, status=status.HTTP_400_BAD_REQUEST)
                
                bottlenecks = SmartQueueManager.detect_queue_bottlenecks(clinic_id)
                return Response({'bottlenecks': bottlenecks})
            
            elif action == 'reschedule_suggestions':
                doctor = Doctor.objects.get(id=doctor_id)
                clinic_id = doctor.clinic.id if doctor.clinic else None
                if not clinic_id:
                    return Response({'error': 'Doctor not associated with clinic'}, status=status.HTTP_400_BAD_REQUEST)
                
                suggestions = SmartQueueManager.auto_reschedule_suggestions(clinic_id)
                return Response({'suggestions': suggestions})
            
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Smart queue error: {e}")
            return Response({'error': 'Queue management failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CommunicationHubView(APIView):
    """Patient communication management API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        action = request.data.get('action')
        
        if not action:
            return Response({'error': 'Action required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if action == 'send_smart_notifications':
                result = CommunicationHub.send_smart_notifications()
                return Response(result)
            
            elif action == 'bulk_announcement':
                clinic_id = self._get_user_clinic_id(request.user)
                if not clinic_id:
                    return Response({'error': 'User not associated with clinic'}, status=status.HTTP_403_FORBIDDEN)
                
                message = request.data.get('message')
                target_group = request.data.get('target_group', 'all')
                
                if not message:
                    return Response({'error': 'Message required'}, status=status.HTTP_400_BAD_REQUEST)
                
                result = CommunicationHub.send_bulk_announcement(clinic_id, message, target_group)
                return Response(result)
            
            elif action == 'setup_automation':
                CommunicationHub.setup_automated_notifications()
                return Response({'message': 'Automated notifications setup completed'})
            
            elif action == 'get_analytics':
                clinic_id = self._get_user_clinic_id(request.user)
                if not clinic_id:
                    return Response({'error': 'User not associated with clinic'}, status=status.HTTP_403_FORBIDDEN)
                
                days = int(request.data.get('days', 7))
                analytics = CommunicationHub.get_communication_analytics(clinic_id, days)
                return Response(analytics)
            
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Communication hub error: {e}")
            return Response({'error': 'Communication operation failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_user_clinic_id(self, user):
        """Helper to get clinic ID from user"""
        if hasattr(user, 'doctor') and user.doctor.clinic:
            return user.doctor.clinic.id
        elif hasattr(user, 'receptionist') and user.receptionist.clinic:
            return user.receptionist.clinic.id
        return None

class AdvancedReportsView(APIView):
    """Advanced reporting and analytics API"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        report_type = request.query_params.get('type', 'performance')
        clinic_id = self._get_user_clinic_id(request.user)
        
        if not clinic_id:
            return Response({'error': 'User not associated with clinic'}, status=status.HTTP_403_FORBIDDEN)
        
        # Parse date parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        try:
            if report_type == 'performance':
                report = AdvancedReports.generate_clinic_performance_report(
                    clinic_id, start_date, end_date
                )
                return Response(report)
            
            elif report_type == 'financial':
                report = AdvancedReports.generate_financial_report(
                    clinic_id, start_date, end_date
                )
                return Response(report)
            
            else:
                return Response({'error': 'Invalid report type'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Clinic.DoesNotExist:
            return Response({'error': 'Clinic not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return Response({'error': 'Report generation failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Export report data"""
        report_data = request.data.get('report_data')
        export_format = request.data.get('format', 'json')
        
        if not report_data:
            return Response({'error': 'Report data required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            exported_data = AdvancedReports.export_report_data(report_data, export_format)
            return Response({
                'exported_data': exported_data,
                'format': export_format,
                'timestamp': timezone.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Report export error: {e}")
            return Response({'error': 'Export failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_user_clinic_id(self, user):
        """Helper to get clinic ID from user"""
        if hasattr(user, 'doctor') and user.doctor.clinic:
            return user.doctor.clinic.id
        elif hasattr(user, 'receptionist') and user.receptionist.clinic:
            return user.receptionist.clinic.id
        return None

class ClinicInsightsView(APIView):
    """Combined insights and recommendations API"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        clinic_id = self._get_user_clinic_id(request.user)
        
        if not clinic_id:
            return Response({'error': 'User not associated with clinic'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Get real-time metrics
            metrics = RealTimeDashboard.get_clinic_metrics(clinic_id)
            
            # Get bottlenecks
            bottlenecks = SmartQueueManager.detect_queue_bottlenecks(clinic_id)
            
            # Get recent performance (last 7 days)
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=7)
            performance = AdvancedReports.generate_clinic_performance_report(
                clinic_id, start_date, end_date
            )
            
            return Response({
                'current_metrics': metrics,
                'bottlenecks': bottlenecks,
                'weekly_performance': performance,
                'insights_generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Insights generation error: {e}")
            return Response({'error': 'Failed to generate insights'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_user_clinic_id(self, user):
        """Helper to get clinic ID from user"""
        if hasattr(user, 'doctor') and user.doctor.clinic:
            return user.doctor.clinic.id
        elif hasattr(user, 'receptionist') and user.receptionist.clinic:
            return user.receptionist.clinic.id
        return None