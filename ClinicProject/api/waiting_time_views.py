from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from .waiting_time_predictor import waiting_time_predictor
from .models import Token, Doctor
import logging

logger = logging.getLogger(__name__)

class PredictWaitingTimeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, doctor_id):
        """Get predicted waiting time for a specific doctor"""
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            appointment_time_str = request.query_params.get('appointment_time')
            appointment_time = None
            
            if appointment_time_str:
                try:
                    from datetime import datetime
                    appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
                except ValueError:
                    pass
            
            predicted_time = waiting_time_predictor.predict_waiting_time(
                doctor_id, 
                for_appointment_time=appointment_time
            )
            
            if predicted_time is None:
                return Response({
                    'error': 'Waiting time prediction not available. Model may not be trained yet.'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Get current queue info
            current_queue = Token.objects.filter(
                doctor_id=doctor_id,
                created_at__date=timezone.now().date(),
                status__in=['waiting', 'confirmed', 'in_consultation']
            ).count()
            
            return Response({
                'doctor_id': doctor_id,
                'doctor_name': doctor.name,
                'predicted_waiting_time_minutes': predicted_time,
                'current_queue_length': current_queue,
                'appointment_time': appointment_time_str,
                'prediction_timestamp': timezone.now().isoformat()
            })
            
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error predicting waiting time: {e}")
            return Response({'error': 'Failed to predict waiting time'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TrainModelView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Manually trigger model training"""
        try:
            # Only allow staff to trigger training
            if not (hasattr(request.user, 'doctor') or hasattr(request.user, 'receptionist') or request.user.is_staff):
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            success = waiting_time_predictor.train_model()
            
            if success:
                return Response({
                    'message': 'Model training completed successfully',
                    'timestamp': timezone.now().isoformat()
                })
            else:
                return Response({
                    'error': 'Model training failed - insufficient data or other error'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return Response({'error': 'Failed to train model'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WaitingTimeStatusView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get status of waiting time prediction system"""
        try:
            # Check if model files exist
            import os
            model_exists = os.path.exists(waiting_time_predictor.model_path)
            scaler_exists = os.path.exists(waiting_time_predictor.scaler_path)
            
            # Get training data count
            from datetime import timedelta
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            
            training_data_count = Token.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lt=end_date,
                status='completed',
                consultation_start_time__isnull=False
            ).count()
            
            return Response({
                'model_trained': model_exists and scaler_exists,
                'model_file_exists': model_exists,
                'scaler_file_exists': scaler_exists,
                'training_data_available': training_data_count,
                'minimum_data_required': 10,
                'ready_for_predictions': model_exists and scaler_exists and training_data_count >= 10
            })
            
        except Exception as e:
            logger.error(f"Error checking waiting time status: {e}")
            return Response({'error': 'Failed to check system status'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)