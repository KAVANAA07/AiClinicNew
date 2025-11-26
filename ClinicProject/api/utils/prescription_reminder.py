from django.utils import timezone
from datetime import datetime, timedelta
from ..models import PrescriptionItem, PrescriptionReminder
from .utils import send_sms_notification
import logging

logger = logging.getLogger(__name__)

def send_prescription_reminders():
    """Send prescription reminders for current time"""
    now = timezone.now()
    current_time = now.time()
    today = now.date()
    
    reminders_sent = 0
    
    # Get active prescriptions (within duration)
    active_prescriptions = PrescriptionItem.objects.filter(
        consultation__date__gte=today - timedelta(days=30)  # Last 30 days
    )
    
    for prescription in active_prescriptions:
        # Check if prescription is still active
        consultation_date = prescription.consultation.date
        if hasattr(consultation_date, 'date'):
            prescription_start = consultation_date.date()
        else:
            prescription_start = consultation_date
        prescription_end = prescription_start + timedelta(days=prescription.duration_days)
        
        if today > prescription_end:
            continue  # Prescription expired
        
        # Get reminder times for this prescription
        reminder_times = get_prescription_reminder_times(prescription)
        
        for reminder_time, dose_info in reminder_times:
            # Check if current time matches reminder time (within 5 minutes)
            time_diff = abs((current_time.hour * 60 + current_time.minute) - 
                          (reminder_time.hour * 60 + reminder_time.minute))
            
            if time_diff <= 5:  # Within 5 minutes
                # Check if reminder already sent today
                reminder_exists = PrescriptionReminder.objects.filter(
                    prescription=prescription,
                    reminder_time=reminder_time,
                    sent_date=today
                ).exists()
                
                if not reminder_exists:
                    # Send reminder
                    success = send_prescription_reminder_sms(prescription, dose_info)
                    
                    if success:
                        # Record reminder
                        PrescriptionReminder.objects.create(
                            prescription=prescription,
                            reminder_time=reminder_time,
                            sent_date=today,
                            dose_info=dose_info
                        )
                        reminders_sent += 1
    
    return f"Sent {reminders_sent} prescription reminders"

def get_prescription_reminder_times(prescription):
    """Get all reminder times for a prescription"""
    reminder_times = []
    
    if prescription.timing_type == 'frequency':
        # Frequency-based timing
        for i in range(1, prescription.frequency_per_day + 1):
            time_field = getattr(prescription, f'timing_{i}_time', None)
            food_field = getattr(prescription, f'timing_{i}_food', None)
            
            if time_field:
                dose_info = {
                    'dose_number': i,
                    'food_timing': food_field or '',
                    'timing_type': 'frequency'
                }
                reminder_times.append((time_field, dose_info))
    
    else:
        # M/A/N or custom timing
        if prescription.timing_morning and prescription.morning_time:
            dose_info = {
                'dose_number': 1,
                'period': 'morning',
                'food_timing': prescription.morning_food or '',
                'timing_type': 'period'
            }
            reminder_times.append((prescription.morning_time, dose_info))
        
        if prescription.timing_afternoon and prescription.afternoon_time:
            dose_info = {
                'dose_number': 2,
                'period': 'afternoon',
                'food_timing': prescription.afternoon_food or '',
                'timing_type': 'period'
            }
            reminder_times.append((prescription.afternoon_time, dose_info))
        
        if prescription.timing_evening and prescription.evening_time:
            dose_info = {
                'dose_number': 3,
                'period': 'evening',
                'food_timing': prescription.evening_food or '',
                'timing_type': 'period'
            }
            reminder_times.append((prescription.evening_time, dose_info))
        
        if prescription.timing_night and prescription.night_time:
            dose_info = {
                'dose_number': 4,
                'period': 'night',
                'food_timing': prescription.night_food or '',
                'timing_type': 'period'
            }
            reminder_times.append((prescription.night_time, dose_info))
    
    return reminder_times

def send_prescription_reminder_sms(prescription, dose_info):
    """Send SMS reminder for a specific prescription dose"""
    try:
        patient = prescription.consultation.patient
        
        if not patient.phone_number:
            return False
        
        # Create reminder message
        medicine_info = f"{prescription.medicine_name} {prescription.dosage}"
        
        if dose_info['timing_type'] == 'frequency':
            dose_text = f"dose {dose_info['dose_number']}"
        else:
            dose_text = f"{dose_info['period']} dose"
        
        food_text = ""
        if dose_info['food_timing']:
            food_text = f" {dose_info['food_timing']} food"
        
        message = f"Prescription Reminder: Time to take your {medicine_info} - {dose_text}{food_text}. Prescribed by Dr. {prescription.consultation.doctor.name}"
        
        # Send SMS
        success = send_sms_notification(patient.phone_number, message)
        
        if success:
            logger.info(f"Prescription reminder sent to {patient.name} for {medicine_info}")
        else:
            logger.error(f"Failed to send prescription reminder to {patient.name}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending prescription reminder: {e}")
        return False