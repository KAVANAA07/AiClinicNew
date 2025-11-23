from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from .auto_training_triggers import AutoTrainingManager
from .waiting_time_predictor import waiting_time_predictor
from .models import Token
import logging

logger = logging.getLogger(__name__)

class TrainingManagementView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get training management dashboard"""
        try:
            stats = AutoTrainingManager.get_training_stats()
            
            # Get recent training activity
            recent_completions = Token.objects.filter(
                status='completed',
                consultation_start_time__isnull=False,
                completed_at__gte=timezone.now() - timezone.timedelta(days=1)
            ).count()
            
            return Response({
                'training_statistics': stats,
                'recent_completions_24h': recent_completions,
                'auto_training_enabled': True,
                'training_triggers': {
                    'nightly_full_retrain': '2:00 AM daily',
                    'automatic_triggers': 'Every 12 hours if 3+ new consultations',
                    'signal_based': 'After 5+ consultations in 24 hours'
                },
                'data_usage': 'ALL historical consultation data',
                'last_check': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Manually trigger training operations"""
        action = request.data.get('action', 'train')
        
        try:
            if action == 'train':
                # Force immediate training with all data
                success = AutoTrainingManager.force_retrain_all_data()
                
                if success:
                    return Response({
                        'message': 'Model retrained successfully with ALL consultation data',
                        'timestamp': timezone.now().isoformat()
                    })
                else:
                    return Response({
                        'error': 'Training failed - check logs for details'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            elif action == 'setup_schedules':
                # Setup/reset automatic training schedules
                from .tasks_ml import setup_ml_schedules
                result = setup_ml_schedules()
                
                return Response({
                    'message': result,
                    'timestamp': timezone.now().isoformat()
                })
            
            elif action == 'stats':
                # Get detailed training statistics
                stats = AutoTrainingManager.get_training_stats()
                
                # Get data distribution by doctor
                doctor_data = {}
                consultations = Token.objects.filter(
                    status='completed',
                    consultation_start_time__isnull=False
                ).select_related('doctor')
                
                for token in consultations:
                    doctor_name = token.doctor.name
                    if doctor_name not in doctor_data:
                        doctor_data[doctor_name] = 0
                    doctor_data[doctor_name] += 1
                
                return Response({
                    'training_stats': stats,
                    'doctor_data_distribution': doctor_data,
                    'total_training_samples': consultations.count(),
                    'data_quality': 'All historical consultation data included'
                })
            
            else:
                return Response({
                    'error': 'Invalid action. Use: train, setup_schedules, or stats'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Training management error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DataQualityView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get data quality metrics for training"""
        try:
            # Total consultation data
            total_consultations = Token.objects.filter(
                status='completed',
                consultation_start_time__isnull=False
            ).count()
            
            # Data by time periods
            now = timezone.now()
            periods = {
                'last_24h': now - timezone.timedelta(days=1),
                'last_7d': now - timezone.timedelta(days=7),
                'last_30d': now - timezone.timedelta(days=30),
                'last_90d': now - timezone.timedelta(days=90)
            }
            
            period_data = {}
            for period_name, start_date in periods.items():
                count = Token.objects.filter(
                    status='completed',
                    consultation_start_time__isnull=False,
                    completed_at__gte=start_date
                ).count()
                period_data[period_name] = count
            
            # Data quality indicators
            quality_score = min(100, (total_consultations / 100) * 100)  # 100+ consultations = 100% score
            
            return Response({
                'total_consultations': total_consultations,
                'period_breakdown': period_data,
                'data_quality_score': round(quality_score, 1),
                'training_readiness': {
                    'ready': total_consultations >= 10,
                    'minimum_required': 10,
                    'recommended': 50,
                    'excellent': 100
                },
                'data_usage_policy': 'ALL historical data used for training',
                'update_frequency': 'Automatic retraining on new consultations'
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)