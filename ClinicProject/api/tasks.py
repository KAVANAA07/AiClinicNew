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
    Checks for appointments that are past their time + grace period 
    and still in 'waiting' status, then updates them to 'cancelled'.
    """
    now = timezone.now()
    today = now.date()
    grace_period = timedelta(minutes=15)

    print("\n" + "="*60)
    print(f"[MISSED APPOINTMENTS CHECK] - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    missed_tokens = Token.objects.filter(
        date=today,
        appointment_time__isnull=False,
        status='waiting'
    )

    print(f"Found {missed_tokens.count()} waiting tokens for today")
    
    cancelled_count = 0
    for token in missed_tokens:
        appointment_datetime = datetime.combine(today, token.appointment_time)
        appointment_datetime_aware = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())
        cutoff_time = appointment_datetime_aware + grace_period
        
        print(f"\n[TOKEN {token.id}] Patient: {token.patient.name}")
        print(f"   Appointment: {token.appointment_time.strftime('%I:%M %p')}")
        print(f"   Grace ends: {cutoff_time.strftime('%I:%M %p')}")
        print(f"   Current: {now.strftime('%I:%M %p')}")

        if now > cutoff_time:
            print(f"   STATUS: MISSED - Cancelling appointment")
            
            token.status = 'cancelled'
            token.save()
            cancelled_count += 1
            
            logger.info(f"Cancelled token {token.id} for patient {token.patient.name}")

            # Send SMS notification
            if token.patient.phone_number:
                message = (f"Hi {token.patient.name}, we noticed you missed your appointment slot "
                           f"at {token.appointment_time.strftime('%I:%M %p')} with Dr. {token.doctor.name}. "
                           f"Your appointment has been automatically cancelled. Please feel free to book again or contact the clinic.")
                
                print(f"   SMS: Sending to {token.patient.phone_number}")
                print(f"   MSG: {message[:50]}...")
                
                try:
                    async_task('api.tasks.send_cancelled_notification_sms', token.patient.phone_number, message)
                    print(f"   RESULT: SMS queued successfully")
                except Exception as e:
                    print(f"   ERROR: SMS failed - {e}")
            else:
                print(f"   WARNING: No phone number - SMS skipped")
        else:
            print(f"   STATUS: OK - Still within grace period")

    print(f"\n[SUMMARY] Cancelled {cancelled_count} appointments")
    print("="*60 + "\n")
    
    result_message = f"Checked for missed slots. Cancelled {cancelled_count} tokens automatically."
    logger.info(result_message)
    return result_message

# --- RENAMED & UPDATED: Helper task to send the cancelled notification ---
def send_cancelled_notification_sms(phone_number, message):
    """ Sends the SMS notification that an appointment was cancelled due to no-show. """
    print(f"\n[SMS TASK] NOTIFICATION STARTED")
    print(f"   TO: {phone_number}")
    print(f"   MESSAGE: {message}")
    
    try:
        send_sms_notification(phone_number, message)
        print(f"   SUCCESS: SMS SENT to {phone_number}")
        logger.info(f"Sent auto-cancellation notification to {phone_number}")
    except Exception as e:
        print(f"   FAILED: SMS ERROR - {e}")
        logger.error(f"Failed to send auto-cancellation notification to {phone_number}: {e}")
    
    print(f"   [SMS TASK COMPLETED]\n")

