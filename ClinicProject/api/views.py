# Note: transformers.pipeline is imported lazily inside the view to avoid heavy imports at module import time
from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token as AuthToken
from rest_framework.views import APIView
# --- MODIFIED: Added IntegrityError ---
from .models import Token, Doctor, Patient, Consultation, Receptionist, Clinic, State, District, PrescriptionItem, DoctorSchedule
from .serializers import (
    TokenSerializer,
    DoctorSerializer,
    ConsultationSerializer,
    PatientRegisterSerializer,
    ClinicWithDoctorsSerializer,
    PatientSerializer,
    AnonymizedTokenSerializer,
    DoctorScheduleSerializer
)
from django.db.models import Count, Avg, F, Q, Case, When, Value
from django.utils import timezone
from math import radians, sin, cos, sqrt, atan2
from django.contrib.auth import authenticate, get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from twilio.twiml.voice_response import VoiceResponse
from django.http import HttpResponse
# --- MODIFIED: Added IntegrityError ---
from django.db import transaction, IntegrityError
import random

# --- Core App Imports ---
from .utils.utils import send_sms_notification
# --- Imports for Django-Q Scheduling ---
from django_q.tasks import async_task
from datetime import datetime, timedelta, time
# --- FIX: Import get_random_string ---
from django.utils.crypto import get_random_string
import threading
import logging
import re

# Set up loggers
logger = logging.getLogger('api.views')
ivr_logger = logging.getLogger('api.ivr')

User = get_user_model()

# --- Helper Functions ---
def normalize_phone_number(phone):
    """Normalize phone number by removing country codes, spaces, and special chars"""
    if not phone:
        return phone
    # Remove all non-digits
    digits_only = re.sub(r'\D', '', str(phone))
    if not digits_only:
        return phone
    
    # Remove country codes (91 for India, 1 for US, etc.)
    if digits_only.startswith('91') and len(digits_only) == 12:
        return digits_only[2:]
    elif digits_only.startswith('1') and len(digits_only) == 11:
        return digits_only[1:]
    
    # Return last 10 digits if more than 10
    if len(digits_only) > 10:
        return digits_only[-10:]
    return digits_only
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 # Radius of Earth in kilometers
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])
    dlon, dlat = lon2_rad - lon1_rad, lat2_rad - lat1_rad
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    return R * (2 * atan2(sqrt(a), sqrt(1 - a)))

def _get_available_slots_for_doctor(doctor_id, date_str):
    """Returns list of available HH:MM strings for a single date."""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        doctor = Doctor.objects.get(id=doctor_id)
    except (ValueError, Doctor.DoesNotExist):
        return None
    
    # Get doctor's schedule or use defaults
    try:
        schedule = DoctorSchedule.objects.get(doctor=doctor)
        start_time = schedule.start_time
        end_time = schedule.end_time
        slot_duration_minutes = schedule.slot_duration_minutes
        max_slots = schedule.max_slots_per_day
    except DoctorSchedule.DoesNotExist:
        # Default schedule if none exists
        start_time = time(9, 0)
        end_time = time(17, 0)
        slot_duration_minutes = 15
        max_slots = None
    
    slot_duration = timedelta(minutes=slot_duration_minutes)
    all_slots = []
    current_time = datetime.combine(target_date, start_time)
    end_datetime = datetime.combine(target_date, end_time)
    
    while current_time < end_datetime:
        all_slots.append(current_time.time())
        current_time += slot_duration
        
        # Limit slots if max_slots is set
        if max_slots and len(all_slots) >= max_slots:
            break
    
    booked_tokens = Token.objects.filter(
        doctor_id=doctor_id, date=target_date, appointment_time__isnull=False
    ).exclude(status__in=['cancelled', 'skipped'])
    booked_slots = {token.appointment_time for token in booked_tokens}
    available_slots = [slot for slot in all_slots if slot not in booked_slots]
    return [slot.strftime('%H:%M') for slot in available_slots]

# --- Function to find the next earliest available slot across dates ---
def _find_next_available_slot_for_doctor(doctor_id):
    """Finds the next truly available slot (not expired)."""
    try:
        doctor = Doctor.objects.get(id=doctor_id)
    except Doctor.DoesNotExist:
        return None, None

    now = timezone.now()
    today = now.date()
    current_time = now.time()
    
    # Check up to 30 days in the future
    for i in range(30):
        check_date = today + timedelta(days=i)
        date_str = check_date.strftime('%Y-%m-%d')
        available_slots = _get_available_slots_for_doctor(doctor_id, date_str)

        if available_slots:
            # If today, only return slots that are in the future
            if check_date == today:
                future_slots = [
                    slot for slot in available_slots
                    if datetime.strptime(slot, '%H:%M').time() > current_time
                ]
                if future_slots:
                    return check_date, future_slots[0]
            else:
                # Future date - return first available slot
                return check_date, available_slots[0]

    return None, None

# ====================================================================
# --- START IVR USER CREATION ENHANCEMENT ---
# (Helper to create token - Now also creates User and sends password)
# ====================================================================
def _create_ivr_token(doctor, appointment_date, appointment_time_str, caller_phone_number):
    """
    Creates a token for the given details. Returns the token object or None if failed.
    Handles finding/creating patient, checking for existing tokens, AND
    creating a User account if one doesn't exist.
    """
    ivr_logger.info(f"IVR: Creating token for {caller_phone_number} with Dr. {doctor.name} on {appointment_date} at {appointment_time_str}")
    
    patient_name = f"IVR Patient {caller_phone_number[-4:]}"
    patient_query = Patient.objects.filter(phone_number=caller_phone_number)
    patient = patient_query.first()
    
    # Find or create the patient
    if not patient:
        patient, _ = Patient.objects.get_or_create(phone_number=caller_phone_number, defaults={'name': patient_name, 'age': 0})
        ivr_logger.info(f"IVR: Created new patient {patient.id} for {caller_phone_number}")
    else:
        ivr_logger.info(f"IVR: Found existing patient {patient.id} for {caller_phone_number}")

    # --- ENHANCED: Check for User account and create/link appropriately ---
    if patient.user is None:
        try:
            # Normalize phone numbers for comparison
            normalized_caller = normalize_phone_number(caller_phone_number)
            
            # Check if ANY user has a patient with this phone number (sync by phone, not username)
            existing_patient_with_user = None
            for patient in Patient.objects.filter(user__isnull=False):
                if normalize_phone_number(patient.phone_number) == normalized_caller:
                    existing_patient_with_user = patient
                    break
            if existing_patient_with_user:
                # Found existing patient with user - merge this IVR patient with the web patient
                web_patient = existing_patient_with_user
                web_user = web_patient.user
                
                # Update web patient with any missing info and link this booking
                patient.user = web_user
                patient.save()
                ivr_logger.info(f"IVR: Linked patient {patient.id} to existing web user {web_user.id} by phone number")
                
                # Send sync notification
                sync_message = f"Your IVR booking has been synced with your web account. You can now view this appointment online."
                try:
                    send_sms_notification(caller_phone_number, sync_message)
                    ivr_logger.info(f"IVR: Sync SMS sent to {caller_phone_number}")
                except Exception as e:
                    ivr_logger.error(f"IVR: Failed to send SYNC SMS to {caller_phone_number}: {e}")
            else:
                # Check if a user with this phone number as username exists
                existing_user = User.objects.filter(username=caller_phone_number).first()
                if existing_user:
                    # User exists from web - link to this patient
                    patient.user = existing_user
                    patient.save()
                    ivr_logger.info(f"IVR: Linked existing web user to patient {patient.id}")
                    
                    # Send sync notification
                    sync_message = f"Your IVR booking has been synced with your web account. You can now view this appointment online."
                    try:
                        send_sms_notification(caller_phone_number, sync_message)
                        ivr_logger.info(f"IVR: Sync SMS sent to {caller_phone_number}")
                    except Exception as e:
                        ivr_logger.error(f"IVR: Failed to send SYNC SMS to {caller_phone_number}: {e}")
                else:
                    # No web user exists - create new account for IVR user
                    temp_password = get_random_string(length=8)
                    new_user = User.objects.create_user(
                        username=caller_phone_number, 
                        password=temp_password,
                        is_staff=False,
                        is_superuser=False
                    )
                    patient.user = new_user
                    patient.save()
                    ivr_logger.info(f"IVR: Created new user account for patient {patient.id}")
                    
                    # Send welcome SMS with credentials
                    welcome_message = f"Welcome to MedQ! A web account has been created for you.\nUsername: {caller_phone_number}\nPassword: {temp_password}\nYou can now view your appointments online!"
                    try:
                        send_sms_notification(caller_phone_number, welcome_message)
                        ivr_logger.info(f"IVR: Welcome SMS sent to {caller_phone_number}")
                    except Exception as e:
                        ivr_logger.error(f"IVR: Failed to send WELCOME SMS to {caller_phone_number}: {e}")
        
        except Exception as e:
            ivr_logger.error(f"IVR: Failed to create/link user for patient {patient.id}: {e}")
            # Continue with booking, but user won't be able to log in
    else:
        # Patient already has a user account - this is a returning user
        ivr_logger.info(f"IVR: Patient {patient.id} already has linked user account {patient.user.id}")
    # --- END ENHANCED USER CREATION ---


    # Check for existing active token on ANY day
    existing_active_tokens = Token.objects.filter(patient=patient).exclude(status__in=['completed', 'cancelled', 'skipped'])
    if existing_active_tokens.exists():
        existing_token = existing_active_tokens.first()
        ivr_logger.warning(f"IVR Booking failed: Patient {patient.id} already has active token {existing_token.id} on {existing_token.date} at {existing_token.appointment_time} (status: {existing_token.status})")
        return None # Indicate failure: existing token

    try:
        appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()

        # Calculate token number based on slot
        start_time = time(9, 0)
        slot_duration_minutes = 15
        appointment_datetime = datetime.combine(appointment_date, appointment_time)
        start_datetime = datetime.combine(appointment_date, start_time)
        delta_minutes = (appointment_datetime - start_datetime).total_seconds() / 60
        slot_number = int(delta_minutes // slot_duration_minutes) + 1
        doctor_initial = doctor.name[0].upper() if doctor.name else "X"
        formatted_token_number = f"{doctor_initial}-{slot_number}"

        with transaction.atomic():
            # Final check if slot is still free right before creating (race condition protection)
            existing_token = Token.objects.filter(
                doctor=doctor, 
                date=appointment_date, 
                appointment_time=appointment_time
            ).exclude(status__in=['cancelled', 'skipped']).first()
            
            if existing_token:
                ivr_logger.warning(f"IVR Booking failed: Slot {appointment_date} {appointment_time_str} for Dr. {doctor.id} already taken by token {existing_token.id}")
                return None # Indicate failure: slot taken

            new_appointment = Token.objects.create(
                patient=patient, doctor=doctor, clinic=doctor.clinic, date=appointment_date,
                appointment_time=appointment_time, token_number=formatted_token_number, status='waiting'
            )
            ivr_logger.info(f"IVR: Successfully created token {new_appointment.id} for patient {patient.id}")
            return new_appointment # Indicate success

    except IntegrityError as e:
        ivr_logger.error(f"IVR Booking failed: Database integrity error for slot {appointment_date} {appointment_time_str} Dr. {doctor.id}: {e}")
        return None # Indicate failure: database conflict
    except Exception as e:
        ivr_logger.error(f"IVR Booking failed: Unexpected error during token creation - {e}")
        return None # Indicate general failure

# ====================================================================
# --- END IVR ENHANCEMENT ---
# ====================================================================


# --- Standard API Views ---

class AvailableSlotsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, doctor_id, date):
        formatted_slots = _get_available_slots_for_doctor(doctor_id, date)
        if formatted_slots is None:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(formatted_slots, status=status.HTTP_200_OK)

