from django_q.tasks import schedule
from django_q.models import Schedule
from .waiting_time_predictor import waiting_time_predictor
from .auto_training_triggers import AutoTrainingManager
import logging

logger = logging.getLogger(__name__)

def train_waiting_time_model():
    """Nightly task to retrain the waiting time prediction model"""
    try:
        logger.info("Starting nightly model training...")
        success = waiting_time_predictor.train_model()
        
        if success:
            logger.info("Model training completed successfully")
            return "Model trained successfully"
        else:
            logger.error("Model training failed - insufficient data")
            return "Training failed - insufficient data"
            
    except Exception as e:
        logger.error(f"Model training error: {str(e)}")
        return f"Training error: {str(e)}"

def setup_ml_schedules():
    """Setup scheduled tasks for ML model training"""
    # Clear existing ML schedules
    Schedule.objects.filter(func='api.tasks_ml.train_waiting_time_model').delete()
    Schedule.objects.filter(name__startswith='auto_training_').delete()
    
    # Schedule nightly training at 2 AM (full retrain with all data)
    from datetime import datetime, time
    from django.utils import timezone
    
    # Calculate next 2 AM
    now = timezone.now()
    next_2am = now.replace(hour=2, minute=0, second=0, microsecond=0)
    if next_2am <= now:
        next_2am = next_2am + timezone.timedelta(days=1)
    
    schedule(
        'api.tasks_ml.train_waiting_time_model',
        schedule_type='D',  # Daily
        next_run=next_2am,
        name='nightly_model_training_full'
    )
    
    # Setup automatic training triggers
    AutoTrainingManager.setup_periodic_training()
    
    logger.info("ML schedules and auto-training setup completed")
    return "ML schedules and auto-training created"