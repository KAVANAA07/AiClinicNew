from django.utils import timezone
from datetime import timedelta, datetime
from .models import Token, Patient # Make sure Token and Patient are imported
from .utils.utils import send_sms_notification
# --- NEW: Import async_task ---
from django_q.tasks import async_task # pyright: ignore[reportMissingImports]
import logging

logger = logging.getLogger(__name__)

# --- Function for Daily Morning Reminders ---
def send_daily_appointment_reminders():
    """
    Sends SMS reminders for all appointments scheduled for today.
    """
    today = timezone.now().date()
    todays_tokens = Token.objects.filter(
        date=today,
        status__in=['waiting', 'confirmed']
    ).select_related('patient', 'doctor', 'clinic')

    count = todays_tokens.count()
    logger.info(f"Found {count} active appointments for {today}. Sending reminders...")
    print(f"Found {count} active appointments for {today}. Sending reminders...")

    if count == 0:
        return f"No appointments found for {today}."

    success_count = 0
    failure_count = 0

    for token in todays_tokens:
        patient = token.patient
        doctor = token.doctor
        clinic = token.clinic
        
        if patient.phone_number:
            time_str = token.appointment_time.strftime('%I:%M %p') if token.appointment_time else "your scheduled time"
            message = (
                f"Hi {patient.name}, this is a reminder for your appointment at {clinic.name} "
                f"with Dr. {doctor.name} today around {time_str}. "
            )
            if token.token_number:
                 message += f"Your token is {token.token_number}. "
            
            message += "Please arrive on time."

            try:
                send_sms_notification(patient.phone_number, message)
                logger.info(f"  -> Sent reminder to {patient.name} for Dr. {doctor.name}")
                print(f"  -> Sent reminder to {patient.name} for Dr. {doctor.name}")
                success_count += 1
            except Exception as e:
                logger.error(f"  -> FAILED to send reminder to {patient.name} ({patient.phone_number}): {e}")
                print(f"  -> FAILED to send reminder to {patient.name} ({patient.phone_number}): {e}")
                failure_count += 1
        else:
            logger.warning(f"  -> SKIPPED reminder for {patient.name} - No phone number.")
            print(f"  -> SKIPPED reminder for {patient.name} - No phone number.")
            failure_count += 1

    result_message = f"Finished sending reminders for {today}. Success: {success_count}, Failed/Skipped: {failure_count}."
    logger.info(result_message)
    print(result_message)
    return result_message

# --- Function for Prescription Reminders ---
def send_prescription_reminder_sms(phone_number, message, **kwargs):
    """
    Sends a single prescription dosage reminder SMS.
    Accepts **kwargs to ignore extra arguments like 'schedule'.
    """
    try:
        send_sms_notification(phone_number, message)
        logger.info(f"Sent prescription reminder to {phone_number}")
        print(f"Sent prescription reminder to {phone_number}")
    except Exception as e:
        logger.error(f"Failed to send prescription reminder to {phone_number}: {e}")
        print(f"Failed to send prescription reminder to {phone_number}: {e}")

# --- MODIFIED: Function to automatically CANCEL missed appointments ---
def check_and_cancel_missed_slots():
    """
    Checks all waiting tokens and cancels any that crossed time limit.
    """
    now = timezone.now()
    grace_period = timedelta(minutes=15)

    # Get ALL waiting tokens with appointment times
    all_waiting_tokens = Token.objects.filter(
        appointment_time__isnull=False,
        status='waiting'
    )
    
    total_count = all_waiting_tokens.count()
    expired_count = 0
    cancelled_count = 0
    
    print(f"\n[{now.strftime('%H:%M:%S')}] Checking appointments - Total waiting tokens: {total_count}")
    
    for token in all_waiting_tokens:
        appointment_datetime = datetime.combine(token.date, token.appointment_time)
        appointment_datetime_aware = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())
        cutoff_time = appointment_datetime_aware + grace_period
        
        # Check if crossed time limit
        if now > cutoff_time:
            expired_count += 1
            token.status = 'cancelled'
            token.save()
            cancelled_count += 1
            
            print(f"  CANCELLED: {token.patient.name} - {token.date} {token.appointment_time.strftime('%I:%M %p')}")
            
            # Send SMS for today's appointments only
            if token.date == now.date() and token.patient.phone_number:
                message = f"Hi {token.patient.name}, your appointment at {token.appointment_time.strftime('%I:%M %p')} with Dr. {token.doctor.name} has been cancelled due to no-show."
                try:
                    async_task('api.tasks.send_cancelled_notification_sms', token.patient.phone_number, message)
                    print(f"  SMS SENT: {token.patient.phone_number}")
                except Exception as e:
                    print(f"  SMS FAILED: {e}")

    print(f"  Expired tokens: {expired_count}, Cancelled: {cancelled_count}")
    
    result_message = f"Total: {total_count}, Expired: {expired_count}, Cancelled: {cancelled_count}"
    logger.info(result_message)
    return result_message

# --- RENAMED & UPDATED: Helper task to send the cancelled notification ---
def send_cancelled_notification_sms(phone_number, message):
    """ Sends the SMS notification that an appointment was cancelled due to no-show. """
    print(f"\n[SMS] Sending cancellation notice to {phone_number}")
    
    try:
        send_sms_notification(phone_number, message)
        print(f"[SMS] SUCCESS - Message sent to {phone_number}")
        logger.info(f"Sent auto-cancellation notification to {phone_number}")
    except Exception as e:
        print(f"[SMS] FAILED - {e}")
        logger.error(f"Failed to send auto-cancellation notification to {phone_number}: {e}")
    


