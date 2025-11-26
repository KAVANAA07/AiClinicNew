"""
Improved ML Model Training System for Waiting Time Prediction
Generates realistic data and trains with advanced features
"""
import os
import sys
import django
import numpy as np
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from django.utils import timezone
from api.models import Token, Doctor, Patient
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

class ImprovedModelTrainer:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = 'waiting_time_model.pkl'
        self.scaler_path = 'waiting_time_scaler.pkl'
    
    def generate_realistic_data(self, days=90, min_tokens=500):
        """Generate realistic training data with diverse patterns"""
        print("Generating realistic training data...")
        
        doctors = list(Doctor.objects.all()[:5])
        patients = list(Patient.objects.all())
        
        if not doctors or not patients:
            print("ERROR: Need doctors and patients in database")
            return False
        
        # Clear old training data
        Token.objects.filter(token_number__startswith='TRAIN').delete()
        
        start_date = timezone.now() - timedelta(days=days)
        tokens_created = 0
        token_counter = 0
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # Skip weekends (20% chance)
            if current_date.weekday() >= 5 and random.random() < 0.8:
                continue
            
            for doctor in doctors:
                # Variable workload: 8-20 patients/day
                num_patients = random.randint(8, 20)
                clinic_start = current_date.replace(hour=9, minute=0, second=0)
                
                # Doctor efficiency varies (0.6=fast, 1.4=slow)
                doctor_efficiency = random.uniform(0.6, 1.4)
                
                # Day-specific factors
                is_busy_day = random.random() < 0.3  # 30% busy days
                has_emergency = random.random() < 0.15  # 15% emergency interruptions
                
                for i in range(num_patients):
                    patient = random.choice(patients)
                    
                    # Appointment scheduling (15-min slots)
                    slot_time = clinic_start + timedelta(minutes=i * 15, seconds=token_counter)
                    
                    # REALISTIC ARRIVAL PATTERNS
                    arrival_pattern = random.choices(
                        ['very_early', 'early', 'ontime', 'late', 'very_late', 'no_show'],
                        weights=[0.08, 0.25, 0.40, 0.18, 0.07, 0.02]
                    )[0]
                    
                    if arrival_pattern == 'no_show':
                        continue  # Skip no-shows
                    
                    arrival_offsets = {
                        'very_early': random.randint(-30, -15),
                        'early': random.randint(-14, -3),
                        'ontime': random.randint(-2, 5),
                        'late': random.randint(6, 20),
                        'very_late': random.randint(21, 45)
                    }
                    
                    actual_arrival = slot_time + timedelta(minutes=arrival_offsets[arrival_pattern])
                    
                    # WAITING TIME CALCULATION (realistic factors)
                    queue_position = i + 1
                    
                    # Base wait depends on position
                    if queue_position == 1:
                        base_wait = random.randint(0, 5)  # First patient minimal wait
                    elif queue_position <= 3:
                        base_wait = random.randint(2, 12)  # Early patients
                    elif queue_position <= 8:
                        base_wait = queue_position * random.randint(3, 8)  # Mid-day
                    else:
                        base_wait = queue_position * random.randint(5, 12)  # Late day accumulation
                    
                    # Apply realistic modifiers
                    modifiers = []
                    
                    # Doctor efficiency impact
                    modifiers.append(base_wait * (doctor_efficiency - 1.0))
                    
                    # Busy day impact
                    if is_busy_day:
                        modifiers.append(random.randint(5, 15))
                    
                    # Emergency interruption
                    if has_emergency and i > num_patients // 2:
                        modifiers.append(random.randint(10, 25))
                    
                    # Time of day factor (afternoon slower)
                    hour = (clinic_start + timedelta(minutes=i * 15)).hour
                    if hour >= 14:
                        modifiers.append(random.randint(2, 8))
                    
                    # Patient complexity (random)
                    if random.random() < 0.2:  # 20% complex cases
                        modifiers.append(random.randint(5, 15))
                    
                    # Early arrival bonus (less wait if early)
                    if arrival_pattern in ['very_early', 'early']:
                        modifiers.append(random.randint(-8, -2))
                    
                    # Late arrival penalty
                    if arrival_pattern in ['late', 'very_late']:
                        modifiers.append(random.randint(3, 10))
                    
                    total_wait = int(base_wait + sum(modifiers))
                    total_wait = max(0, min(120, total_wait))  # Cap at 0-120 min
                    
                    consultation_start = actual_arrival + timedelta(minutes=total_wait)
                    
                    # Consultation duration (realistic distribution)
                    consultation_duration = random.choices(
                        [5, 8, 10, 12, 15, 18, 20, 25, 30, 40],
                        weights=[0.10, 0.15, 0.20, 0.18, 0.15, 0.10, 0.06, 0.04, 0.01, 0.01]
                    )[0]
                    
                    completed_at = consultation_start + timedelta(minutes=consultation_duration)
                    
                    try:
                        token = Token.objects.create(
                            patient=patient,
                            doctor=doctor,
                            token_number=f"TRAIN{token_counter:06d}",
                            status='Completed',
                            appointment_time=slot_time.time(),
                            consultation_start_time=consultation_start,
                            completed_at=completed_at,
                            date=current_date.date()
                        )
                        Token.objects.filter(id=token.id).update(created_at=actual_arrival)
                        tokens_created += 1
                        token_counter += 1
                    except Exception as e:
                        token_counter += 1
                        continue
        
        print(f"Created {tokens_created} realistic training tokens")
        
        if tokens_created < min_tokens:
            print(f"Warning: Only {tokens_created} tokens created (minimum {min_tokens} recommended)")
            return False
        
        self._show_data_statistics()
        return True
    
    def _show_data_statistics(self):
        """Display data distribution statistics"""
        tokens = Token.objects.filter(status='Completed', token_number__startswith='TRAIN')
        
        wait_times = []
        for t in tokens:
            if t.created_at and t.consultation_start_time:
                wait = (t.consultation_start_time - t.created_at).total_seconds() / 60
                wait_times.append(max(0, wait))
        
        if not wait_times:
            return
        
        print(f"\nData Statistics:")
        print(f"   Total samples: {len(wait_times)}")
        print(f"   Mean wait: {np.mean(wait_times):.1f} min")
        print(f"   Median wait: {np.median(wait_times):.1f} min")
        print(f"   Std dev: {np.std(wait_times):.1f} min")
        print(f"   Range: {np.min(wait_times):.0f} - {np.max(wait_times):.0f} min")
        
        # Distribution
        bins = [0, 10, 20, 30, 60, 120]
        labels = ['0-10', '11-20', '21-30', '31-60', '61+']
        for i in range(len(bins)-1):
            count = sum(1 for w in wait_times if bins[i] <= w < bins[i+1])
            pct = (count / len(wait_times)) * 100
            print(f"   {labels[i]} min: {count} ({pct:.1f}%)")
    
    def extract_features(self, tokens):
        """Extract enhanced features for ML model"""
        features = []
        targets = []
        
        for token in tokens:
            try:
                # Calculate actual wait time
                wait_time = (token.consultation_start_time - token.created_at).total_seconds() / 60
                wait_time = max(0, wait_time)
                
                # Time features
                hour = token.created_at.hour
                minute = token.created_at.minute
                day_of_week = token.created_at.weekday()
                is_weekend = 1 if day_of_week >= 5 else 0
                
                # Appointment time features
                appt_hour = token.appointment_time.hour if token.appointment_time else hour
                appt_minute = token.appointment_time.minute if token.appointment_time else minute
                
                # Queue position (tokens before this one on same day)
                queue_pos = Token.objects.filter(
                    doctor=token.doctor,
                    date=token.date,
                    created_at__lt=token.created_at
                ).count() + 1
                
                # Doctor workload that day
                doctor_load = Token.objects.filter(
                    doctor=token.doctor,
                    date=token.date
                ).count()
                
                # Time since clinic start
                clinic_start = token.created_at.replace(hour=9, minute=0, second=0)
                minutes_since_start = (token.created_at - clinic_start).total_seconds() / 60
                
                # Arrival timing (early/late relative to appointment)
                if token.appointment_time:
                    scheduled = datetime.combine(token.date, token.appointment_time)
                    if scheduled.tzinfo is None:
                        scheduled = timezone.make_aware(scheduled)
                    arrival_offset = (token.created_at - scheduled).total_seconds() / 60
                else:
                    arrival_offset = 0
                
                features.append([
                    hour,
                    minute,
                    day_of_week,
                    is_weekend,
                    appt_hour,
                    appt_minute,
                    queue_pos,
                    doctor_load,
                    minutes_since_start,
                    arrival_offset,
                    token.doctor.id
                ])
                
                targets.append(wait_time)
                
            except Exception as e:
                continue
        
        return np.array(features), np.array(targets)
    
    def train_model(self):
        """Train improved ML model with cross-validation"""
        print("\nTraining improved ML model...")
        
        # Get training data
        tokens = Token.objects.filter(
            status='Completed',
            token_number__startswith='TRAIN',
            consultation_start_time__isnull=False,
            created_at__isnull=False
        ).select_related('doctor')
        
        if tokens.count() < 100:
            print(f"ERROR: Insufficient data: {tokens.count()} tokens (need 100+)")
            return False
        
        print(f"Using {tokens.count()} training samples")
        
        # Extract features
        X, y = self.extract_features(tokens)
        
        if len(X) < 100:
            print(f"ERROR: Feature extraction failed: only {len(X)} valid samples")
            return False
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Gradient Boosting model (better for complex patterns)
        print("Training Gradient Boosting Regressor...")
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=10,
            min_samples_leaf=4,
            random_state=42,
            verbose=0
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        # Metrics
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train, 
            cv=5, scoring='neg_mean_absolute_error'
        )
        cv_mae = -cv_scores.mean()
        
        print(f"\nModel Performance:")
        print(f"   Training MAE: {train_mae:.2f} min")
        print(f"   Test MAE: {test_mae:.2f} min")
        print(f"   Training RMSE: {train_rmse:.2f} min")
        print(f"   Test RMSE: {test_rmse:.2f} min")
        print(f"   Training R²: {train_r2:.3f}")
        print(f"   Test R²: {test_r2:.3f}")
        print(f"   Cross-Val MAE: {cv_mae:.2f} min")
        
        # Quality check
        if test_mae > 15:
            print(f"Warning: Test MAE is high ({test_mae:.2f} min)")
        if test_r2 < 0.5:
            print(f"Warning: Test R2 is low ({test_r2:.3f})")
        
        # Save model
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        print(f"\nModel saved to {self.model_path}")
        
        return True

def main():
    print("=" * 60)
    print("IMPROVED WAITING TIME PREDICTION MODEL TRAINER")
    print("=" * 60)
    
    trainer = ImprovedModelTrainer()
    
    # Step 1: Generate realistic data
    if not trainer.generate_realistic_data(days=90, min_tokens=500):
        print("\nERROR: Data generation failed")
        return
    
    # Step 2: Train model
    if not trainer.train_model():
        print("\nERROR: Model training failed")
        return
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE - Model ready for production!")
    print("=" * 60)

if __name__ == '__main__':
    main()
