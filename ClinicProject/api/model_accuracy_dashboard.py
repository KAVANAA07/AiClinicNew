from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from .models import Token, Doctor
from .waiting_time_predictor import waiting_time_predictor, ML_AVAILABLE
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ModelAccuracyDashboardView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get comprehensive model accuracy metrics for judges"""
        try:
            if not ML_AVAILABLE:
                return Response({
                    'error': 'ML dependencies not available',
                    'install_command': 'pip install pandas scikit-learn joblib'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Calculate accuracy metrics
            accuracy_data = self._calculate_model_accuracy()
            
            # Get model performance over time
            performance_trend = self._get_performance_trend()
            
            # Get feature importance and model details
            model_details = self._get_model_details()
            
            # Get real-time predictions vs actual comparison
            prediction_comparison = self._get_prediction_comparison()
            
            return Response({
                'model_accuracy': accuracy_data,
                'performance_trend': performance_trend,
                'model_details': model_details,
                'prediction_comparison': prediction_comparison,
                'timestamp': timezone.now().isoformat(),
                'data_source': 'Real clinic consultation data',
                'model_type': 'Linear Regression with StandardScaler'
            })
            
        except Exception as e:
            logger.error(f"Accuracy dashboard error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _calculate_model_accuracy(self):
        """Calculate comprehensive accuracy metrics"""
        try:
            import pandas as pd
            import numpy as np
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
            
            # Get test data from last 7 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=7)
            
            test_tokens = Token.objects.filter(
                created_at__date__gte=start_date,
                status='completed',
                consultation_start_time__isnull=False,
                predicted_waiting_time__isnull=False
            )
            
            if test_tokens.count() < 5:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need at least 5 completed consultations with predictions',
                    'available_data': test_tokens.count()
                }
            
            # Extract actual vs predicted waiting times
            actual_times = []
            predicted_times = []
            
            for token in test_tokens:
                actual_wait = (token.consultation_start_time - token.created_at).total_seconds() / 60
                if actual_wait > 0:
                    actual_times.append(actual_wait)
                    predicted_times.append(token.predicted_waiting_time)
            
            if len(actual_times) < 5:
                return {'status': 'insufficient_valid_data'}
            
            actual_times = np.array(actual_times)
            predicted_times = np.array(predicted_times)
            
            # Calculate metrics
            mae = mean_absolute_error(actual_times, predicted_times)
            mse = mean_squared_error(actual_times, predicted_times)
            rmse = np.sqrt(mse)
            r2 = r2_score(actual_times, predicted_times)
            
            # Calculate accuracy percentage (within 10 minutes)
            within_10min = np.abs(actual_times - predicted_times) <= 10
            accuracy_10min = np.mean(within_10min) * 100
            
            # Calculate accuracy percentage (within 15 minutes)
            within_15min = np.abs(actual_times - predicted_times) <= 15
            accuracy_15min = np.mean(within_15min) * 100
            
            # Calculate MAPE (Mean Absolute Percentage Error)
            mape = np.mean(np.abs((actual_times - predicted_times) / actual_times)) * 100
            
            # F1-like score for classification (Good/Bad prediction)
            # Good prediction = within 15 minutes of actual
            true_positives = np.sum(within_15min)
            false_positives = np.sum(~within_15min)
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = precision  # Same for this binary case
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            return {
                'status': 'success',
                'sample_size': len(actual_times),
                'date_range': f"{start_date} to {end_date}",
                'metrics': {
                    'mae_minutes': round(mae, 2),
                    'rmse_minutes': round(rmse, 2),
                    'r2_score': round(r2, 3),
                    'mape_percentage': round(mape, 2),
                    'accuracy_within_10min': round(accuracy_10min, 1),
                    'accuracy_within_15min': round(accuracy_15min, 1),
                    'f1_score': round(f1_score, 3)
                },
                'interpretation': {
                    'mae': f"Average prediction error: {mae:.1f} minutes",
                    'accuracy': f"{accuracy_15min:.1f}% predictions within 15 minutes of actual",
                    'f1_score': f"F1 Score: {f1_score:.3f} (0=worst, 1=perfect)",
                    'model_quality': self._interpret_model_quality(mae, accuracy_15min, f1_score)
                }
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _interpret_model_quality(self, mae, accuracy_15min, f1_score):
        """Interpret model quality for judges"""
        if mae <= 10 and accuracy_15min >= 80 and f1_score >= 0.8:
            return "Excellent - Highly accurate predictions"
        elif mae <= 15 and accuracy_15min >= 70 and f1_score >= 0.7:
            return "Good - Reliable for clinical use"
        elif mae <= 20 and accuracy_15min >= 60 and f1_score >= 0.6:
            return "Fair - Acceptable with room for improvement"
        else:
            return "Poor - Needs more training data or feature engineering"
    
    def _get_performance_trend(self):
        """Get model performance over time"""
        try:
            # Get daily accuracy for last 14 days
            daily_performance = []
            
            for i in range(14):
                date = timezone.now().date() - timedelta(days=i)
                
                day_tokens = Token.objects.filter(
                    created_at__date=date,
                    status='completed',
                    consultation_start_time__isnull=False,
                    predicted_waiting_time__isnull=False
                )
                
                if day_tokens.count() >= 3:
                    actual_times = []
                    predicted_times = []
                    
                    for token in day_tokens:
                        actual_wait = (token.consultation_start_time - token.created_at).total_seconds() / 60
                        if actual_wait > 0:
                            actual_times.append(actual_wait)
                            predicted_times.append(token.predicted_waiting_time)
                    
                    if len(actual_times) >= 3:
                        import numpy as np
                        from sklearn.metrics import mean_absolute_error
                        
                        mae = mean_absolute_error(actual_times, predicted_times)
                        within_15min = np.mean(np.abs(np.array(actual_times) - np.array(predicted_times)) <= 15) * 100
                        
                        daily_performance.append({
                            'date': date.isoformat(),
                            'mae_minutes': round(mae, 2),
                            'accuracy_15min': round(within_15min, 1),
                            'sample_size': len(actual_times)
                        })
            
            return daily_performance
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_model_details(self):
        """Get detailed model information"""
        return {
            'algorithm': 'Linear Regression',
            'preprocessing': 'StandardScaler for feature normalization',
            'features': [
                'Hour of day (0-23)',
                'Day of week (0-6)',
                'Doctor workload (tokens today)',
                'Queue position (1-N)',
                'Doctor ID (categorical)'
            ],
            'training_frequency': 'Nightly at 2:00 AM',
            'training_data_window': '30 days of historical consultations',
            'minimum_training_samples': 10,
            'prediction_bounds': '5-240 minutes',
            'model_files': [
                'waiting_time_model.pkl (trained model)',
                'waiting_time_scaler.pkl (feature scaler)'
            ]
        }
    
    def _get_prediction_comparison(self):
        """Get recent predictions vs actual outcomes"""
        try:
            # Get last 10 completed consultations with predictions
            recent_tokens = Token.objects.filter(
                status='completed',
                consultation_start_time__isnull=False,
                predicted_waiting_time__isnull=False
            ).order_by('-completed_at')[:10]
            
            comparisons = []
            for token in recent_tokens:
                actual_wait = (token.consultation_start_time - token.created_at).total_seconds() / 60
                predicted_wait = token.predicted_waiting_time
                error = abs(actual_wait - predicted_wait)
                
                comparisons.append({
                    'token_id': token.id,
                    'doctor': token.doctor.name,
                    'date': token.created_at.date().isoformat(),
                    'predicted_minutes': predicted_wait,
                    'actual_minutes': round(actual_wait, 1),
                    'error_minutes': round(error, 1),
                    'accuracy_status': 'Good' if error <= 15 else 'Poor'
                })
            
            return comparisons
            
        except Exception as e:
            return {'error': str(e)}

class ModelTrainingLogView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get model training history and logs"""
        try:
            # Get training data statistics
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            
            training_tokens = Token.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lt=end_date,
                status='completed',
                consultation_start_time__isnull=False
            )
            
            # Group by doctor
            doctor_stats = {}
            for token in training_tokens:
                doctor_id = token.doctor.id
                if doctor_id not in doctor_stats:
                    doctor_stats[doctor_id] = {
                        'doctor_name': token.doctor.name,
                        'consultation_count': 0,
                        'avg_waiting_time': 0,
                        'waiting_times': []
                    }
                
                waiting_time = (token.consultation_start_time - token.created_at).total_seconds() / 60
                if waiting_time > 0:
                    doctor_stats[doctor_id]['consultation_count'] += 1
                    doctor_stats[doctor_id]['waiting_times'].append(waiting_time)
            
            # Calculate averages
            for doctor_id in doctor_stats:
                if doctor_stats[doctor_id]['waiting_times']:
                    doctor_stats[doctor_id]['avg_waiting_time'] = round(
                        sum(doctor_stats[doctor_id]['waiting_times']) / len(doctor_stats[doctor_id]['waiting_times']), 1
                    )
            
            return Response({
                'training_period': f"{start_date} to {end_date}",
                'total_training_samples': training_tokens.count(),
                'doctor_statistics': list(doctor_stats.values()),
                'data_quality': {
                    'sufficient_data': training_tokens.count() >= 10,
                    'recommendation': 'Good' if training_tokens.count() >= 50 else 'Need more data for better accuracy'
                }
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)