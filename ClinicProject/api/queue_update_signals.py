from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Token
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Token)
def queue_update_signal(sender, instance, created, **kwargs):
    """Send real-time queue updates when token status changes"""
    try:
        channel_layer = get_channel_layer()
        
        # Get affected tokens (same doctor, same date)
        affected_tokens = Token.objects.filter(
            doctor=instance.doctor,
            appointment_date=instance.appointment_date,
            status__in=['confirmed', 'in_progress']
        ).order_by('appointment_time')
        
        # Calculate updated wait times
        from .advanced_wait_predictor import advanced_wait_predictor
        
        updates = []
        for token in affected_tokens:
            new_wait_time = advanced_wait_predictor.get_predicted_wait_time(token.id)
            updates.append({
                'token_id': token.id,
                'token_number': token.token_number,
                'patient_name': token.patient.name,
                'new_wait_time': new_wait_time,
                'status': token.status,
                'position_in_queue': list(affected_tokens).index(token) + 1
            })
        
        # Broadcast to WebSocket
        async_to_sync(channel_layer.group_send)(
            f"queue_updates_{instance.doctor.id}",
            {
                'type': 'queue_update',
                'message': {
                    'event': 'token_updated' if not created else 'token_created',
                    'doctor_id': instance.doctor.id,
                    'updated_token_id': instance.id,
                    'queue_updates': updates,
                    'timestamp': timezone.now().isoformat()
                }
            }
        )
        
        logger.info(f"Queue update broadcast for doctor {instance.doctor.id}")
        
    except Exception as e:
        logger.error(f"Error broadcasting queue update: {e}")

@receiver(post_delete, sender=Token)
def queue_delete_signal(sender, instance, **kwargs):
    """Send updates when token is deleted/cancelled"""
    try:
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f"queue_updates_{instance.doctor.id}",
            {
                'type': 'queue_update',
                'message': {
                    'event': 'token_cancelled',
                    'doctor_id': instance.doctor.id,
                    'cancelled_token_id': instance.id,
                    'timestamp': timezone.now().isoformat()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error broadcasting queue deletion: {e}")