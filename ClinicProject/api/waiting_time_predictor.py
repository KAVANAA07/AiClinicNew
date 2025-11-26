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
                date__week_day=weekday + 1,
                status='completed',
                completed_at__isnull=False,
                appointment_time__isnull=False,
                date__gte=timezone.now().date() - timedelta(days=60)
            )
            
            if not tokens.exists():
                return 0.0
            
            early_count = 0
            for t in tokens:
                expected = timezone.make_aware(datetime.combine(t.date, t.appointment_time))
                if t.completed_at < expected:
                    early_count += 1
            
            return early_count / tokens.count()
        except:
            return 0.0
    
    def get_avg_early_time(self, doctor_id, weekday):
        """Get average early completion time for doctor on specific weekday"""
        try:
            tokens = Token.objects.filter(
                doctor_id=doctor_id,
                date__week_day=weekday + 1,
                status='completed',
                completed_at__isnull=False,
                appointment_time__isnull=False,
                date__gte=timezone.now().date() - timedelta(days=60)
            )
            
            early_times = []
            for t in tokens:
                expected = timezone.make_aware(datetime.combine(t.date, t.appointment_time))
                actual = t.completed_at
                diff = (actual - expected).total_seconds() / 60
                if diff < 0:  # Early completion
                    early_times.append(abs(diff))
            
            return np.mean(early_times) if early_times else 0.0
        except:
            return 0.0
    
    def get_daily_trend_factor(self, doctor_id, current_time):
        """Calculate real-time trend factor based on today's performance vs historical average"""
        try:
            today_date = current_time.date()
            
            # Get today's completed consultations
            today_completed = Token.objects.filter(
                doctor_id=doctor_id,
                date=today_date,
                status='completed',
                completed_at__isnull=False,
                appointment_time__isnull=False
            )
            
            if today_completed.count() < 2:  # Need at least 2 consultations for trend
                return 1.0  # Neutral factor
            
            # Calculate today's average consultation time
            today_times = []
            for t in today_completed:
                expected = timezone.make_aware(datetime.combine(t.date, t.appointment_time))
                actual = t.completed_at
                consultation_time = (actual - expected).total_seconds() / 60
                today_times.append(consultation_time)
            
            today_avg = np.mean(today_times)
            
            # Get historical average for this doctor on same weekday
            weekday = today_date.weekday()
            historical_tokens = Token.objects.filter(
                doctor_id=doctor_id,
                date__week_day=weekday + 1,
                status='completed',
                completed_at__isnull=False,
                appointment_time__isnull=False,
                date__gte=today_date - timedelta(days=60),
                date__lt=today_date  # Exclude today
            )
            
            if historical_tokens.count() < 5:  # Need historical data
                return 1.0
            
            historical_times = []
            for t in historical_tokens:
                expected = timezone.make_aware(datetime.combine(t.date, t.appointment_time))
                actual = t.completed_at
                consultation_time = (actual - expected).total_seconds() / 60
                historical_times.append(consultation_time)
            
            historical_avg = np.mean(historical_times)
            
            # Calculate trend factor
            if historical_avg != 0:
                trend_factor = today_avg / historical_avg
                # Limit extreme adjustments
                trend_factor = max(0.5, min(2.0, trend_factor))
                
                logger.info(f"Daily trend for doctor {doctor_id}: today_avg={today_avg:.1f}, historical_avg={historical_avg:.1f}, factor={trend_factor:.2f}")
                return trend_factor
            
            return 1.0
            
        except Exception as e:
            logger.error(f"Error calculating daily trend: {e}")
            return 1.0
    
    def prepare_training_data(self, use_all_data=True, days_back=30):
        """Prepare training data from historical tokens including early completion patterns"""
        if use_all_data:
            tokens = Token.objects.filter(
                status='Completed',
                completed_at__isnull=False,
                appointment_time__isnull=False,
                consultation_start_time__isnull=False
            ).select_related('doctor')
            logger.info(f"Using ALL consultation data: {tokens.count()} records")
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days_back)
            tokens = Token.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lt=end_date,
                status='Completed',
                completed_at__isnull=False,
                appointment_time__isnull=False,
                consultation_start_time__isnull=False
            ).select_related('doctor')
            logger.info(f"Using recent data ({days_back} days): {tokens.count()} records")
        
        if tokens.count() < 10:
            logger.warning("Insufficient training data")
            return None, None
        
        features = []
        targets = []
        
        for current_token in tokens:
            try:
                # Calculate actual waiting time from arrival to consultation start
                arrival_time = current_token.created_at
                consultation_start = current_token.consultation_start_time
                waiting_time = (consultation_start - arrival_time).total_seconds() / 60
                
                # Extract enhanced features including early completion patterns
                hour = current_token.created_at.hour
                day_of_week = current_token.created_at.weekday()
                
                # Doctor workload that day
                doctor_tokens_today = Token.objects.filter(
                    doctor=current_token.doctor,
                    created_at__date=current_token.created_at.date()
                ).count()
                
                # Queue position
                queue_position = Token.objects.filter(
                    doctor=current_token.doctor,
                    created_at__date=current_token.created_at.date(),
                    created_at__lt=current_token.created_at
                ).count() + 1
                
                features.append([
                    hour,
                    day_of_week,
                    doctor_tokens_today,
                    queue_position,
                    current_token.doctor.id
                ])
                targets.append(max(0, waiting_time))  # Ensure non-negative wait times
            except Exception as e:
                logger.error(f"Error processing token {current_token.id}: {e}")
                continue
        
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
        """Predict waiting time using improved ML model with enhanced features"""
        if current_time is None:
            current_time = timezone.now()
        
        # Get current active queue
        current_queue = Token.objects.filter(
            doctor_id=doctor_id,
            date=current_time.date(),
            status__in=['waiting', 'confirmed', 'in_consultancy']
        ).order_by('appointment_time', 'created_at')
        
        queue_count = current_queue.count()
        
        # Calculate queue position
        if for_appointment_time:
            patients_before = current_queue.filter(
                appointment_time__lt=for_appointment_time
            ).count()
            queue_position = patients_before + 1
        else:
            queue_position = queue_count + 1
        
        # PRIORITY: Use improved ML model
        if ML_AVAILABLE and self.load_model():
            try:
                # Enhanced feature extraction
                hour = current_time.hour
                minute = current_time.minute
                day_of_week = current_time.weekday()
                is_weekend = 1 if day_of_week >= 5 else 0
                
                # Appointment time features
                if for_appointment_time:
                    appt_hour = for_appointment_time.hour
                    appt_minute = for_appointment_time.minute
                else:
                    appt_hour = hour
                    appt_minute = minute
                
                # Doctor workload
                doctor_load = Token.objects.filter(
                    doctor_id=doctor_id,
                    date=current_time.date()
                ).count()
                
                # Time since clinic start
                clinic_start = current_time.replace(hour=9, minute=0, second=0)
                minutes_since_start = (current_time - clinic_start).total_seconds() / 60
                
                # Arrival offset (0 for new bookings)
                arrival_offset = 0
                
                features = np.array([[
                    hour,
                    minute,
                    day_of_week,
                    is_weekend,
                    appt_hour,
                    appt_minute,
                    queue_position,
                    doctor_load,
                    minutes_since_start,
                    arrival_offset,
                    doctor_id
                ]])
                
                features_scaled = self.scaler.transform(features)
                predicted_time = self.model.predict(features_scaled)[0]
                
                # Ensure reasonable range
                predicted_time = max(0, min(120, predicted_time))
                
                logger.info(f"ML prediction for doctor {doctor_id}: {predicted_time:.1f} min (queue: {queue_position})")
                return round(predicted_time)
                
            except Exception as e:
                logger.error(f"ML prediction failed: {e}")
        
        # Fallback only if ML completely fails
        if queue_count == 0:
            return 5
        
        result = max(5, min(60, queue_position * 10))
        logger.warning(f"Using fallback prediction for doctor {doctor_id}: {result} min")
        return result

# Global predictor instance
waiting_time_predictor = WaitingTimePredictor()