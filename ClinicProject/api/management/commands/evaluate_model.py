from django.core.management.base import BaseCommand
from api.waiting_time_predictor import waiting_time_predictor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics import accuracy_score, f1_score, classification_report
import numpy as np

class Command(BaseCommand):
    help = 'Evaluate waiting time prediction model - Show Accuracy & F1 Score'

    def handle(self, *args, **options):
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("AI CLINIC - MODEL EVALUATION"))
        self.stdout.write("="*70)
        
        # Load data
        self.stdout.write("\nLoading training data...")
        X, y = waiting_time_predictor.prepare_training_data(use_all_data=True)
        
        if X is None or len(X) < 10:
            self.stdout.write(self.style.ERROR("❌ Insufficient training data"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(X)} samples"))
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.stdout.write("\nTraining model...")
        success = waiting_time_predictor.train_model()
        
        if not success:
            self.stdout.write(self.style.ERROR("❌ Model training failed"))
            return
        
        self.stdout.write(self.style.SUCCESS("Model trained successfully"))
        
        # Make predictions
        waiting_time_predictor.load_model()
        X_test_scaled = waiting_time_predictor.scaler.transform(X_test)
        y_pred = waiting_time_predictor.model.predict(X_test_scaled)
        
        # ═══════════════════════════════════════════════════════════
        # REGRESSION METRICS
        # ═══════════════════════════════════════════════════════════
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("REGRESSION METRICS (Continuous Prediction)"))
        self.stdout.write("="*70)
        self.stdout.write(f"\nMean Absolute Error (MAE):     {mae:.2f} minutes")
        self.stdout.write(f"   -> Predictions are off by {mae:.2f} minutes on average")
        self.stdout.write(f"\nRoot Mean Squared Error (RMSE): {rmse:.2f} minutes")
        self.stdout.write(f"\nR2 Score:                       {r2:.4f} ({r2*100:.2f}%)")
        self.stdout.write(f"   -> Model explains {r2*100:.2f}% of variance")
        self.stdout.write(f"\nMAPE:                           {mape:.2f}%")
        
        # ═══════════════════════════════════════════════════════════
        # CLASSIFICATION METRICS (ACCURACY & F1 SCORE)
        # ═══════════════════════════════════════════════════════════
        def categorize_wait_time(minutes):
            if minutes <= 15:
                return 'Short'
            elif minutes <= 30:
                return 'Medium'
            else:
                return 'Long'
        
        y_test_cat = [categorize_wait_time(y) for y in y_test]
        y_pred_cat = [categorize_wait_time(y) for y in y_pred]
        
        accuracy = accuracy_score(y_test_cat, y_pred_cat)
        f1 = f1_score(y_test_cat, y_pred_cat, average='weighted')
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("CLASSIFICATION METRICS (For Judges)"))
        self.stdout.write("="*70)
        self.stdout.write(f"\nACCURACY SCORE: {accuracy:.4f} ({accuracy*100:.2f}%)")
        self.stdout.write(f"   -> Model correctly predicts category {accuracy*100:.2f}% of time")
        self.stdout.write(f"\nF1 SCORE:       {f1:.4f} ({f1*100:.2f}%)")
        self.stdout.write(f"   -> Harmonic mean of precision & recall")
        
        # Detailed classification report
        self.stdout.write("\n" + "="*70)
        self.stdout.write("DETAILED CLASSIFICATION REPORT:")
        self.stdout.write("="*70)
        self.stdout.write("\n" + classification_report(y_test_cat, y_pred_cat))
        
        # ═══════════════════════════════════════════════════════════
        # FINAL SUMMARY
        # ═══════════════════════════════════════════════════════════
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("FINAL SUMMARY FOR JUDGES"))
        self.stdout.write("="*70)
        self.stdout.write(f"\nDataset: {len(X)} samples ({len(X_train)} train, {len(X_test)} test)")
        self.stdout.write(f"\nKey Metrics:")
        self.stdout.write(f"   - Accuracy:  {accuracy*100:.2f}%")
        self.stdout.write(f"   - F1 Score:  {f1*100:.2f}%")
        self.stdout.write(f"   - R2 Score:  {r2*100:.2f}%")
        self.stdout.write(f"   - MAE:       {mae:.2f} minutes")
        
        # Performance rating
        self.stdout.write(f"\nPerformance Rating:")
        if accuracy >= 0.85 and r2 >= 0.80:
            self.stdout.write(self.style.SUCCESS("   EXCELLENT - Production Ready!"))
        elif accuracy >= 0.75 and r2 >= 0.70:
            self.stdout.write(self.style.SUCCESS("   GOOD - Performs Well"))
        elif accuracy >= 0.65 and r2 >= 0.60:
            self.stdout.write(self.style.WARNING("   FAIR - Needs Improvement"))
        else:
            self.stdout.write(self.style.ERROR("   POOR - Needs Retraining"))
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("Evaluation Complete!"))
        self.stdout.write("="*70)
