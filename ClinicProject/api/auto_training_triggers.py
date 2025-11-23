from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Token
from .waiting_time_predictor import waiting_time_predictor
from django_q.tasks import async_task
import logging

logger = logging.getLogger(__name__)

last_training_trigger = None
TRAINING_COOLDOWN_HOURS = 6

@receiver(post_save, sender=Token)
def trigger_model_retraining(sender, instance, created, **kwargs):
    global last_training_trigger
    
    if instance.status == 'completed' and instance.completed_at:
        now = timezone.now()
        if last_training_trigger and (now - last_training_trigger).total_seconds() < TRAINING_COOLDOWN_HOURS * 3600:
            logger.info(f"Training cooldown active, skipping retrain trigger")
            return
        
        recent_completions = Token.objects.filter(
            status='completed',
            completed_at__isnull=False,
            completed_at__gte=now - timezone.timedelta(hours=24)
        ).count()
        
        if recent_completions >= 5:
            logger.info(f"Triggering automatic model retraining: {recent_completions} new completions")
            async_task(
                'api.tasks_ml.train_waiting_time_model',
                hook='api.auto_training_triggers.training_completed_hook'
            )
            last_training_trigger = now
        else:
            logger.info(f"Not enough new data for retraining: {recent_completions} completions")

def training_completed_hook(task):
    if task.success:
        logger.info(f"Automatic model retraining completed successfully")
    else:
        logger.error(f"Automatic model retraining failed: {task.result}")

class AutoTrainingManager:
    @staticmethod
    def force_retrain_all_data():
        logger.info("Force retraining with ALL consultation data")
        try:
            success = waiting_time_predictor.train_model()
            if success:
                logger.info("Force retraining completed successfully")
                return True
            else:
                logger.error("Force retraining failed")
                return False
        except Exception as e:
            logger.error(f"Force retraining error: {e}")
            return False
    
    @staticmethod
    def get_training_stats():
        total_consultations = Token.objects.filter(
            status='completed',
            completed_at__isnull=False
        ).count()
        
        recent_consultations = Token.objects.filter(
            status='completed',
            completed_at__isnull=False,
            completed_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        return {
            'total_consultations': total_consultations,
            'recent_consultations_7days': recent_consultations,
            'last_training_trigger': last_training_trigger,
            'ready_for_training': total_consultations >= 10
        }

def conditional_training_task():
    stats = AutoTrainingManager.get_training_stats()
    
    if stats['total_consultations'] < 10:
        logger.info("Not enough total data for training")
        return "Insufficient data"
    
    new_data = Token.objects.filter(
        status='completed',
        completed_at__isnull=False,
        completed_at__gte=timezone.now() - timezone.timedelta(hours=12)
    ).count()
    
    if new_data >= 3:
        logger.info(f"Conditional training triggered: {new_data} new consultations")
        return waiting_time_predictor.train_model()
    else:
        logger.info(f"No training needed: only {new_data} new consultations")
        return "No training needed"