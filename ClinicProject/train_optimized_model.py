import os
import sys
import django
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token

def train_optimized_model():
    """Train optimized model with better features for MAE <= 14 minutes"""
    
    print("Loading training data...")
    tokens = Token.objects.filter(
        status='Completed',
        completed_at__isnull=False,
        appointment_time__isnull=False,
        consultation_start_time__isnull=False
    ).select_related('doctor').order_by('created_at')
    
    print(f"Found {tokens.count()} completed tokens")
    
    features = []
    targets = []
    
    for token in tokens:
        # Calculate actual wait time
        wait_time = (token.consultation_start_time - token.created_at).total_seconds() / 60
        wait_time = max(0, wait_time)
        
        # Enhanced features
        hour = token.created_at.hour
        day_of_week = token.created_at.weekday()
        
        # Queue position that day
        queue_pos = Token.objects.filter(
            doctor=token.doctor,
            created_at__date=token.created_at.date(),
            created_at__lt=token.created_at
        ).count() + 1
        
        # Total patients that day (workload)
        total_patients = Token.objects.filter(
            doctor=token.doctor,
            created_at__date=token.created_at.date()
        ).count()
        
        # Historical average wait for this doctor at this hour
        hist_tokens = Token.objects.filter(
            doctor=token.doctor,
            created_at__hour=hour,
            created_at__date__lt=token.created_at.date(),
            status='Completed'
        )[:50]  # Last 50 similar appointments
        
        if hist_tokens:
            hist_waits = []
            for ht in hist_tokens:
                hw = (ht.consultation_start_time - ht.created_at).total_seconds() / 60
                hist_waits.append(max(0, hw))
            avg_hist_wait = np.mean(hist_waits) if hist_waits else 20
        else:
            avg_hist_wait = 20
        
        # Historical average for this queue position
        hist_queue_tokens = Token.objects.filter(
            doctor=token.doctor,
            created_at__date__lt=token.created_at.date(),
            status='Completed'
        )
        
        queue_waits = []
        for ht in hist_queue_tokens[:100]:
            qp = Token.objects.filter(
                doctor=ht.doctor,
                created_at__date=ht.created_at.date(),
                created_at__lt=ht.created_at
            ).count() + 1
            if abs(qp - queue_pos) <= 2:  # Similar queue position
                hw = (ht.consultation_start_time - ht.created_at).total_seconds() / 60
                queue_waits.append(max(0, hw))
        
        avg_queue_wait = np.mean(queue_waits) if queue_waits else 20
        
        features.append([
            hour,
            day_of_week,
            queue_pos,
            total_patients,
            avg_hist_wait,
            avg_queue_wait,
            token.doctor.id
        ])
        targets.append(wait_time)
    
    X = np.array(features)
    y = np.array(targets)
    
    print(f"\nPrepared {len(X)} training samples")
    print(f"Average wait time: {np.mean(y):.1f} minutes")
    print(f"Wait time range: {np.min(y):.0f}-{np.max(y):.0f} minutes")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Gradient Boosting model (better for this task)
    print("\nTraining Gradient Boosting model...")
    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=5,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n{'='*70}")
    print(f"MODEL PERFORMANCE")
    print(f"{'='*70}")
    print(f"MAE:  {mae:.2f} minutes")
    print(f"R2:   {r2:.4f} ({r2*100:.2f}%)")
    print(f"{'='*70}")
    
    if mae <= 14:
        print("✓ TARGET ACHIEVED: MAE <= 14 minutes!")
    else:
        print(f"✗ Need improvement: MAE should be <= 14 (current: {mae:.2f})")
    
    # Save model
    joblib.dump(model, 'waiting_time_model.pkl')
    joblib.dump(scaler, 'waiting_time_scaler.pkl')
    print("\nModel saved successfully!")
    
    return mae, r2

if __name__ == '__main__':
    train_optimized_model()
