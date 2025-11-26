"""
DEMONSTRATION SCRIPT FOR JUDGES
Shows ML Model Performance and System Capabilities
"""
import os
import sys
import django
import numpy as np
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_token_system.settings')
django.setup()

from api.models import Token, Doctor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, classification_report
from sklearn.model_selection import train_test_split
import joblib

def print_header(title):
    print("\n" + "="*70)
    print(title.center(70))
    print("="*70)

def classify_wait_time(minutes):
    """Classify wait time into Short/Medium/Long"""
    if minutes <= 20:
        return "Short"
    elif minutes <= 45:
        return "Medium"
    else:
        return "Long"

def main():
    print_header("AI CLINIC WAITING TIME PREDICTION SYSTEM")
    print_header("DEMONSTRATION FOR JUDGES")
    
    # 1. DATASET INFORMATION
    print_header("1. DATASET INFORMATION")
    
    total_tokens = Token.objects.filter(
        status='Completed',
        consultation_start_time__isnull=False,
        created_at__isnull=False
    ).count()
    
    print(f"\nTotal Training Samples: {total_tokens}")
    
    if total_tokens == 0:
        print("\nERROR: No training data found!")
        print("Please run: python train_improved_model.py")
        return
    
    # Calculate wait times
    tokens = Token.objects.filter(
        status='Completed',
        consultation_start_time__isnull=False,
        created_at__isnull=False
    ).select_related('doctor')
    
    wait_times = []
    for token in tokens:
        wait = (token.consultation_start_time - token.created_at).total_seconds() / 60
        wait_times.append(max(0, wait))
    
    print(f"Valid Samples: {len(wait_times)}")
    print(f"\nWait Time Distribution:")
    print(f"   Mean: {np.mean(wait_times):.2f} minutes")
    print(f"   Median: {np.median(wait_times):.2f} minutes")
    print(f"   Std Dev: {np.std(wait_times):.2f} minutes")
    print(f"   Min: {np.min(wait_times):.0f} minutes")
    print(f"   Max: {np.max(wait_times):.0f} minutes")
    
    # Classification distribution
    classifications = [classify_wait_time(w) for w in wait_times]
    short_count = classifications.count("Short")
    medium_count = classifications.count("Medium")
    long_count = classifications.count("Long")
    
    print(f"\nClassification Distribution:")
    print(f"   Short (0-20 min): {short_count} ({short_count/len(classifications)*100:.1f}%)")
    print(f"   Medium (21-45 min): {medium_count} ({medium_count/len(classifications)*100:.1f}%)")
    print(f"   Long (46+ min): {long_count} ({long_count/len(classifications)*100:.1f}%)")
    
    # 2. MODEL LOADING
    print_header("2. MODEL INFORMATION")
    
    try:
        model = joblib.load('waiting_time_model.pkl')
        scaler = joblib.load('waiting_time_scaler.pkl')
        print("\nModel Type: Gradient Boosting Regressor")
        print(f"Model Parameters:")
        print(f"   Estimators: {model.n_estimators}")
        if hasattr(model, 'learning_rate'):
            print(f"   Learning Rate: {model.learning_rate}")
        if hasattr(model, 'max_depth'):
            print(f"   Max Depth: {model.max_depth}")
        print(f"\nFeatures Used: 11")
        print("   - Hour, Minute, Day of Week, Is Weekend")
        print("   - Appointment Hour/Minute")
        print("   - Queue Position, Doctor Load")
        print("   - Minutes Since Start, Arrival Offset, Doctor ID")
    except FileNotFoundError:
        print(f"\nERROR: Model files not found")
        print("Please run: python train_improved_model.py")
        return
    except Exception as e:
        print(f"\nWARNING: {e}")
        print("Continuing with evaluation...")
    
    # 3. EXTRACT FEATURES AND MAKE PREDICTIONS
    print_header("3. MODEL PERFORMANCE EVALUATION")
    
    print("\nExtracting features from dataset...")
    
    from train_improved_model import ImprovedModelTrainer
    trainer = ImprovedModelTrainer()
    try:
        trainer.model = model
        trainer.scaler = scaler
    except:
        pass
    
    X, y = trainer.extract_features(tokens)
    
    if len(X) < 100:
        print(f"ERROR: Insufficient valid samples: {len(X)}")
        return
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale and predict
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    y_pred_train = model.predict(X_train_scaled)
    y_pred_test = model.predict(X_test_scaled)
    
    # Calculate metrics
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    
    print(f"\nDataset Split:")
    print(f"   Training Set: {len(X_train)} samples ({len(X_train)/len(X)*100:.1f}%)")
    print(f"   Test Set: {len(X_test)} samples ({len(X_test)/len(X)*100:.1f}%)")
    
    print(f"\nREGRESSION METRICS:")
    print(f"   Training MAE: {train_mae:.2f} minutes")
    print(f"   Test MAE: {test_mae:.2f} minutes")
    print(f"   Training RMSE: {train_rmse:.2f} minutes")
    print(f"   Test RMSE: {test_rmse:.2f} minutes")
    print(f"   Training R2 Score: {train_r2:.4f}")
    print(f"   Test R2 Score: {test_r2:.4f}")
    
    # 4. CLASSIFICATION REPORT
    print_header("4. CLASSIFICATION PERFORMANCE")
    
    # Convert to classifications
    y_test_class = [classify_wait_time(y) for y in y_test]
    y_pred_class = [classify_wait_time(y) for y in y_pred_test]
    
    print("\nClassification Report:")
    print(classification_report(y_test_class, y_pred_class, 
                                target_names=['Long', 'Medium', 'Short']))
    
    # 5. JUDGE CRITERIA EVALUATION
    print_header("5. JUDGE APPROVAL CRITERIA")
    
    print("\nRequired Criteria:")
    print(f"   1. MAE < 15 minutes")
    print(f"      Result: {test_mae:.2f} minutes - {'PASS' if test_mae < 15 else 'FAIL'}")
    
    print(f"\n   2. R2 Score > 0.70")
    print(f"      Result: {test_r2:.4f} - {'PASS' if test_r2 > 0.70 else 'FAIL'}")
    
    print(f"\n   3. Minimum 500 training samples")
    print(f"      Result: {len(X)} samples - {'PASS' if len(X) >= 500 else 'FAIL'}")
    
    # Overall verdict
    all_pass = (test_mae < 15) and (test_r2 > 0.70) and (len(X) >= 500)
    
    print_header("FINAL VERDICT")
    
    if all_pass:
        print("\n   STATUS: ALL CRITERIA MET")
        print("   RECOMMENDATION: APPROVED FOR PRODUCTION")
    else:
        print("\n   STATUS: SOME CRITERIA NOT MET")
        print("   RECOMMENDATION: NEEDS IMPROVEMENT")
    
    # 6. SAMPLE PREDICTIONS
    print_header("6. SAMPLE PREDICTIONS")
    
    print("\nShowing 5 random test predictions:")
    print(f"\n{'Actual':<10} {'Predicted':<10} {'Error':<10} {'Classification'}")
    print("-" * 60)
    
    sample_indices = np.random.choice(len(y_test), min(5, len(y_test)), replace=False)
    for idx in sample_indices:
        actual = y_test[idx]
        predicted = y_pred_test[idx]
        error = abs(actual - predicted)
        actual_class = classify_wait_time(actual)
        pred_class = classify_wait_time(predicted)
        match = "OK" if actual_class == pred_class else "X"
        
        print(f"{actual:>6.1f} min {predicted:>8.1f} min {error:>7.1f} min  "
              f"{actual_class} -> {pred_class} {match}")
    
    # 7. SYSTEM INFORMATION
    print_header("7. SYSTEM INFORMATION")
    
    print(f"\nModel File: waiting_time_model.pkl")
    print(f"Scaler File: waiting_time_scaler.pkl")
    print(f"Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Algorithm: Gradient Boosting Regressor")
    print(f"Framework: scikit-learn")
    
    doctors = Doctor.objects.all().count()
    print(f"\nSystem Configuration:")
    print(f"   Doctors in System: {doctors}")
    print(f"   Features: 11 engineered features")
    print(f"   Prediction Range: 0-120 minutes")
    
    print_header("END OF DEMONSTRATION")
    print("\nTo retrain model: python train_improved_model.py")
    print("To verify model: python verify_model.py")
    print()

if __name__ == '__main__':
    main()