class PublicClinicListView(generics.ListAPIView):
    queryset = Clinic.objects.prefetch_related('doctors').all()
    serializer_class = ClinicWithDoctorsSerializer
    permission_classes = [permissions.AllowAny]

class ClinicAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        clinic = None
        if hasattr(user, 'doctor'): 
            clinic = user.doctor.clinic
        elif hasattr(user, 'receptionist'): 
            clinic = user.receptionist.clinic
        
        if not clinic: 
            return Response({'error': 'User is not associated with a clinic.'}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.now().date()
        todays_tokens = Token.objects.filter(clinic=clinic, date=today)
        completed_tokens = todays_tokens.filter(status='completed', completed_at__isnull=False)
        avg_wait_data = completed_tokens.aggregate(avg_duration=Avg(F('completed_at') - F('created_at')))
        avg_wait_minutes = round(avg_wait_data['avg_duration'].total_seconds() / 60, 1) if avg_wait_data['avg_duration'] else 0

        stats = {
            'clinic_name': clinic.name, 'date': today.strftime("%B %d, %Y"),
            'total_patients': todays_tokens.count(),
            'average_wait_time_minutes': avg_wait_minutes,
            'doctor_workload': list(todays_tokens.values('doctor__name').annotate(count=Count('id')).order_by('-count')),
            'patient_status_breakdown': {
                'waiting': todays_tokens.filter(status='waiting').count(),
                'confirmed': todays_tokens.filter(status='confirmed').count(),
                'completed': completed_tokens.count()
            }
        }
        return Response(stats, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class PatientRegisterView(generics.CreateAPIView):
    serializer_class = PatientRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        
        # Check if patient already exists from IVR booking (sync by phone number)
        if phone_number:
            # Normalize phone number for comparison
            normalized_phone = normalize_phone_number(phone_number)
            
            # Check for any patient with this phone number (with or without user)
            existing_patients = []
            for patient in Patient.objects.all():
                if normalize_phone_number(patient.phone_number) == normalized_phone:
                    existing_patients.append(patient)
            if existing_patients:
                # Check if any of these patients already have a user account
                patient_with_user = next((p for p in existing_patients if p.user is not None), None)
                if patient_with_user:
                    return Response({
                        'error': 'phone_already_registered',
                        'message': 'This phone number is already registered. Please use a different phone number or log in with existing credentials.'
                    }, status=status.HTTP_409_CONFLICT)
                
                # Found IVR-only patients - offer to link
                ivr_patient = next((p for p in existing_patients if p.user is None), None)
                if ivr_patient:
                    return Response({
                        'error': 'ivr_account_exists',
                        'message': 'We found that you have booked appointments via phone. Would you like to link your existing bookings to this web account?',
                        'phone_number': phone_number
                    }, status=status.HTTP_409_CONFLICT)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            patient = user.patient
            token, _ = AuthToken.objects.get_or_create(user=user)
            if patient.phone_number:
                message = f"Welcome to MedQ, {patient.name}! Your registration was successful."
                try:
                    send_sms_notification(patient.phone_number, message)
                except Exception as e:
                    print(f"Failed to send welcome SMS: {e}")

            # Build a normalized user payload so frontend always receives the same shape
            profile = {
                'id': user.id,
                'username': user.username,
                'name': patient.name,
                'age': patient.age,
                'phone_number': patient.phone_number,
                'role': 'patient'
            }
            user_data = {'token': token.key, 'user': profile}
            return Response(user_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LinkIVRAccountView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        name = request.data.get('name')
        age = request.data.get('age')
        password = request.data.get('password')
        
        if not all([phone_number, name, age, password]):
            return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find all IVR patients with this phone number
            existing_patients = Patient.objects.filter(phone_number=phone_number, user__isnull=True)
            if not existing_patients.exists():
                raise Patient.DoesNotExist
            
            # Create new user account
            user = User.objects.create_user(
                username=phone_number,
                password=password,
                is_staff=False,
                is_superuser=False
            )
            
            # Link all existing patients to new user and update the primary one
            primary_patient = existing_patients.first()
            primary_patient.user = user
            primary_patient.name = name  # Update name from web registration
            primary_patient.age = int(age)  # Update age from web registration
            primary_patient.save()
            
            # Link any additional patients with same phone number
            for patient in existing_patients.exclude(id=primary_patient.id):
                patient.user = user
                patient.save()
            
            # Create auth token
            token, _ = AuthToken.objects.get_or_create(user=user)
            
            # Send confirmation SMS
            message = f"Great! Your web account has been linked to your existing appointments. You can now view all your bookings online."
            try:
                send_sms_notification(phone_number, message)
            except Exception as e:
                print(f"Failed to send linking SMS: {e}")
            
            # Return user data
            profile = {
                'id': user.id,
                'username': user.username,
                'name': existing_patient.name,
                'age': existing_patient.age,
                'phone_number': existing_patient.phone_number,
                'role': 'patient'
            }
            user_data = {'token': token.key, 'user': profile}
            return Response(user_data, status=status.HTTP_201_CREATED)
            
        except Patient.DoesNotExist:
            return Response({'error': 'No IVR bookings found for this phone number.'}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'error': 'An account with this phone number already exists.'}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            return Response({'error': f'Failed to link account: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ConfirmArrivalView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user = request.user
        user_lat, user_lon = request.data.get('latitude'), request.data.get('longitude')
        if not all([user_lat, user_lon]): 
            return Response({'error': 'Location data is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not hasattr(user, 'patient'): 
            return Response({'error': 'No patient profile found.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find tokens by normalized phone number
            user_phone_normalized = normalize_phone_number(user.patient.phone_number)
            matching_patients = []
            for patient in Patient.objects.all():
                if normalize_phone_number(patient.phone_number) == user_phone_normalized:
                    matching_patients.append(patient.id)
            
            token = Token.objects.filter(
                patient_id__in=matching_patients, 
                date=timezone.now().date(), 
                status='waiting'
            ).first()
            
            if not token:
                raise Token.DoesNotExist

            if token.appointment_time:
                now = timezone.now()
                appointment_datetime = timezone.make_aware(datetime.combine(token.date, token.appointment_time))
                start_window = appointment_datetime - timedelta(minutes=20)
                end_window = appointment_datetime + timedelta(minutes=15)
                if not (start_window <= now <= end_window):
                    start_window_str = start_window.strftime('%I:%M %p')
                    return Response({
                        'error': f"You can only confirm arrival between {start_window_str} and {end_window.strftime('%I:%M %p')}."
                    }, status=status.HTTP_400_BAD_REQUEST)

            clinic = token.clinic
            if not all([clinic.latitude, clinic.longitude]): 
                return Response({'error': 'Clinic location has not been configured by the admin.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            distance = haversine_distance(float(user_lat), float(user_lon), clinic.latitude, clinic.longitude)
            token.distance_km = round(distance, 2)
            
            if distance > 1.0: # 1km radius check
                token.save()
                return Response({'error': f'You are approximately {distance:.1f} km away. You must be within 1 km to confirm your arrival.'}, status=status.HTTP_400_BAD_REQUEST)

            token.status = 'confirmed'
            token.save()
            return Response({"message": "Arrival confirmed successfully!", "token": TokenSerializer(token).data}, status=status.HTTP_200_OK)
        except Token.DoesNotExist: 
            return Response({'error': 'No active appointment found for today to confirm.'}, status=status.HTTP_404_NOT_FOUND)
        except Token.MultipleObjectsReturned: 
            return Response({'error': 'Multiple active appointments found. Please contact reception.'}, status=status.HTTP_400_BAD_REQUEST)

# --- CORRECTED PatientCancelTokenView ---
class PatientCancelTokenView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user = request.user
        if not hasattr(user, 'patient'): 
            return Response({'error': 'No patient profile found.'}, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.now().date()
        try:
            # Find tokens by normalized phone number
            user_phone_normalized = normalize_phone_number(user.patient.phone_number)
            matching_patients = []
            for patient in Patient.objects.all():
                if normalize_phone_number(patient.phone_number) == user_phone_normalized:
                    matching_patients.append(patient.id)
            
            token = Token.objects.filter(
                patient_id__in=matching_patients,
                date__gte=today,
                status__in=['waiting', 'confirmed']
            ).order_by('date', 'appointment_time').first()

            if not token:
                raise Token.DoesNotExist

            token.status = 'cancelled'
            token.save(update_fields=['status'])
            return Response({'message': 'Your token has been successfully cancelled.'}, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({'error': 'You do not have an active token to cancel.'}, status=status.HTTP_404_NOT_FOUND)

# --- CORRECTED GetPatientTokenView ---
class GetPatientTokenView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        if not hasattr(user, 'patient'): 
            return Response({'error': 'No patient profile found.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            today = timezone.now().date()
            user_phone_normalized = normalize_phone_number(user.patient.phone_number)

            # Find tokens by normalized phone number (not just patient ID)
            matching_patients = []
            for patient in Patient.objects.all():
                if normalize_phone_number(patient.phone_number) == user_phone_normalized:
                    matching_patients.append(patient.id)

            # Get today's token first, then future tokens
            token = Token.objects.filter(
                patient_id__in=matching_patients,
                date=today
            ).exclude(status__in=['completed', 'cancelled']).order_by('appointment_time', 'created_at').first()

            if not token:
                # Get next upcoming token (including future dates)
                token = Token.objects.filter(
                    patient_id__in=matching_patients,
                    date__gte=today,
                    status__in=['waiting', 'confirmed']
                ).order_by('date', 'appointment_time', 'created_at').first()

            if token:
                token_data = TokenSerializer(token).data
                token_data['doctor_id'] = token.doctor_id
                token_data['clinic_id'] = token.clinic_id
                if token.doctor: token_data['doctor'] = {'name': token.doctor.name}
                if token.clinic: token_data['clinic'] = {'name': token.clinic.name}
                token_data['date'] = token.date.strftime('%Y-%m-%d')
                return Response(token_data)
            else:
                return Response({'error': 'No active or upcoming appointments found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error in GetPatientTokenView: {e}")
            return Response({'error': 'An error occurred while fetching your token.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClinicWithDoctorsListView(generics.ListAPIView):
    queryset = Clinic.objects.prefetch_related('doctors').all()
    serializer_class = ClinicWithDoctorsSerializer
    permission_classes = [permissions.AllowAny]

# --- ENHANCED PatientCreateTokenView ---
class PatientCreateTokenView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user = request.user
        doctor_id, appointment_date_str, appointment_time_str = request.data.get('doctor_id'), request.data.get('date'), request.data.get('time')
        
        if not all([doctor_id, appointment_date_str, appointment_time_str]): 
            return Response({'error': 'Doctor, date, and time slot are required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not hasattr(user, 'patient'): 
            return Response({'error': 'Only patients can create appointments.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
            if appointment_date < timezone.now().date():
                return Response({'error': 'Cannot book appointments for past dates.'}, status=status.HTTP_400_BAD_REQUEST)
            doctor = Doctor.objects.get(id=doctor_id)
        except (ValueError, Doctor.DoesNotExist): 
            return Response({'error': 'Invalid data provided.'}, status=status.HTTP_400_BAD_REQUEST)

        if Token.objects.filter(patient=user.patient).exclude(status__in=['completed', 'cancelled', 'skipped']).exists():
            return Response({'error': 'You already have an active appointment. Cannot book another one now.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                is_slot_booked = Token.objects.filter(
                    doctor=doctor, date=appointment_date, appointment_time=appointment_time
                ).exclude(status__in=['cancelled', 'skipped']).exists()
                if is_slot_booked:
                    return Response({'error': 'This slot was just booked. Please select another time.'}, status=status.HTTP_409_CONFLICT)
                new_appointment = Token.objects.create(patient=user.patient, doctor=doctor, clinic=doctor.clinic, date=appointment_date, appointment_time=appointment_time, status='waiting')
        except IntegrityError:
            return Response({'error': 'Database conflict trying to book slot. Please try again.'}, status=status.HTTP_409_CONFLICT)

        if user.patient.phone_number:
            message = (f"Hi {user.patient.name}, your appointment with Dr. {doctor.name} is confirmed for " f"{appointment_date.strftime('%d-%m-%Y')} at {appointment_time.strftime('%I:%M %p')}.")
            try: send_sms_notification(user.patient.phone_number, message)
            except Exception as e: print(f"Failed to send confirmation SMS for new token {new_appointment.id}: {e}")
        return Response(TokenSerializer(new_appointment).data, status=status.HTTP_201_CREATED)

# ====================================================================
# --- START OF ENHANCEMENT: Date Filtering for Staff/Doctor Queues ---
# ====================================================================
class TokenListCreate(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TokenSerializer
    


    def get_queryset(self):
        user = self.request.user
        # --- DATE FILTERING LOGIC ---
        date_param = self.request.query_params.get('date', None)
        target_date = timezone.now().date() # Default to today
        if date_param:
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                pass # Ignore invalid date param, use default (today)
        # --- END DATE FILTERING LOGIC ---

        status_priority = Case(
            When(status='in_consultancy', then=Value(1)),
            When(status='confirmed', then=Value(2)),
            When(status='waiting', then=Value(3)),
            default=Value(4)
        )

        # --- Filter by target_date instead of today ---
        base_queryset = Token.objects.filter(
            date=target_date
        ).exclude(status__in=['completed', 'cancelled'])

        clinic = None # Determine clinic based on user role
        if hasattr(user, 'doctor'):
            clinic = user.doctor.clinic
            queryset = base_queryset.filter(doctor=user.doctor) # Doctor sees only their queue
        elif hasattr(user, 'receptionist'):
            clinic = user.receptionist.clinic
            queryset = base_queryset.filter(clinic=clinic) # Receptionist sees whole clinic queue
        else:
            return Token.objects.none()

        return queryset.order_by(
            status_priority,
            F('appointment_time').asc(nulls_last=True),
            'created_at'
        )
# ====================================================================
# --- END OF DATE FILTERING ENHANCEMENT ---
# ====================================================================

    # --- ENHANCED POST METHOD (Strict Slot Check) ---
    def post(self, request, *args, **kwargs):
        patient_name = request.data.get('patient_name')
        patient_age = request.data.get('patient_age')
        phone_number = request.data.get('phone_number')
        doctor_id = request.data.get('assigned_doctor')
        appointment_time_str = request.data.get('appointment_time') # e.g., "09:15"

        if not all([patient_name, patient_age, phone_number, doctor_id]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if not hasattr(request.user, 'receptionist'):
                 return Response({'error': 'Only receptionists can create tokens.'}, status=status.HTTP_403_FORBIDDEN)

            receptionist = request.user.receptionist
            doctor = Doctor.objects.get(id=doctor_id, clinic=receptionist.clinic)

            patient, created = Patient.objects.update_or_create(
                phone_number=phone_number,
                defaults={'name': patient_name, 'age': patient_age}
            )

            appointment_time = None
            today = timezone.now().date() # Receptionist only books for today
            today_str = today.strftime('%Y-%m-%d')

            # Check if this patient already has an active token for ANY date (prevent double booking for patient)
            if Token.objects.filter(patient=patient).exclude(status__in=['completed', 'cancelled', 'skipped']).exists():
                return Response({'error': f'Patient {patient.name} already has an active appointment.'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate and check slot availability if time is provided
            if appointment_time_str:
                try:
                    appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
                except ValueError:
                    return Response({'error': 'Invalid time format. Use HH:MM.'}, status=status.HTTP_400_BAD_REQUEST)

                # --- Strict check inside transaction ---
                try:
                    with transaction.atomic():
                        is_slot_booked = Token.objects.filter(
                            doctor=doctor, date=today, appointment_time=appointment_time
                        ).exclude(status__in=['cancelled', 'skipped']).exists()
                        if is_slot_booked:
                            return Response({'error': 'This slot was just booked. Please refresh and select another.'}, status=status.HTTP_409_CONFLICT)
                        token_status = 'waiting'
                        new_token = Token.objects.create(
                            patient=patient, doctor=doctor, clinic=doctor.clinic, date=today,
                            appointment_time=appointment_time, status=token_status
                        )
                except IntegrityError:
                    return Response({'error': 'Database conflict trying to book slot. Please try again.'}, status=status.HTTP_409_CONFLICT)
                # --- End strict check ---
            else:
                # Walk-in
                token_status = 'confirmed'
                new_token = Token.objects.create(
                    patient=patient, doctor=doctor, clinic=doctor.clinic, date=today,
                    appointment_time=None, status=token_status
                )

            # Send SMS Notification
            message = f"Dear {patient.name}, your token for Dr. {doctor.name} at {doctor.clinic.name} has been confirmed for today."
            if new_token.appointment_time: message += f" Your appointment is at {new_token.appointment_time.strftime('%I:%M %p')}."
            new_token.refresh_from_db()
            if new_token.token_number: message += f" Your token number is {new_token.token_number}."
            try: send_sms_notification(patient.phone_number, message)
            except Exception as e: print(f"Receptionist: Failed to send confirmation SMS to {patient.phone_number}: {e}")

            return Response(TokenSerializer(new_token).data, status=status.HTTP_201_CREATED)

        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found in your clinic'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error creating token (receptionist): {e}")
            return Response({'error': f'An unexpected error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- CORRECTED DoctorList ---
class DoctorList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DoctorSerializer

    def get_queryset(self):
        user = self.request.user
        clinic = None
        if hasattr(user, 'doctor'): clinic = user.doctor.clinic
        elif hasattr(user, 'receptionist'): clinic = user.receptionist.clinic
        if clinic: return Doctor.objects.filter(clinic=clinic)
        return Doctor.objects.none()

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, format=None):
        username, password = request.data.get('username'), request.data.get('password')
        logger.info(f"Login attempt for username: {username}")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            logger.info(f"Authentication successful for user: {username}")
            
            if not user.is_active:
                logger.warning(f"Login failed - inactive account: {username}")
                # If user has a patient profile, give a clearer message for patients
                if hasattr(user, 'patient'):
                    return Response({'error': 'Account not verified. Please contact support.'}, status=status.HTTP_401_UNAUTHORIZED)
                else:
                    return Response({'error': 'Account is inactive.'}, status=status.HTTP_403_FORBIDDEN)

            # Prefer staff roles (doctor/receptionist) over patient only when the user
            # actually has a doctor or receptionist profile in the database.
            # We DO NOT treat a user as staff solely because `is_staff` is True.
            if hasattr(user, 'doctor') or hasattr(user, 'receptionist'):
                token, _ = AuthToken.objects.get_or_create(user=user)
                profile_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': getattr(user, 'email', ''),
                    'is_ivr_user': getattr(user, 'is_ivr_user', False),
                }
                clinic_data = None
                role = 'staff'
                if hasattr(user, 'doctor'):
                    role = 'doctor'
                    profile_data['name'] = user.doctor.name
                    if user.doctor.clinic:
                        clinic_data = {'id': user.doctor.clinic.id, 'name': user.doctor.clinic.name}
                elif hasattr(user, 'receptionist'):
                    role = 'receptionist'
                    profile_data['name'] = user.get_full_name() or user.username
                    if user.receptionist.clinic:
                        clinic_data = {'id': user.receptionist.clinic.id, 'name': user.receptionist.clinic.name}

                logger.info(f"Staff login successful - Role: {role}, User: {username}")
                response_data = {'token': token.key, 'user': {**profile_data, 'role': role, 'clinic': clinic_data}}
                return Response(response_data, status=status.HTTP_200_OK)

            # Fallback to patient login if user has a patient profile
            if hasattr(user, 'patient'):
                token, _ = AuthToken.objects.get_or_create(user=user)
                patient = user.patient
                profile_data = {
                    'id': user.id,
                    'username': user.username,
                    'name': patient.name,
                    'age': patient.age,
                    'phone_number': patient.phone_number,
                    'role': 'patient'
                }
                logger.info(f"Patient login successful - User: {username}, Patient: {patient.name}")
                user_data = {'token': token.key, 'user': profile_data}
                return Response(user_data, status=status.HTTP_200_OK)

        logger.warning(f"Login failed - invalid credentials for username: {username}")
        return Response({'error': 'Invalid Credentials.'}, status=status.HTTP_400_BAD_REQUEST)

class StaffLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        logger.info(f"Staff login attempt for username: {username}")
        
        user = authenticate(username=username, password=password)
        if user is not None and user.is_staff:
            logger.info(f"Staff authentication successful for user: {username}")
            token, created = AuthToken.objects.get_or_create(user=user)
            # Build a consistent user payload for the frontend
            role = 'unknown'
            profile_data = {
                'id': user.id,
                'username': user.username,
                'email': getattr(user, 'email', ''),
                'is_ivr_user': getattr(user, 'is_ivr_user', False),
            }

            clinic_data = None
            if hasattr(user, 'doctor'):
                role = 'doctor'
                profile_data['name'] = user.doctor.name
                if user.doctor.clinic:
                    clinic_data = {'id': user.doctor.clinic.id, 'name': user.doctor.clinic.name}
            elif hasattr(user, 'receptionist'):
                role = 'receptionist'
                profile_data['name'] = user.get_full_name() or user.username
                if user.receptionist.clinic:
                    clinic_data = {'id': user.receptionist.clinic.id, 'name': user.receptionist.clinic.name}
            else:
                # If user is staff but not assigned a specific profile yet, mark as 'staff'
                if user.is_staff:
                    role = 'staff'

            logger.info(f"Staff login successful - Role: {role}, User: {username}")
            response_data = {'token': token.key, 'user': {**profile_data, 'role': role, 'clinic': clinic_data}}
            return Response(response_data, status=status.HTTP_200_OK)
        
        logger.warning(f"Staff login failed - invalid credentials or not staff: {username}")
        return Response({'error': 'Invalid Credentials or not a staff member.'}, status=status.HTTP_400_BAD_REQUEST)

class MyHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConsultationSerializer
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'patient'): return Consultation.objects.filter(patient=user.patient).order_by('-date')
        return Consultation.objects.none()

class PatientHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConsultationSerializer
    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        if patient_id:
            # Get the patient and find all patients with same normalized phone number
            try:
                patient = Patient.objects.get(id=patient_id)
                normalized_phone = normalize_phone_number(patient.phone_number)
                
                # Find all patients with same phone number (IVR + web accounts)
                matching_patients = []
                for p in Patient.objects.all():
                    if normalize_phone_number(p.phone_number) == normalized_phone:
                        matching_patients.append(p.id)
                
                # Return consultations from ALL matching patients
                return Consultation.objects.filter(patient_id__in=matching_patients).order_by('-date')
            except Patient.DoesNotExist:
                return Consultation.objects.none()
        return Consultation.objects.none()

# ====================================================================
# --- NEW FEATURE: Patient History Search (Emergency/Doctor) ---
# ====================================================================
class PatientHistorySearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        phone_number = request.query_params.get('phone')
        if not phone_number:
            return Response({'error': 'Phone number parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Normalize phone number
            normalized_phone = normalize_phone_number(phone_number)
            matching_patients = []
            
            # Find all patients with matching normalized phone
            for patient in Patient.objects.all():
                if normalize_phone_number(patient.phone_number) == normalized_phone:
                    matching_patients.append(patient.id)
            
            if not matching_patients:
                return Response({
                    'error': 'Patient not found with this phone number.',
                    'searched_phone': phone_number,
                    'normalized_phone': normalized_phone
                }, status=status.HTTP_404_NOT_FOUND)
            
            # DOCTOR RESTRICTION: Only allow doctors to search patients they have consulted before
            if hasattr(request.user, 'doctor'):
                doctor = request.user.doctor
                # Check if this doctor has ever consulted any of these patients
                doctor_consultations = Consultation.objects.filter(
                    doctor=doctor,
                    patient_id__in=matching_patients
                )
                
                if not doctor_consultations.exists():
                    return Response({
                        'error': 'Access denied. You can only search history of patients you have previously consulted.',
                        'searched_phone': phone_number
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Return only consultations by this doctor for these patients
                consultations = doctor_consultations.order_by('-date')
            else:
                # Non-doctors (receptionists, admin) can see all consultations
                consultations = Consultation.objects.filter(
                    patient_id__in=matching_patients
                ).order_by('-date')
            
            # Get patient info
            primary_patient = Patient.objects.get(id=matching_patients[0])
            serializer = ConsultationSerializer(consultations, many=True)
            
            # Debug: Log the response data
            consultation_data = serializer.data
            print(f"DEBUG: Returning {len(consultation_data)} consultations for phone {phone_number}")
            
            return Response({
                'success': True,
                'consultations': consultation_data,
                'patient_info': {
                    'name': primary_patient.name,
                    'phone_number': primary_patient.phone_number,
                    'age': primary_patient.age
                },
                'total_patients_found': len(matching_patients),
                'total_consultations': consultations.count(),
                'message': f'Found {consultations.count()} consultations for {primary_patient.name}'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f'Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, *args, **kwargs):
        """Simple test endpoint to verify API is working"""
        return Response({
            'success': True,
            'message': 'Patient history search API is working',
            'test_consultations': [
                {
                    'id': 1,
                    'date': '2025-11-23',
                    'notes': 'Test consultation notes',
                    'doctor': {'name': 'Test Doctor'}
                }
            ],
            'patient_info': {
                'name': 'Test Patient',
                'phone_number': '+1234567890',
                'age': 30
            },
            'total_consultations': 1
        }, status=status.HTTP_200_OK)


class PatientLiveQueueView(generics.ListAPIView):
    serializer_class = AnonymizedTokenSerializer
    permission_classes = [permissions.AllowAny]
    def get_queryset(self):
        doctor_id = self.kwargs.get('doctor_id')
        date_str = self.kwargs.get('date')
        if not doctor_id or not date_str: return Token.objects.none()
        try: target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError: return Token.objects.none()
        active_statuses = ['waiting', 'confirmed', 'in_consultancy']
        status_priority = Case(When(status='in_consultancy', then=Value(1)), When(status='confirmed', then=Value(2)), When(status='waiting', then=Value(3)), default=Value(4))
        return Token.objects.filter(doctor_id=doctor_id, date=target_date, status__in=active_statuses).order_by(status_priority, F('appointment_time').asc(nulls_last=True), 'created_at')

class ConsultationCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        data = request.data
        patient_id, notes = data.get('patient'), data.get('notes')
        prescription_items_data = data.get('prescription_items', [])
        if not patient_id or not notes: return Response({'error': 'Patient and notes are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            patient = Patient.objects.get(id=patient_id)
            if not hasattr(request.user, 'doctor'): return Response({'error': 'Only doctors can create consultations.'}, status=status.HTTP_403_FORBIDDEN)
            doctor = request.user.doctor
            new_prescription_items = []
            with transaction.atomic():
                consultation = Consultation.objects.create(patient=patient, doctor=doctor, notes=notes)
                for item_data in prescription_items_data:
                    if not item_data.get('medicine_name') or not item_data.get('dosage') or not item_data.get('duration_days'): raise ValueError("Incomplete prescription item data")
                    item = PrescriptionItem.objects.create(consultation=consultation, **item_data)
                    new_prescription_items.append(item)
                try:
                    token = Token.objects.filter(patient=patient, doctor=doctor, date=timezone.now().date(), status__in=['waiting', 'confirmed', 'in_consultancy']).latest('created_at')
                    token.status = 'completed'; token.completed_at = timezone.now(); token.save(update_fields=['status', 'completed_at'])
                except Token.DoesNotExist: print(f"No active token found to complete for patient {patient.id} with doctor {doctor.id} today.")
                if patient.phone_number and new_prescription_items:
                    MORNING_DOSE_TIME, AFTERNOON_DOSE_TIME, EVENING_DOSE_TIME = time(8, 0), time(13, 0), time(20, 0)
                    today = timezone.now().date()
                    for item in new_prescription_items:
                        try:
                            duration = int(item.duration_days)
                            for day in range(1, duration + 1):
                                reminder_date = today + timedelta(days=day); reminder_message = f"Reminder: Take {item.medicine_name} - {item.dosage}."
                                if item.timing_morning: schedule_datetime = datetime.combine(reminder_date, MORNING_DOSE_TIME);
                                if schedule_datetime > timezone.now(): async_task('api.tasks.send_prescription_reminder_sms', patient.phone_number, reminder_message, schedule=schedule_datetime)
                                if item.timing_afternoon: schedule_datetime = datetime.combine(reminder_date, AFTERNOON_DOSE_TIME);
                                if schedule_datetime > timezone.now(): async_task('api.tasks.send_prescription_reminder_sms', patient.phone_number, reminder_message, schedule=schedule_datetime)
                                if item.timing_evening: schedule_datetime = datetime.combine(reminder_date, EVENING_DOSE_TIME);
                                if schedule_datetime > timezone.now(): async_task('api.tasks.send_prescription_reminder_sms', patient.phone_number, reminder_message, schedule=schedule_datetime)
                        except (ValueError, TypeError) as e: print(f"Error scheduling reminders for item {item.id}: Invalid duration '{item.duration_days}'. Error: {e}")
            serializer = ConsultationSerializer(consultation); return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Patient.DoesNotExist: return Response({'error': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as ve: return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e: print(f"Error creating consultation: {e}"); return Response({'error': f'An unexpected error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ====================================================================
# --- START OF ENHANCEMENT: Allow Staff to Cancel Future Tokens ---
# ====================================================================
class TokenUpdateStatusView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TokenSerializer
    lookup_field = 'id'
    def get_queryset(self):
        user = self.request.user; clinic = None
        if hasattr(user, 'doctor'): clinic = user.doctor.clinic
        elif hasattr(user, 'receptionist'): clinic = user.receptionist.clinic
        
        # --- MODIFIED: Allow staff to update tokens for *any date* in their clinic ---
        if clinic: return Token.objects.filter(clinic=clinic)
        
        return Token.objects.none()
    
    def patch(self, request, *args, **kwargs):
        instance = self.get_object(); new_status = request.data.get('status')
        allowed_statuses = ['waiting', 'confirmed', 'completed', 'skipped', 'cancelled', 'in_consultancy']
        if new_status not in allowed_statuses: return Response({'error': 'Invalid status update.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # --- MODIFIED: Allow cancelling a future 'waiting' token ---
        # Only disallow changes if *already* completed or cancelled
        if instance.status in ['completed', 'cancelled']: 
            return Response({'error': f'Cannot change status from {instance.status}.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Staff can cancel, but only doctors should complete
        if new_status == 'completed' and not hasattr(request.user, 'doctor'):
            return Response({'error': 'Only doctors can mark a consultation as completed.'}, status=status.HTTP_403_FORBIDDEN)

        if new_status == 'completed': instance.completed_at = timezone.now()
        else: instance.completed_at = None
        
        instance.status = new_status; instance.save(update_fields=['status', 'completed_at']); return Response(TokenSerializer(instance).data)

# ====================================================================
# --- END OF ENHANCEMENT ---
# ====================================================================


# ====================================================================
# --- IVR LOGIC (WITH CONFIRMATION ENHANCEMENT) ---
# ====================================================================

@csrf_exempt
def ivr_welcome(request):
    try:
        ivr_logger.info(f"IVR Welcome called - Method: {request.method}, From: {request.POST.get('From', 'Unknown')}")
        response = VoiceResponse()
        states = State.objects.all()
        if not states:
            ivr_logger.warning("IVR Welcome: No states configured")
            response.say("Sorry, no clinics are configured. Goodbye.")
            response.hangup()
            return HttpResponse(str(response), content_type='text/xml')
        
        gather = response.gather(num_digits=1, action='/api/ivr/handle-state/')
        say_message = "Welcome to ClinicFlow AI. Please select a state. "
        for i, state in enumerate(states):
            say_message += f"For {state.name}, press {i + 1}. "
        gather.say(say_message)
        response.redirect('/api/ivr/welcome/')
        ivr_logger.info(f"IVR Welcome: Generated response with {states.count()} states")
        return HttpResponse(str(response), content_type='text/xml')
    except Exception as e:
        ivr_logger.error(f"IVR Welcome Error: {e}")
        response = VoiceResponse()
        response.say("Sorry, there was a system error. Please try again later.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')

@csrf_exempt
def ivr_handle_state(request):
    choice = request.POST.get('Digits')
    caller = request.POST.get('From', 'Unknown')
    ivr_logger.info(f"IVR Handle State - From: {caller}, Choice: {choice}")
    
    response = VoiceResponse()
    try:
        state = State.objects.all()[int(choice) - 1]
        districts = District.objects.filter(state=state)
        ivr_logger.info(f"IVR: Selected state {state.name}, found {districts.count()} districts")
        
        if not districts:
            ivr_logger.warning(f"IVR: No districts found for state {state.name}")
            response.say(f"Sorry, no districts found for {state.name}. Please try again.")
            response.redirect('/api/ivr/welcome/')
            return HttpResponse(str(response), content_type='text/xml')
            
        num_digits = len(str(districts.count())) if districts.count() > 0 else 1
        gather = response.gather(num_digits=num_digits, action=f'/api/ivr/handle-district/{state.id}/')
        say_message = f"You selected {state.name}. Please select a district. "
        for i, district in enumerate(districts):
            say_message += f"For {district.name}, press {i + 1}. "
        gather.say(say_message)
        response.redirect('/api/ivr/handle-state/')
        
    except (ValueError, IndexError, TypeError) as e:
        ivr_logger.error(f"IVR Handle State Error: {e}, Choice: {choice}")
        response.say("Invalid choice.")
        response.redirect('/api/ivr/welcome/')
    return HttpResponse(str(response), content_type='text/xml')

@csrf_exempt
def ivr_handle_district(request, state_id):
    choice = request.POST.get('Digits'); response = VoiceResponse()
    try:
        state = State.objects.get(id=state_id); district = District.objects.filter(state=state)[int(choice) - 1]; clinics = Clinic.objects.filter(district=district)
        if not clinics: response.say(f"Sorry, no clinics found for {district.name}. Please try again."); response.redirect(f'/api/ivr/handle-state/'); return HttpResponse(str(response), content_type='text/xml')
        num_digits = len(str(clinics.count())) if clinics.count() > 0 else 1; gather = response.gather(num_digits=num_digits, action=f'/api/ivr/handle-clinic/{district.id}/')
        say_message = f"You selected {district.name}. Please select a clinic. ";
        for i, clinic in enumerate(clinics): say_message += f"For {clinic.name}, press {i + 1}. "
        gather.say(say_message); response.redirect(f'/api/ivr/handle-district/{state.id}/');
    except (ValueError, IndexError, TypeError, State.DoesNotExist, District.DoesNotExist): response.say("Invalid choice or error."); response.redirect('/api/ivr/welcome/')
    return HttpResponse(str(response), content_type='text/xml')

@csrf_exempt
def ivr_handle_clinic(request, district_id):
    choice = request.POST.get('Digits')
    caller = request.POST.get('From', 'Unknown')
    ivr_logger.info(f"IVR Handle Clinic - From: {caller}, Choice: {choice}")
    
    response = VoiceResponse()
    try:
        district = District.objects.get(id=district_id)
        clinic = Clinic.objects.filter(district=district)[int(choice) - 1]
        ivr_logger.info(f"IVR: Selected clinic {clinic.name}")
        
        gather = response.gather(num_digits=1, action=f'/api/ivr/handle-booking-type/{clinic.id}/')
        gather.say(f"You selected {clinic.name}. Press 1 for next available appointment. Press 2 to book for particular date.")
        response.redirect(f'/api/ivr/handle-clinic/{district.id}/')
        
    except (ValueError, IndexError, TypeError, District.DoesNotExist, Clinic.DoesNotExist) as e:
        ivr_logger.error(f"IVR Handle Clinic Error: {e}")
        response.say("Invalid choice or error.")
        response.redirect('/api/ivr/welcome/')
    return HttpResponse(str(response), content_type='text/xml')

# --- MODIFIED: Asks for confirmation ---
@csrf_exempt
def ivr_handle_booking_type(request, clinic_id):
    choice = request.POST.get('Digits')
    caller_phone_number = request.POST.get('From', None)
    ivr_logger.info(f"IVR Booking Type - From: {caller_phone_number}, Choice: {choice}")
    
    response = VoiceResponse()
    
    if not caller_phone_number:
        response.say("We could not identify your phone number. Cannot proceed. Goodbye.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')
    
    try:
        clinic = Clinic.objects.get(id=clinic_id)
        
        if choice == '1':  # Next available appointment - ask specialization first
            specializations = list(Doctor.objects.filter(clinic=clinic).values_list('specialization', flat=True).distinct())
            if not specializations:
                response.say(f"Sorry, no specializations available at {clinic.name}.")
                response.redirect(f'/api/ivr/handle-clinic/{clinic.district_id}/')
                return HttpResponse(str(response), content_type='text/xml')
            
            gather = response.gather(num_digits=1, action=f'/api/ivr/handle-next-available-spec/{clinic.id}/?phone={caller_phone_number}')
            say_message = "Please select a specialization. "
            for i, spec in enumerate(specializations):
                say_message += f"For {spec}, press {i + 1}. "
            gather.say(say_message)
            response.redirect(f'/api/ivr/handle-booking-type/{clinic_id}/')
                
        elif choice == '2':  # Book for particular date - ask specialization first
            specializations = list(Doctor.objects.filter(clinic=clinic).values_list('specialization', flat=True).distinct())
            if not specializations:
                response.say(f"Sorry, no specializations available at {clinic.name}.")
                response.redirect(f'/api/ivr/handle-clinic/{clinic.district_id}/')
                return HttpResponse(str(response), content_type='text/xml')
            
            gather = response.gather(num_digits=1, action=f'/api/ivr/handle-date-specialization/{clinic.id}/?phone={caller_phone_number}')
            say_message = "Please select a specialization. "
            for i, spec in enumerate(specializations):
                say_message += f"For {spec}, press {i + 1}. "
            gather.say(say_message)
            response.redirect(f'/api/ivr/handle-booking-type/{clinic_id}/')
        else:
            response.say("Invalid choice. Please try again.")
            response.redirect(f'/api/ivr/handle-booking-type/{clinic_id}/')
            
    except Clinic.DoesNotExist:
        response.say("Clinic not found.")
        response.redirect('/api/ivr/welcome/')
    except Exception as e:
        ivr_logger.error(f"IVR: Error in booking type: {e}")
        response.say("An application error occurred. Goodbye.")
        response.hangup()
    
    return HttpResponse(str(response), content_type='text/xml')

# --- MODIFIED: Finds slot and asks for confirmation ---
@csrf_exempt
def ivr_handle_specialization(request, clinic_id):
    choice = request.POST.get('Digits'); response = VoiceResponse()
    try:
        clinic = Clinic.objects.get(id=clinic_id); specializations = list(Doctor.objects.filter(clinic=clinic).values_list('specialization', flat=True).distinct()); spec = specializations[int(choice) - 1]
        doctors = Doctor.objects.filter(clinic=clinic, specialization=spec)
        if not doctors.exists(): response.say(f"Sorry, no doctors found for specialization {spec}."); response.redirect(f'/api/ivr/handle-booking-type/{clinic_id}/'); return HttpResponse(str(response), content_type='text/xml')
        num_digits = len(str(doctors.count())) if doctors.count() > 0 else 1; gather = response.gather(num_digits=num_digits, action=f'/api/ivr/handle-doctor/{clinic.id}/{spec}/')
        say_message = f"You selected {spec}. Please select a doctor. ";
        for i, doctor in enumerate(doctors): say_message += f"For Doctor {doctor.name}, press {i + 1}. "
        gather.say(say_message); response.redirect(f'/api/ivr/handle-specialization/{clinic.id}/');
    except (ValueError, IndexError, TypeError, Clinic.DoesNotExist): response.say("Invalid choice or error."); response.redirect(f'/api/ivr/handle-booking-type/{clinic_id}/')
    except Exception as e: print(f"Error in ivr_handle_specialization: {e}"); response.say("An application error occurred."); response.hangup()
    return HttpResponse(str(response), content_type='text/xml')

# --- NEW: Handle next available appointment with specialization ---
@csrf_exempt
def ivr_handle_next_available_spec(request, clinic_id):
    choice = request.POST.get('Digits')
    caller_phone_number = request.POST.get('From', None) or request.GET.get('phone')
    ivr_logger.info(f"IVR Next Available Spec - From: {caller_phone_number}, Choice: {choice}")
    
    response = VoiceResponse()
    if not caller_phone_number:
        response.say("Could not identify phone number. Goodbye.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')
    
    try:
        clinic = Clinic.objects.get(id=clinic_id)
        specializations = list(Doctor.objects.filter(clinic=clinic).values_list('specialization', flat=True).distinct())
        spec = specializations[int(choice) - 1]
        
        # Find next available doctor in this specialization
        doctors = Doctor.objects.filter(clinic=clinic, specialization=spec)
        best_doctor = None
        earliest_date = None
        earliest_slot = None
        
        for doctor in doctors:
            app_date, slot_str = _find_next_available_slot_for_doctor(doctor.id)
            if app_date and slot_str:
                if earliest_date is None or app_date < earliest_date:
                    earliest_date = app_date
                    earliest_slot = slot_str
                    best_doctor = doctor
        
        if best_doctor:
            today = timezone.now().date()
            if earliest_date == today:
                date_spoken = "today"
            elif earliest_date == today + timedelta(days=1):
                date_spoken = "tomorrow"
            else:
                date_spoken = earliest_date.strftime("%B %d")
            
            time_spoken = datetime.strptime(earliest_slot, '%H:%M').strftime('%I:%M %p')
            action_url = f'/api/ivr/confirm-booking/?doctor_id={best_doctor.id}&date={earliest_date.strftime("%Y-%m-%d")}&time={earliest_slot}&phone={caller_phone_number}'
            gather = response.gather(num_digits=1, action=action_url)
            gather.say(f"Next available appointment for {spec} is with Doctor {best_doctor.name} on {date_spoken} at {time_spoken}. Press 1 to confirm, press 2 to cancel.")
            response.redirect(f'/api/ivr/handle-next-available-spec/{clinic_id}/?phone={caller_phone_number}')
        else:
            response.say(f"Sorry, no appointments available for {spec} in the next 30 days. Please try another specialization.")
            response.redirect(f'/api/ivr/handle-booking-type/{clinic_id}/')
            
    except (ValueError, IndexError, TypeError, Clinic.DoesNotExist) as e:
        ivr_logger.error(f"IVR Next Available Spec Error: {e}")
        response.say("Invalid choice or error.")
        response.redirect(f'/api/ivr/handle-booking-type/{clinic_id}/')
    return HttpResponse(str(response), content_type='text/xml')

# --- NEW: Handle date-based specialization selection ---
@csrf_exempt
def ivr_handle_date_specialization(request, clinic_id):
    choice = request.POST.get('Digits')
    caller_phone_number = request.POST.get('From', None) or request.GET.get('phone')
    ivr_logger.info(f"IVR Date Specialization - From: {caller_phone_number}, Choice: {choice}")
    
    response = VoiceResponse()
    if not caller_phone_number:
        response.say("Could not identify phone number. Goodbye.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')
    
    try:
        clinic = Clinic.objects.get(id=clinic_id)
        specializations = list(Doctor.objects.filter(clinic=clinic).values_list('specialization', flat=True).distinct())
        spec = specializations[int(choice) - 1]
        
        gather = response.gather(num_digits=1, action=f'/api/ivr/handle-date-doctor-choice/{clinic_id}/{spec}/?phone={caller_phone_number}')
        gather.say(f"You selected {spec}. Press 1 for next available doctor, or press 2 to choose specific doctor.")
        response.redirect(f'/api/ivr/handle-date-specialization/{clinic_id}/?phone={caller_phone_number}')
        
    except (ValueError, IndexError, TypeError, Clinic.DoesNotExist) as e:
        ivr_logger.error(f"IVR Date Specialization Error: {e}")
        response.say("Invalid choice or error.")
        response.redirect(f'/api/ivr/handle-booking-type/{clinic_id}/')
    return HttpResponse(str(response), content_type='text/xml')

# --- NEW: Handle doctor choice after specialization ---
@csrf_exempt
def ivr_handle_date_doctor_choice(request, clinic_id, spec):
    choice = request.POST.get('Digits')
    caller_phone_number = request.POST.get('From', None) or request.GET.get('phone')
    ivr_logger.info(f"IVR Date Doctor Choice - From: {caller_phone_number}, Choice: {choice}")
    
    response = VoiceResponse()
    if not caller_phone_number:
        response.say("Could not identify phone number. Goodbye.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')
    
    try:
        clinic = Clinic.objects.get(id=clinic_id)
        doctors = Doctor.objects.filter(clinic=clinic, specialization=spec)
        
        if choice == '1':  # Next available doctor for selected date
            gather = response.gather(num_digits=2, action=f'/api/ivr/handle-date-input/{clinic_id}/{spec}/?phone={caller_phone_number}&type=next')
            gather.say("Please enter the date you prefer. Enter day of month as 2 digits. For example, press 0 5 for 5th, or 1 5 for 15th.")
            response.redirect(f'/api/ivr/handle-date-doctor-choice/{clinic_id}/{spec}/?phone={caller_phone_number}')
                
        elif choice == '2':  # Choose specific doctor for selected date
            gather = response.gather(num_digits=2, action=f'/api/ivr/handle-date-input/{clinic_id}/{spec}/?phone={caller_phone_number}&type=specific')
            gather.say("Please enter the date you prefer. Enter day of month as 2 digits. For example, press 0 5 for 5th, or 1 5 for 15th.")
            response.redirect(f'/api/ivr/handle-date-doctor-choice/{clinic_id}/{spec}/?phone={caller_phone_number}')
        else:
            response.say("Invalid choice. Please try again.")
            response.redirect(f'/api/ivr/handle-date-doctor-choice/{clinic_id}/{spec}/?phone={caller_phone_number}')
            
    except (ValueError, IndexError, TypeError, Clinic.DoesNotExist) as e:
        ivr_logger.error(f"IVR Date Doctor Choice Error: {e}")
        response.say("Invalid choice or error.")
        response.redirect(f'/api/ivr/handle-booking-type/{clinic_id}/')
    return HttpResponse(str(response), content_type='text/xml')

# --- NEW: Handle date input ---
@csrf_exempt
def ivr_handle_date_input(request, clinic_id, spec):
    choice = request.POST.get('Digits')
    caller_phone_number = request.POST.get('From', None) or request.GET.get('phone')
    booking_type = request.GET.get('type', 'next')  # 'next' or 'specific'
    ivr_logger.info(f"IVR Date Input - From: {caller_phone_number}, Choice: {choice}, Type: {booking_type}")
    
    response = VoiceResponse()
    if not caller_phone_number:
        response.say("Could not identify phone number. Goodbye.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')
    
    try:
        # Parse the day input
        day = int(choice)
        if day < 1 or day > 31:
            raise ValueError("Invalid day")
        
        # Calculate the target date (current month)
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year
        
        # If the day is in the past this month, use next month
        if day < today.day:
            if current_month == 12:
                target_date = today.replace(year=current_year + 1, month=1, day=day)
            else:
                target_date = today.replace(month=current_month + 1, day=day)
        else:
            target_date = today.replace(day=day)
        
        clinic = Clinic.objects.get(id=clinic_id)
        doctors = Doctor.objects.filter(clinic=clinic, specialization=spec)
        
        if booking_type == 'next':  # Next available doctor for this date
            best_doctor = None
            best_slot = None
            
            for doctor in doctors:
                # Get fresh available slots (checks for bookings in real-time)
                available_slots = _get_available_slots_for_doctor(doctor.id, target_date.strftime('%Y-%m-%d'))
                if available_slots:
                    # Filter out past slots if it's today
                    if target_date == today:
                        # Get current time in local timezone
                        now_local = timezone.localtime(timezone.now())
                        current_time = now_local.time()
                        future_slots = [
                            slot for slot in available_slots
                            if datetime.strptime(slot, '%H:%M').time() > current_time
                        ]
                        if future_slots:
                            best_doctor = doctor
                            best_slot = future_slots[0]
                            ivr_logger.info(f"IVR: Found available slot {best_slot} with Dr. {doctor.name} on {target_date}")
                            break
                    else:
                        best_doctor = doctor
                        best_slot = available_slots[0]
                        ivr_logger.info(f"IVR: Found available slot {best_slot} with Dr. {doctor.name} on {target_date}")
                        break
            
            if best_doctor and best_slot:
                date_spoken = "today" if target_date == today else target_date.strftime("%B %d")
                time_spoken = datetime.strptime(best_slot, '%H:%M').strftime('%I:%M %p')
                action_url = f'/api/ivr/confirm-booking/?doctor_id={best_doctor.id}&date={target_date.strftime("%Y-%m-%d")}&time={best_slot}&phone={caller_phone_number}'
                gather = response.gather(num_digits=1, action=action_url)
                gather.say(f"Available appointment on {date_spoken} at {time_spoken} with Doctor {best_doctor.name}. Press 1 to confirm, press 2 to cancel.")
                response.redirect(f'/api/ivr/handle-date-input/{clinic_id}/{spec}/?phone={caller_phone_number}&type=next')
            else:
                response.say(f"Sorry, no appointments available on {target_date.strftime('%B %d')} for {spec}. Please try another date.")
                response.redirect(f'/api/ivr/handle-date-doctor-choice/{clinic_id}/{spec}/?phone={caller_phone_number}')
                
        else:  # Specific doctor selection for this date
            if not doctors.exists():
                response.say(f"Sorry, no doctors found for {spec}.")
                response.redirect(f'/api/ivr/handle-booking-type/{clinic_id}/')
                return HttpResponse(str(response), content_type='text/xml')
            
            gather = response.gather(num_digits=1, action=f'/api/ivr/handle-specific-doctor-date/{clinic_id}/{spec}/{target_date.strftime("%Y-%m-%d")}/?phone={caller_phone_number}')
            say_message = f"Please select a doctor for {target_date.strftime('%B %d')}. "
            for i, doctor in enumerate(doctors):
                say_message += f"For Doctor {doctor.name}, press {i + 1}. "
            gather.say(say_message)
            response.redirect(f'/api/ivr/handle-date-input/{clinic_id}/{spec}/?phone={caller_phone_number}&type=specific')
            
    except (ValueError, Clinic.DoesNotExist) as e:
        ivr_logger.error(f"IVR Date Input Error: {e}")
        response.say("Invalid date. Please try again.")
        response.redirect(f'/api/ivr/handle-date-doctor-choice/{clinic_id}/{spec}/?phone={caller_phone_number}')
    return HttpResponse(str(response), content_type='text/xml')

# --- NEW: Handle specific doctor with date ---
@csrf_exempt
def ivr_handle_specific_doctor_date(request, clinic_id, spec, date_str):
    choice = request.POST.get('Digits')
    caller_phone_number = request.POST.get('From', None) or request.GET.get('phone')
    ivr_logger.info(f"IVR Specific Doctor Date - From: {caller_phone_number}, Choice: {choice}, Date: {date_str}")
    
    response = VoiceResponse()
    if not caller_phone_number:
        response.say("Could not identify phone number. Goodbye.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')
    
    try:
        clinic = Clinic.objects.get(id=clinic_id)
        doctor = Doctor.objects.filter(clinic=clinic, specialization=spec)[int(choice) - 1]
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get fresh available slots (real-time check)
        available_slots = _get_available_slots_for_doctor(doctor.id, date_str)
        ivr_logger.info(f"IVR: Available slots for Dr. {doctor.name} on {date_str}: {available_slots}")
        
        if available_slots:
            # Filter out past slots if it's today
            if target_date == timezone.now().date():
                # Get current time in local timezone
                now_local = timezone.localtime(timezone.now())
                current_time = now_local.time()
                future_slots = [
                    slot for slot in available_slots
                    if datetime.strptime(slot, '%H:%M').time() > current_time
                ]
                if future_slots:
                    best_slot = future_slots[0]
                    ivr_logger.info(f"IVR: Selected future slot {best_slot} for Dr. {doctor.name}")
                else:
                    ivr_logger.warning(f"IVR: No future slots available today for Dr. {doctor.name}")
                    response.say(f"Sorry, no more slots available today for Doctor {doctor.name}. Please try another date.")
                    response.redirect(f'/api/ivr/handle-date-doctor-choice/{clinic_id}/{spec}/?phone={caller_phone_number}')
                    return HttpResponse(str(response), content_type='text/xml')
            else:
                best_slot = available_slots[0]
                ivr_logger.info(f"IVR: Selected slot {best_slot} for Dr. {doctor.name} on {date_str}")
            
            date_spoken = "today" if target_date == timezone.now().date() else target_date.strftime("%B %d")
            time_spoken = datetime.strptime(best_slot, '%H:%M').strftime('%I:%M %p')
            action_url = f'/api/ivr/confirm-booking/?doctor_id={doctor.id}&date={date_str}&time={best_slot}&phone={caller_phone_number}'
            gather = response.gather(num_digits=1, action=action_url)
            gather.say(f"Available slot with Doctor {doctor.name} on {date_spoken} at {time_spoken}. Press 1 to confirm, press 2 to cancel.")
            response.redirect(f'/api/ivr/handle-specific-doctor-date/{clinic_id}/{spec}/{date_str}/?phone={caller_phone_number}')
        else:
            ivr_logger.warning(f"IVR: No available slots for Dr. {doctor.name} on {date_str}")
            response.say(f"Sorry, Doctor {doctor.name} has no available slots on {target_date.strftime('%B %d')}. Please try another doctor or date.")
            response.redirect(f'/api/ivr/handle-date-doctor-choice/{clinic_id}/{spec}/?phone={caller_phone_number}')
            
    except (ValueError, IndexError, TypeError, Clinic.DoesNotExist, Doctor.DoesNotExist) as e:
        ivr_logger.error(f"IVR Specific Doctor Date Error: {e}")
        response.say("Invalid choice or error.")
        response.redirect(f'/api/ivr/handle-date-doctor-choice/{clinic_id}/{spec}/?phone={caller_phone_number}')
    return HttpResponse(str(response), content_type='text/xml')

# --- NEW: Handle specific doctor selection ---
@csrf_exempt
def ivr_handle_specific_doctor(request, clinic_id, spec):
    choice = request.POST.get('Digits')
    caller_phone_number = request.POST.get('From', None) or request.GET.get('phone')
    ivr_logger.info(f"IVR Specific Doctor - From: {caller_phone_number}, Choice: {choice}")
    
    response = VoiceResponse()
    if not caller_phone_number:
        response.say("Could not identify phone number. Goodbye.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')
    
    try:
        clinic = Clinic.objects.get(id=clinic_id)
        doctor = Doctor.objects.filter(clinic=clinic, specialization=spec)[int(choice) - 1]
        appointment_date, slot_str = _find_next_available_slot_for_doctor(doctor.id)
        
        if appointment_date and slot_str:
            today = timezone.now().date()
            if appointment_date == today:
                date_spoken = "today"
            elif appointment_date == today + timedelta(days=1):
                date_spoken = "tomorrow"
            else:
                date_spoken = appointment_date.strftime("%B %d")
            
            time_spoken = datetime.strptime(slot_str, '%H:%M').strftime('%I:%M %p')
            action_url = f'/api/ivr/confirm-booking/?doctor_id={doctor.id}&date={appointment_date.strftime("%Y-%m-%d")}&time={slot_str}&phone={caller_phone_number}'
            gather = response.gather(num_digits=1, action=action_url)
            gather.say(f"The next available slot with Doctor {doctor.name} is at {time_spoken} on {date_spoken}. Press 1 to confirm, press 2 to cancel.")
            response.redirect(f'/api/ivr/handle-specific-doctor/{clinic_id}/{spec}/?phone={caller_phone_number}')
        else:
            response.say(f"Sorry, Doctor {doctor.name} has no available slots in the coming days. Please try another doctor.")
            response.redirect(f'/api/ivr/handle-date-doctor-choice/{clinic_id}/{spec}/?phone={caller_phone_number}')
            
    except (ValueError, IndexError, TypeError, Clinic.DoesNotExist, Doctor.DoesNotExist) as e:
        ivr_logger.error(f"IVR Specific Doctor Error: {e}")
        response.say("Invalid choice or error.")
        response.redirect(f'/api/ivr/handle-date-doctor-choice/{clinic_id}/{spec}/?phone={caller_phone_number}')
    return HttpResponse(str(response), content_type='text/xml')

# --- MODIFIED: Finds slot and asks for confirmation ---
@csrf_exempt
def ivr_handle_doctor(request, clinic_id, spec):
    choice = request.POST.get('Digits'); response = VoiceResponse(); caller_phone_number = request.POST.get('From', None)
    if not caller_phone_number: response.say("Could not identify phone number. Goodbye."); response.hangup(); return HttpResponse(str(response), content_type='text/xml')
    try:
        clinic = Clinic.objects.get(id=clinic_id); doctor = Doctor.objects.filter(clinic_id=clinic_id, specialization=spec)[int(choice) - 1]
        appointment_date, slot_str = _find_next_available_slot_for_doctor(doctor.id)
        if appointment_date and slot_str:
             # --- ASK FOR CONFIRMATION ---
             date_spoken = "today" if appointment_date == timezone.now().date() else appointment_date.strftime("%B %d")
             time_spoken = datetime.strptime(slot_str, '%H:%M').strftime('%I:%M %p')
             action_url = f'/api/ivr/confirm-booking/?doctor_id={doctor.id}&date={appointment_date.strftime("%Y-%m-%d")}&time={slot_str}&phone={caller_phone_number}'
             gather = response.gather(num_digits=1, action=action_url)
             gather.say(f"The next available slot with Doctor {doctor.name} is at {time_spoken} on {date_spoken}. Press 1 to confirm, press 2 to cancel.")
             response.redirect(f'/api/ivr/handle-doctor/{clinic_id}/{spec}/') # Redirect if no input
             # --- END ASK FOR CONFIRMATION ---
        else:
             response.say(f"Sorry, Doctor {doctor.name} has no available slots in the coming days. Please try another doctor or call back later.")
             response.redirect(f'/api/ivr/handle-specialization/{clinic_id}/') # Go back to spec selection
    except (ValueError, IndexError, TypeError): response.say("Invalid choice."); response.redirect(f'/api/ivr/handle-specialization/{clinic_id}/')
    except Clinic.DoesNotExist: response.say("Clinic not found."); response.redirect('/api/ivr/welcome/')
    except Doctor.DoesNotExist: response.say("Doctor not found."); response.redirect(f'/api/ivr/handle-specialization/{clinic_id}/')
    except Exception as e: print(f"Error in ivr_handle_doctor: {e}"); response.say("An application error occurred."); response.hangup()
    return HttpResponse(str(response), content_type='text/xml')

# ====================================================================
# --- NEW VIEW: Handles IVR Booking Confirmation ---
# ====================================================================
@csrf_exempt
def ivr_confirm_booking(request):
    choice = request.POST.get('Digits')
    caller = request.POST.get('From', 'Unknown')
    ivr_logger.info(f"IVR Confirm Booking - From: {caller}, Choice: {choice}")
    
    response = VoiceResponse()
    # Get details passed in the action URL's query parameters
    # Prefer GET query params (action URL) but fall back to POST form fields (Twilio sometimes posts From)
    doctor_id = request.GET.get('doctor_id') or request.POST.get('doctor_id')
    date_str = request.GET.get('date') or request.POST.get('date')
    time_str = request.GET.get('time') or request.POST.get('time')
    caller_phone_number = (request.GET.get('phone') or request.POST.get('phone') or request.POST.get('From'))

    ivr_logger.info(f"IVR Confirm: doctor_id={doctor_id}, date={date_str}, time={time_str}, phone={caller_phone_number}")

    if not all([doctor_id, date_str, time_str, caller_phone_number]):
        # Try parsing raw QUERY_STRING as a last resort (some test clients may not populate request.GET)
        try:
            from urllib.parse import parse_qs
            raw_qs = request.META.get('QUERY_STRING', '')
            parsed = parse_qs(raw_qs)
            # parsed values are lists
            if not doctor_id and parsed.get('doctor_id'): doctor_id = parsed.get('doctor_id')[0]
            if not date_str and parsed.get('date'): date_str = parsed.get('date')[0]
            if not time_str and parsed.get('time'): time_str = parsed.get('time')[0]
            if not caller_phone_number and parsed.get('phone'): caller_phone_number = parsed.get('phone')[0]
        except Exception:
            pass
        # Debug output to help tests understand why booking info was missing
        ivr_logger.error(f"IVR Confirm: Missing booking info. PATH={request.get_full_path()} QUERY_STRING={request.META.get('QUERY_STRING')} GET={dict(request.GET)} POST={dict(request.POST)} ParsedFallback_doctor={doctor_id} date={date_str} time={time_str} phone={caller_phone_number}")
        response.say("Sorry, booking information is missing. Please start over.")
        response.redirect('/api/ivr/welcome/')
        return HttpResponse(str(response), content_type='text/xml')

    try:
        if choice == '1': # Confirm booking
            ivr_logger.info(f"IVR: Confirming booking for doctor {doctor_id} on {date_str} at {time_str}")
            doctor = Doctor.objects.get(id=int(doctor_id))
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Double-check slot availability before booking
            available_slots = _get_available_slots_for_doctor(doctor.id, appointment_date.strftime('%Y-%m-%d'))
            if time_str not in available_slots:
                ivr_logger.warning(f"IVR: Slot {time_str} no longer available for doctor {doctor.id} on {appointment_date}")
                response.say("Sorry, this slot was just booked by someone else. Please try again.")
                response.hangup()
                return HttpResponse(str(response), content_type='text/xml')
            
            # Attempt to create the token using the helper
            # This helper now ALSO creates a User and sends a password SMS if it's a new patient
            new_token = _create_ivr_token(doctor, appointment_date, time_str, caller_phone_number)

            if new_token:
                # Booking succeeded
                ivr_logger.info(f"IVR: Booking successful - Token {new_token.id} created for {caller_phone_number}")
                date_spoken = "today" if new_token.date == timezone.now().date() else new_token.date.strftime("%B %d")
                time_spoken = new_token.appointment_time.strftime('%I:%M %p')
                token_num_spoken = f"Your token number is {new_token.token_number}." if new_token.token_number else ""

                # Send the *appointment confirmation* SMS
                # The "welcome" SMS is sent from the helper
                message = (f"Your appointment with Dr. {doctor.name} is confirmed for "
                           f"{time_spoken} on {date_spoken}. {token_num_spoken}")
                try: 
                    send_sms_notification(caller_phone_number, message)
                    ivr_logger.info(f"IVR: Confirmation SMS sent to {caller_phone_number}")
                except Exception as e: 
                    ivr_logger.error(f"IVR Confirm: Failed to send APPOINTMENT SMS to {caller_phone_number}: {e}")

                response.say(f"Booking confirmed for {time_spoken} on {date_spoken}. Confirmation SMS has been sent. Goodbye.")
                response.hangup()
            else:
                # Booking failed - check if it's because patient already has active token
                from api.models import Patient
                try:
                    patient = Patient.objects.get(phone_number=caller_phone_number)
                    existing_tokens = Token.objects.filter(patient=patient).exclude(status__in=['completed', 'cancelled', 'skipped'])
                    if existing_tokens.exists():
                        existing_token = existing_tokens.first()
                        existing_date_spoken = "today" if existing_token.date == timezone.now().date() else existing_token.date.strftime("%B %d")
                        existing_time_spoken = existing_token.appointment_time.strftime('%I:%M %p') if existing_token.appointment_time else "unscheduled"
                        ivr_logger.warning(f"IVR: Booking failed - patient already has appointment on {existing_token.date} at {existing_token.appointment_time}")
                        response.say(f"You already have an appointment scheduled for {existing_time_spoken} on {existing_date_spoken}. Please cancel that first or contact the clinic.")
                    else:
                        ivr_logger.warning(f"IVR: Booking failed for {caller_phone_number} - slot may be taken")
                        response.say("Sorry, this slot was just taken by someone else. Please try again.")
                except Patient.DoesNotExist:
                    response.say("Sorry, we could not process your booking. Please try again.")
                response.hangup()

        elif choice == '2': # Cancel booking attempt
            ivr_logger.info(f"IVR: Booking cancelled by user {caller_phone_number}")
            response.say("Booking cancelled. Goodbye.")
            response.hangup()
        else: # Invalid digit
            ivr_logger.warning(f"IVR: Invalid choice '{choice}' from {caller_phone_number}")
            response.say("Invalid choice. Hanging up.")
            response.hangup() # End call on invalid input to avoid loops

    except Doctor.DoesNotExist:
        ivr_logger.error(f"IVR: Doctor {doctor_id} not found")
        response.say("Doctor information error. Please start over.")
        response.redirect('/api/ivr/welcome/')
    except ValueError as e: # Handle potential errors converting date/time/doctor_id
        ivr_logger.error(f"IVR: Value error in confirm booking: {e}")
        response.say("Booking information error. Please start over.")
        response.redirect('/api/ivr/welcome/')
    except Exception as e:
        ivr_logger.error(f"IVR: Error in confirm booking: {e}")
        response.say("An application error occurred during confirmation. Goodbye.")
        response.hangup()

    return HttpResponse(str(response), content_type='text/xml')
# ====================================================================
# --- END IVR ENHANCEMENTS ---
# ====================================================================

# --- SMS CANCELLATION LOGIC ---
@csrf_exempt
def handle_incoming_sms(request):
    from_number = request.POST.get('From', None)
    body = request.POST.get('Body', '').strip().upper()
    # Try different Twilio imports for SMS response
    try:
        from twilio.twiml.messaging_response import MessagingResponse
        response = MessagingResponse()
    except ImportError:
        try:
            from twilio.twiml import MessagingResponse
            response = MessagingResponse()
        except ImportError:
            # Fallback to VoiceResponse which also works for SMS in some versions
            response = VoiceResponse()
    if from_number and body == 'CANCEL':
        today = timezone.now().date()
        try:
            patient = Patient.objects.get(phone_number=from_number)
            # Find the next active token (today or future) for cancellation via SMS
            active_token = Token.objects.filter(
                patient=patient, date__gte=today, status__in=['waiting', 'confirmed']
            ).order_by('date', 'appointment_time').first()

            if not active_token: raise Token.DoesNotExist

            active_token.status = 'cancelled'
            active_token.save(update_fields=['status'])
            message = f"Your appointment for {active_token.date.strftime('%B %d')} has been successfully cancelled. Thank you."
            response.message(message)
            print(f"Cancelled appointment for {from_number} via SMS.")
        except Patient.DoesNotExist: message = "We could not find an account associated with your phone number."; response.message(message); print(f"Received 'CANCEL' from unknown number: {from_number}")
        except Token.DoesNotExist: message = "You do not have an active appointment scheduled to cancel."; response.message(message); print(f"Received 'CANCEL' from {from_number}, but no active token was found.")
        except Exception as e: print(f"Error processing SMS cancellation for {from_number}: {e}"); message = "An error occurred trying to cancel. Contact clinic."; response.message(message)
    else: print(f"Received non-cancellation SMS from {from_number}: '{body}' - No action taken."); pass
    return HttpResponse(str(response), content_type='text/xml')

# ====================================================================
# --- AI PATIENT HISTORY SUMMARIZER (LAZY LOADING) ---
# ====================================================================

# Initialize global variable as None.
# We will load the AI model ONLY when the first request comes in.
ai_summarizer = None
ai_model_name = None
ai_load_lock = threading.Lock()
logger = logging.getLogger(__name__)


def load_ai_model(model_name: str = "sshleifer/distilbart-cnn-12-6"):
    """Load the HF summarization pipeline into the global `ai_summarizer`.

    This function is idempotent and thread-safe. It returns True on success,
    False on failure (and logs the exception).
    """
    global ai_summarizer, ai_model_name

    # Fast path
    if ai_summarizer is not None:
        return True

    with ai_load_lock:
        if ai_summarizer is not None:
            return True
        try:
            # Import lazily to avoid heavy deps at module import time
            from transformers import pipeline as _hf_pipeline
            ai_model_name = model_name
            logger.info(f"Loading AI model {ai_model_name}...")
            ai_summarizer = _hf_pipeline("summarization", model=ai_model_name)
            logger.info("AI model loaded successfully.")
            return True
        except Exception as e:
            logger.exception("Failed to load AI model: %s", e)
            ai_summarizer = None
            ai_model_name = None
            return False

class PatientHistorySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        """
        Returns a structured JSON summary of the patient's consultation history.

        Behavior:
        - Lazy-loads the HF summarization pipeline on first use.
        - Sends the concatenated history with a short instruction that asks the model
          to output a JSON object with the following keys:
            - chief_complaint
            - history_of_present_illness
            - past_medical_history
            - medications
            - allergies
            - examination_findings
            - assessment
            - plan
        - Attempts to parse JSON out of the model output. If parsing fails, falls back
          to returning a plain-text summary under the key `summary_text`.
        """
        global ai_summarizer, ai_model_name

        try:
            # 1. Load model if necessary
            # Ensure model is loaded (may be loaded in background by admin/dev)
            if ai_summarizer is None:
                ok = load_ai_model()
                if not ok:
                    return Response({"error": "AI model not available. Trigger load via POST /api/patient-summary/load/ or install model dependencies."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # 2. Fetch consultations
            consultations = Consultation.objects.filter(patient__id=patient_id).order_by('date')
            if not consultations.exists():
                return Response({"error": "No previous consultation history found."}, status=status.HTTP_404_NOT_FOUND)

            # 3. Combine notes into a single prompt
            full_text = []
            for consult in consultations:
                if consult.notes:
                    full_text.append(f"Date: {consult.date}. Notes: {consult.notes}")
            joined = "\n\n".join(full_text)

            if len(joined.split()) < 30:
                return Response({"error": "History too short for AI summarization.", "recent_notes": joined}, status=status.HTTP_400_BAD_REQUEST)

            # 4. Build instruction + payload asking for JSON output
            instruction = (
                "Extract a structured patient history from the text below. "
                "Output only a valid JSON object with these keys: chief_complaint, history_of_present_illness, "
                "past_medical_history, medications, allergies, examination_findings, assessment, plan. "
                "If a field is not present, set it to an empty string. Do not include any additional commentary.\n\n"
            )
            prompt = instruction + "PATIENT_HISTORY:\n" + joined

            # 5. Ask the configured AI backend to summarize.
            # This will dispatch to local pipeline or a hosted API depending on settings.
            from .ai_client import summarize_text, get_model_name

            try:
                result = summarize_text(prompt, max_length=512, min_length=64)
            except RuntimeError as re:
                return Response({"error": str(re)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            # normalize result
            raw_text = ''
            if isinstance(result, dict):
                raw_text = result.get('summary_text', '')
            elif isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                raw_text = result[0].get('summary_text', '')
            else:
                raw_text = str(result)
            ai_model_name = get_model_name()

            # 6. Try to extract JSON from the returned text
            import re, json
            # Find first {...} block
            m = re.search(r"\{[\s\S]*\}", raw_text)
            if m:
                candidate = m.group(0)
                try:
                    parsed = json.loads(candidate)
                    # Ensure all keys exist
                    keys = [
                        'chief_complaint', 'history_of_present_illness', 'past_medical_history',
                        'medications', 'allergies', 'examination_findings', 'assessment', 'plan'
                    ]
                    structured = {k: (parsed.get(k, '') if isinstance(parsed.get(k, ''), str) else parsed.get(k, '')) for k in keys}
                    # Also include a short raw summary for convenience
                    structured['raw_summary'] = raw_text
                    structured['model'] = ai_model_name
                    return Response(structured)
                except Exception:
                    # fall through to text fallback
                    pass

            # 7. Fallback: return plain text summary
            return Response({"summary_text": raw_text, "model": ai_model_name})

        except Exception as e:
            print(f"AI ERROR: {str(e)}")
            return Response({"error": str(e)}, status=500)
# --- ADD THIS TO THE BOTTOM OF api/views.py ---
 


class AIModelStatusView(APIView):
    """Simple status endpoint to check whether the AI summarizer is loaded."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .ai_client import is_model_loaded, get_model_name
        return Response({
            'loaded': bool(is_model_loaded()),
            'model': get_model_name()
        })


class AIModelLoadView(APIView):
    """Trigger loading of the AI model.

    POST -> starts loading (synchronously) and returns 200 on success or 500 on failure.
    If you want non-blocking behavior, call this endpoint and it will start a background
    thread and return 202 Accepted.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from .ai_client import is_model_loaded, load_local_model, load_model_background, get_model_name

        # If model/backend already reported as available, return ready
        if is_model_loaded():
            return Response({'loaded': True, 'model': get_model_name()})

        background = request.query_params.get('background', '0') in ['1', 'true', 'True']
        if background:
            load_model_background()
            return Response({'message': 'AI model loading started in background.'}, status=status.HTTP_202_ACCEPTED)

        ok = load_local_model()
        if ok:
            return Response({'loaded': True, 'model': get_model_name()})
        else:
            return Response({'error': 'Failed to load AI model. Check logs.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIHistorySummaryView(APIView):
    """Simple AI summary endpoint that matches frontend expectations."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            patient_history = request.data.get('patient_history', '')
            phone = request.data.get('phone', '')
            
            if not patient_history.strip():
                return Response({'error': 'Patient history is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            from .ai_client import summarize_text, get_model_name
            
            try:
                prompt = f"Summarize the following patient medical history in a clear, professional format:\n\n{patient_history}"
                result = summarize_text(prompt, max_length=300, min_length=50)
                
                summary = ''
                if isinstance(result, dict):
                    summary = result.get('summary_text', str(result))
                elif isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], dict):
                        summary = result[0].get('summary_text', str(result[0]))
                    else:
                        summary = str(result[0])
                else:
                    summary = str(result)
                
                return Response({
                    'summary': summary,
                    'model': get_model_name(),
                    'phone': phone
                })
                
            except RuntimeError as e:
                return Response({'error': f'AI service unavailable: {str(e)}'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            print(f"AI Summary error: {str(e)}")
            return Response({'error': 'Failed to generate AI summary'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MeView(APIView):
    """Return the normalized profile for the currently authenticated user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Prefer staff roles
        if user.is_staff or hasattr(user, 'doctor') or hasattr(user, 'receptionist'):
            profile = {
                'id': user.id,
                'username': user.username,
                'email': getattr(user, 'email', ''),
                'is_ivr_user': getattr(user, 'is_ivr_user', False),
            }
            clinic = None
            role = 'staff'
            if hasattr(user, 'doctor'):
                role = 'doctor'
                profile['name'] = user.doctor.name
                if user.doctor.clinic:
                    clinic = {'id': user.doctor.clinic.id, 'name': user.doctor.clinic.name}
            elif hasattr(user, 'receptionist'):
                role = 'receptionist'
                profile['name'] = user.get_full_name() or user.username
                if user.receptionist.clinic:
                    clinic = {'id': user.receptionist.clinic.id, 'name': user.receptionist.clinic.name}

            profile['role'] = role
            profile['clinic'] = clinic
            return Response({'user': profile})

        # Fallback to patient
        if hasattr(user, 'patient'):
            p = user.patient
            profile = {
                'id': user.id,
                'username': user.username,
                'name': p.name,
                'age': p.age,
                'phone_number': p.phone_number,
                'role': 'patient'
            }
            return Response({'user': profile})

        # Generic staff fallback
        return Response({'user': {'id': user.id, 'username': user.username, 'role': 'staff'}})

# ====================================================================
# --- SCHEDULE MANAGEMENT VIEWS ---
# ====================================================================

class DoctorScheduleListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all doctor schedules for the receptionist's clinic"""
        if not hasattr(request.user, 'receptionist'):
            return Response({'error': 'Only receptionists can manage schedules.'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            clinic = request.user.receptionist.clinic
            doctors = Doctor.objects.filter(clinic=clinic)
            schedules = []
            
            for doctor in doctors:
                try:
                    schedule = DoctorSchedule.objects.get(doctor=doctor)
                    serialized_data = DoctorScheduleSerializer(schedule).data
                    schedules.append(serialized_data)
                except DoctorSchedule.DoesNotExist:
                    # Create default schedule if none exists
                    from datetime import time
                    default_schedule = DoctorSchedule.objects.create(
                        doctor=doctor,
                        start_time=time(9, 0),
                        end_time=time(17, 0),
                        slot_duration_minutes=15
                    )
                    serialized_data = DoctorScheduleSerializer(default_schedule).data
                    schedules.append(serialized_data)
                except Exception as e:
                    print(f"Error processing doctor {doctor.id}: {e}")
                    # Skip this doctor if there's an error
                    continue
            
            return Response(schedules)
        except Exception as e:
            return Response({'error': f'Failed to load schedules: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DoctorScheduleUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, doctor_id):
        """Update a doctor's schedule"""
        if not hasattr(request.user, 'receptionist'):
            return Response({'error': 'Only receptionists can manage schedules.'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            doctor = Doctor.objects.get(id=doctor_id, clinic=request.user.receptionist.clinic)
            schedule, created = DoctorSchedule.objects.get_or_create(doctor=doctor)
            
            # Update schedule fields
            if 'start_time' in request.data:
                from datetime import time as time_obj
                time_str = str(request.data['start_time']).strip()
                parts = time_str.split(':')
                hour = int(parts[0])
                minute = int(parts[1])
                schedule.start_time = time_obj(hour, minute)
                    
            if 'end_time' in request.data:
                from datetime import time as time_obj
                time_str = str(request.data['end_time']).strip()
                parts = time_str.split(':')
                hour = int(parts[0])
                minute = int(parts[1])
                schedule.end_time = time_obj(hour, minute)
                    
            if 'slot_duration_minutes' in request.data:
                schedule.slot_duration_minutes = int(request.data['slot_duration_minutes'])
                
            if 'max_slots_per_day' in request.data:
                max_slots = request.data['max_slots_per_day']
                schedule.max_slots_per_day = int(max_slots) if max_slots else None
                
            if 'is_active' in request.data:
                schedule.is_active = bool(request.data['is_active'])
            
            schedule.save()
            return Response(DoctorScheduleSerializer(schedule).data)
            
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found in your clinic.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SimpleAISummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            patient_history = request.data.get('patient_history', '')
            phone = request.data.get('phone', '')
            
            if not patient_history.strip():
                return Response({'error': 'Patient history is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Enhanced extractive summary with medical structure
            lines = [line.strip() for line in patient_history.split('\n') if line.strip()]
            
            # Extract key medical information
            complaints = []
            diagnoses = []
            treatments = []
            medications = []
            vitals = []
            
            for line in lines:
                line_lower = line.lower()
                if any(word in line_lower for word in ['complaint', 'complain', 'symptom', 'pain', 'ache', 'fever', 'headache']):
                    complaints.append(line)
                elif any(word in line_lower for word in ['diagnosis', 'diagnosed', 'condition', 'disease']):
                    diagnoses.append(line)
                elif any(word in line_lower for word in ['treatment', 'therapy', 'procedure', 'surgery']):
                    treatments.append(line)
                elif any(word in line_lower for word in ['prescribed', 'medication', 'medicine', 'drug', 'tablet', 'capsule']):
                    medications.append(line)
                elif any(word in line_lower for word in ['blood pressure', 'temperature', 'pulse', 'weight', 'bp', 'temp']):
                    vitals.append(line)
            
            # Build structured summary
            summary_parts = []
            
            if complaints:
                summary_parts.append(f"CHIEF COMPLAINTS: {'; '.join(complaints[:2])}")
            
            if vitals:
                summary_parts.append(f"VITALS: {'; '.join(vitals[:2])}")
            
            if diagnoses:
                summary_parts.append(f"DIAGNOSIS: {'; '.join(diagnoses[:2])}")
            
            if treatments:
                summary_parts.append(f"TREATMENT: {'; '.join(treatments[:2])}")
            
            if medications:
                summary_parts.append(f"MEDICATIONS: {'; '.join(medications[:2])}")
            
            if summary_parts:
                summary = "MEDICAL SUMMARY:\n\n" + "\n\n".join(summary_parts)
            else:
                # Fallback to general medical lines
                medical_lines = [line for line in lines if any(word in line.lower() for word in [
                    'patient', 'doctor', 'notes', 'consultation', 'examination', 'advised'
                ])]
                if medical_lines:
                    summary = "CONSULTATION SUMMARY:\n\n" + "\n".join(medical_lines[:3])
                else:
                    summary = "Patient consultation history available. Medical records contain relevant clinical information."
            
            return Response({
                'summary': summary,
                'model': 'clinical_extractive_summarizer',
                'phone': phone
            })
            
        except Exception as e:
            return Response({'error': 'Failed to generate summary'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class AIHistorySummaryView(APIView):
    """Simple AI summary endpoint that matches frontend expectations."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            patient_history = request.data.get('patient_history', '')
            phone = request.data.get('phone', '')
            
            if not patient_history.strip():
                return Response({'error': 'Patient history is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Use the AI client to generate summary
            from .ai_client import summarize_text, get_model_name
            
            try:
                prompt = f"Summarize the following patient medical history in a clear, professional format:\n\n{patient_history}"
                result = summarize_text(prompt, max_length=300, min_length=50)
                
                # Extract summary text
                summary = ''
                if isinstance(result, dict):
                    summary = result.get('summary_text', str(result))
                elif isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], dict):
                        summary = result[0].get('summary_text', str(result[0]))
                    else:
                        summary = str(result[0])
                else:
                    summary = str(result)
                
                return Response({
                    'summary': summary,
                    'model': get_model_name(),
                    'phone': phone
                })
                
            except RuntimeError as e:
                return Response({'error': f'AI service unavailable: {str(e)}'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            print(f"AI Summary error: {str(e)}")
            return Response({'error': 'Failed to generate AI summary'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)