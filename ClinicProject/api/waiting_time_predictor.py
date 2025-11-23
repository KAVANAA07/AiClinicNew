try:
    import pandas as pd
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    import joblib
    ML_AVAILABLE = True
except ImportError as e:
    ML_AVAILABLE = False
    print(f"ML dependencies not available: {e}")
    print("Install with: pip install pandas scikit-learn joblib")
import os
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Token, Doctor
import logging

logger = logging.getLogger(__name__)

class WaitingTimePredictor:
    def __init__(self):
        if not ML_AVAILABLE:
            self.model = None
            self.scaler = None
            self.model_path = 'waiting_time_model.pkl'
            self.scaler_path = 'waiting_time_scaler.pkl'
            return
        
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.model_path = 'waiting_time_model.pkl'
        self.scaler_path = 'waiting_time_scaler.pkl'
        
    def extract_features(self, tokens_data):
        """Extract features from token data for prediction"""
        features = []
        
        for token in tokens_data:
            # Time-based features
            hour = token['created_at'].hour
            day_of_week = token['created_at'].weekday()
            
            # Doctor workload features
            doctor_tokens_today = tokens_data.filter(
                doctor_id=token['doctor_id'],
                created_at__date=token['created_at'].date()
            ).count()
            
            # Queue position when token was created
            queue_position = tokens_data.filter(
                doctor_id=token['doctor_id'],
                created_at__date=token['created_at'].date(),
                created_at__lt=token['created_at']
            ).count() + 1
            
            features.append([
                hour,
                day_of_week,
                doctor_tokens_today,
                queue_position,
                token['doctor_id']
            ])
            
        return np.array(features)
    
    def get_early_completion_rate(self, doctor_id, weekday):
        """Get rate of early completions for doctor on specific weekday"""
        try:
            tokens = Token.objects.filter(
                doctor_id=doctor_id,
                appointment_date__week_day=weekday + 1,
                status='completed',
                completed_at__isnull=False,
                appointment_time__isnull=False,
                appointment_date__gte=timezone.now().date() - timedelta(days=60)
            )
            
            if not tokens.exists():
                return 0.0
            
            early_count = 0
            for token in tokens:
                expected = datetime.combine(token.appointment_date, token.appointment_time)
                if token.completed_at < expected:
                    early_count += 1
            
            return early_count / tokens.count()
        except:
            return 0.0
    
    def get_avg_early_time(self, doctor_id, weekday):
        """Get average early completion time for doctor on specific weekday"""
        try:
            tokens = Token.objects.filter(
                doctor_id=doctor_id,
                appointment_date__week_day=weekday + 1,
                status='completed',
                completed_at__isnull=False,
                appointment_time__isnull=False,
                appointment_date__gte=timezone.now().date() - timedelta(days=60)
            )
            
            early_times = []
            for token in tokens:
                expected = datetime.combine(token.appointment_date, token.appointment_time)
                actual = token.completed_at
                diff = (actual - expected).total_seconds() / 60
                if diff < 0:  # Early completion
                    early_times.append(abs(diff))
            
            return np.mean(early_times) if early_times else 0.0
        except:
            return 0.0
    
    def prepare_training_data(self, use_all_data=True, days_back=30):
        """Prepare training data from historical tokens including early completion patterns"""
        if use_all_data:
            tokens = Token.objects.filter(
                status='completed',
                completed_at__isnull=False
            ).select_related('doctor')
            logger.info(f"Using ALL consultation data: {tokens.count()} records")
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days_back)
            tokens = Token.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lt=end_date,
                status='completed',
                completed_at__isnull=False
            ).select_related('doctor')
            logger.info(f"Using recent data ({days_back} days): {tokens.count()} records")
        
        if tokens.count() < 10:
            logger.warning("Insufficient training data")
            return None, None
        
        features = []
        targets = []
        
        for token in tokens:
            # Calculate actual waiting time (can be negative for early completions)
            expected_time = datetime.combine(token.appointment_date, token.appointment_time) if token.appointment_time else token.created_at
            actual_time = token.completed_at
            waiting_time = (actual_time - expected_time).total_seconds() / 60
            
            # Extract enhanced features including early completion patterns
            hour = token.created_at.hour
            day_of_week = token.created_at.weekday()
            
            # Doctor workload that day
            doctor_tokens_today = Token.objects.filter(
                doctor=token.doctor,
                created_at__date=token.created_at.date()
            ).count()
            
            # Queue position
            queue_position = Token.objects.filter(
                doctor=token.doctor,
                created_at__date=token.created_at.date(),
                created_at__lt=token.created_at
            ).count() + 1
            
            # Early completion rate for this doctor/weekday
            early_completion_rate = self.get_early_completion_rate(token.doctor.id, day_of_week)
            
            # Average early time for this doctor/weekday
            avg_early_time = self.get_avg_early_time(token.doctor.id, day_of_week)
            
            features.append([
                hour,
                day_of_week,
                doctor_tokens_today,
                queue_position,
                token.doctor.id,
                early_completion_rate,
                avg_early_time
            ])
            targets.append(waiting_time)  # Include negative values for early completions
        
        return np.array(features), np.array(targets)
    
    def train_model(self):
        """Train the waiting time prediction model"""
        if not ML_AVAILABLE:
            logger.error("ML dependencies not available. Install pandas, scikit-learn, joblib")
            return False
            
        logger.info("Starting model training...")
        
        X, y = self.prepare_training_data(use_all_data=True)
        if X is None or len(X) < 10:
            logger.error("Insufficient training data")
            return False
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model with parameters suitable for handling negative values
        from sklearn.ensemble import RandomForestRegressor
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        logger.info(f"Model trained - MAE: {mae:.2f} minutes, R2: {r2:.3f}")
        
        # Save model
        self.save_model()
        return True
    
    def save_model(self):
        """Save trained model and scaler"""
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        logger.info("Model saved successfully")
    
    def load_model(self):
        """Load trained model and scaler"""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            return True
        return False
    
    def predict_waiting_time(self, doctor_id, current_time=None, for_appointment_time=None):
        """Predict waiting time for a patient arriving now or for a specific appointment"""
        if current_time is None:
            current_time = timezone.now()
        
        # Get current active queue
        current_queue = Token.objects.filter(
            doctor_id=doctor_id,
            created_at__date=current_time.date(),
            status__in=['waiting', 'confirmed', 'in_consultation']
        ).order_by('appointment_time', 'created_at')
        
        queue_count = current_queue.count()
        
        # PRIORITY FIX: If no one is waiting, return minimal time
        if queue_count == 0:
            return 5
        
        # Check if doctor is currently in consultation
        in_consultation = current_queue.filter(status='in_consultancy').exists()
        
        # Get real-time analytics for better prediction
        try:
            from .smart_queue_analytics import SmartQueueAnalytics
            analytics = SmartQueueAnalytics.calculate_actual_wait_times()
            
            # Use doctor-specific average if available
            doctor_avg = None
            doctor = Doctor.objects.get(id=doctor_id)
            if doctor.name in analytics.get('doctor_performance', {}):
                doctor_avg = analytics['doctor_performance'][doctor.name]['avg_wait_time']
        except:
            doctor_avg = None
        
        # If this is for a specific appointment time
        if for_appointment_time:
            patients_before = current_queue.filter(
                appointment_time__lt=for_appointment_time
            ).count()
            
            # CRITICAL FIX: If you're first (no patients before), minimal wait
            if patients_before == 0:
                return 10 if in_consultation else 5
            
            queue_position = patients_before + 1
        else:
            queue_position = queue_count + 1
        
        # ENHANCED CALCULATION with real-time data
        if queue_position == 1:
            return 10 if in_consultation else 5
        elif queue_position == 2:
            return 20 if in_consultation else 15
        else:
            # Use doctor's actual average or fallback to 12 minutes per patient
            per_patient_time = doctor_avg if doctor_avg and doctor_avg > 0 else 12
            base_time = 10 if in_consultation else 5
            return base_time + ((queue_position - 1) * per_patient_time)
        
        # Fallback to ML if available
        if not ML_AVAILABLE or not self.load_model():
            # Simple fallback calculation
            return max(5, queue_position * 12)
        
        # ML prediction (only if simple logic doesn't apply)
        doctor_tokens_today = Token.objects.filter(
            doctor_id=doctor_id,
            created_at__date=current_time.date()
        ).count()
        
        # Enhanced features including early completion patterns
        early_rate = self.get_early_completion_rate(doctor_id, current_time.weekday())
        avg_early = self.get_avg_early_time(doctor_id, current_time.weekday())
        
        features = np.array([[
            current_time.hour,
            current_time.weekday(),
            doctor_tokens_today,
            queue_position,
            doctor_id,
            early_rate,
            avg_early
        ]])
        
        features_scaled = self.scaler.transform(features)
        predicted_time = self.model.predict(features_scaled)[0]
        
        # Override ML if queue position is clear
        if queue_position <= 2:
            predicted_time = min(predicted_time, 20)
        
        # Handle negative predictions (early completions)
        if predicted_time < 0:
            predicted_time = max(predicted_time, -30)  # Max 30 minutes early
        else:
            predicted_time = max(5, min(120, predicted_time))
        
        logger.info(f"Wait time for doctor {doctor_id}: {predicted_time} min (pos: {queue_position}, queue: {queue_count})")
        
        return round(predicted_time)

# Global predictor instance
waiting_time_predictor = WaitingTimePredictor()