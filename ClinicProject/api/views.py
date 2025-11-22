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


User = get_user_model()

# --- Helper Functions ---
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
    """Checks today and future dates for the first available slot."""
    try:
        doctor = Doctor.objects.get(id=doctor_id)
    except Doctor.DoesNotExist:
        return None, None # Added check

    # Check today first, starting from the current time
    today = timezone.now().date()
    current_date = today

    # Check up to 7 days in the future (arbitrary limit for IVR convenience)
    for i in range(7):
        date_str = current_date.strftime('%Y-%m-%d')
        available_slots = _get_available_slots_for_doctor(doctor_id, date_str)

        if available_slots:
            # If today, filter out past slots
            if current_date == today:
                now_time = timezone.now().time()
                # Filter slots that are >= current time
                current_time_slots = [
                    slot for slot in available_slots
                    if datetime.strptime(slot, '%H:%M').time() >= now_time
                ]
                if current_time_slots:
                    return current_date, current_time_slots[0]
            else:
                # If future date, return the very first slot
                return current_date, available_slots[0]

        current_date += timedelta(days=1)

    return None, None # No slots found in the next 7 days

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
    patient_name = f"IVR Patient {caller_phone_number[-4:]}"
    patient_query = Patient.objects.filter(phone_number=caller_phone_number)
    patient = patient_query.first()
    
    # Find or create the patient
    if not patient:
        patient, _ = Patient.objects.get_or_create(phone_number=caller_phone_number, defaults={'name': patient_name, 'age': 0})

    # --- NEW: Check for User account and create if missing ---
    if patient.user is None:
        try:
            # Check if a user with this phone number already exists (e.g., from an old, unlinked account)
            existing_user = User.objects.filter(username=caller_phone_number).first()
            if existing_user:
                # Link this existing user to the patient
                patient.user = existing_user
                patient.save()
            else:
                # No user exists, create one
                # --- THIS IS THE FIXED LINE ---
                temp_password = get_random_string(length=8)
                # --- END OF FIX ---
                new_user = User.objects.create_user(
                    username=caller_phone_number, 
                    password=temp_password,
                    is_staff=False,
                    is_superuser=False
                )
                patient.user = new_user
                patient.save()
                
                # Send the "Welcome" SMS with the temporary password
                welcome_message = f"Welcome to MedQ! A web account has been created for you. Login using:\nUsername: {caller_phone_number}\nTemp Password: {temp_password}"
                try:
                    send_sms_notification(caller_phone_number, welcome_message)
                except Exception as e:
                    print(f"IVR: Failed to send WELCOME SMS to {caller_phone_number}: {e}")
        
        except Exception as e:
            print(f"IVR: Failed to create/link user for patient {patient.id}: {e}")
            # Continue with booking, but user won't be able to log in
    # --- END NEW USER CREATION ---


    # Check for existing active token on ANY day
    if Token.objects.filter(patient=patient).exclude(status__in=['completed', 'cancelled', 'skipped']).exists():
        print(f"IVR Booking failed: Patient {patient.id} already has an active token.")
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
            # Final check if slot is still free right before creating
            if Token.objects.filter(doctor=doctor, date=appointment_date, appointment_time=appointment_time).exclude(status__in=['cancelled', 'skipped']).exists():
                print(f"IVR Booking failed: Slot {appointment_date} {appointment_time_str} for Dr. {doctor.id} was taken.")
                return None # Indicate failure: slot taken

            new_appointment = Token.objects.create(
                patient=patient, doctor=doctor, clinic=doctor.clinic, date=appointment_date,
                appointment_time=appointment_time, token_number=formatted_token_number, status='waiting'
            )
            return new_appointment # Indicate success

    except IntegrityError:
        print(f"IVR Booking failed: Database integrity error for slot {appointment_date} {appointment_time_str} Dr. {doctor.id}.")
        return None # Indicate failure: database conflict
    except Exception as e:
        print(f"IVR Booking failed: Unexpected error during token creation - {e}")
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
            token = Token.objects.get(patient=user.patient, date=timezone.now().date(), status='waiting')

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
            token = Token.objects.filter(
                patient=user.patient,
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

            token = Token.objects.filter(
                patient=user.patient,
                date=today
            ).exclude(status__in=['completed', 'cancelled']).order_by('appointment_time', 'created_at').first()

            if not token:
                token = Token.objects.filter(
                    patient=user.patient,
                    date__gt=today,
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
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_active:
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
                user_data = {'token': token.key, 'user': profile_data}
                return Response(user_data, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid Credentials.'}, status=status.HTTP_400_BAD_REQUEST)

class StaffLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None and user.is_staff:
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

            response_data = {'token': token.key, 'user': {**profile_data, 'role': role, 'clinic': clinic_data}}
            return Response(response_data, status=status.HTTP_200_OK)
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
        if patient_id: return Consultation.objects.filter(patient__id=patient_id).order_by('-date')
        return Consultation.objects.none()

# ====================================================================
# --- NEW FEATURE: Patient History Search (Emergency/Doctor) ---
# ====================================================================
class PatientHistorySearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Restrict to Doctors/Staff only
        if not (hasattr(request.user, 'doctor') or hasattr(request.user, 'receptionist') or request.user.is_staff):
            return Response({'error': 'Permission denied. Staff access required.'}, status=status.HTTP_403_FORBIDDEN)

        phone_number = request.query_params.get('phone')
        if not phone_number:
            return Response({'error': 'Phone number parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find the patient by phone number
            patient = Patient.objects.get(phone_number=phone_number)
            
            # --- CHANGED HERE: Fetch Consultations instead of Tokens ---
            consultations = Consultation.objects.filter(patient=patient).order_by('-date')
            
            # --- CHANGED HERE: Use ConsultationSerializer ---
            serializer = ConsultationSerializer(consultations, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found with this phone number.'}, status=status.HTTP_404_NOT_FOUND)


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
        response = VoiceResponse()
        states = State.objects.all()
        if not states:
            response.say("Sorry, no clinics are configured. Goodbye.")
            response.hangup()
            return HttpResponse(str(response), content_type='text/xml')
        
        gather = response.gather(num_digits=1, action='/api/ivr/handle-state/')
        say_message = "Welcome to ClinicFlow AI. Please select a state. "
        for i, state in enumerate(states):
            say_message += f"For {state.name}, press {i + 1}. "
        gather.say(say_message)
        response.redirect('/api/ivr/welcome/')
        return HttpResponse(str(response), content_type='text/xml')
    except Exception as e:
        print(f"IVR Welcome Error: {e}")
        response = VoiceResponse()
        response.say("Sorry, there was a system error. Please try again later.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')

@csrf_exempt
def ivr_handle_state(request):
    choice = request.POST.get('Digits'); response = VoiceResponse()
    try:
        state = State.objects.all()[int(choice) - 1]; districts = District.objects.filter(state=state)
        if not districts: response.say(f"Sorry, no districts found for {state.name}. Please try again."); response.redirect('/api/ivr/welcome/'); return HttpResponse(str(response), content_type='text/xml')
        num_digits = len(str(districts.count())) if districts.count() > 0 else 1; gather = response.gather(num_digits=num_digits, action=f'/api/ivr/handle-district/{state.id}/')
        say_message = f"You selected {state.name}. Please select a district. ";
        for i, district in enumerate(districts): say_message += f"For {district.name}, press {i + 1}. "
        gather.say(say_message); response.redirect('/api/ivr/handle-state/');
    except (ValueError, IndexError, TypeError): response.say("Invalid choice."); response.redirect('/api/ivr/welcome/')
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
    choice = request.POST.get('Digits'); response = VoiceResponse()
    try:
        district = District.objects.get(id=district_id); clinic = Clinic.objects.filter(district=district)[int(choice) - 1]
        gather = response.gather(num_digits=1, action=f'/api/ivr/handle-booking-type/{clinic.id}/')
        gather.say(f"You selected {clinic.name}. For the next available doctor, press 1. To find a doctor by specialization, press 2.")
        response.redirect(f'/api/ivr/handle-clinic/{district.id}/');
    except (ValueError, IndexError, TypeError, District.DoesNotExist, Clinic.DoesNotExist): response.say("Invalid choice or error."); response.redirect('/api/ivr/welcome/')
    return HttpResponse(str(response), content_type='text/xml')

# --- MODIFIED: Asks for confirmation ---
@csrf_exempt
def ivr_handle_booking_type(request, clinic_id):
    choice = request.POST.get('Digits'); response = VoiceResponse(); caller_phone_number = request.POST.get('From', None)
    if not caller_phone_number: response.say("We could not identify your phone number. Cannot proceed. Goodbye."); response.hangup(); return HttpResponse(str(response), content_type='text/xml')
    try:
        clinic = Clinic.objects.get(id=clinic_id)
        if choice == '1': # Book with next available
            doctors = Doctor.objects.filter(clinic=clinic)
            if not doctors.exists(): response.say(f"Sorry, no doctors found for {clinic.name}."); response.hangup(); return HttpResponse(str(response), content_type='text/xml')
            best_doctor = None; earliest_appointment_date = None; earliest_slot_str = None
            for doctor in doctors: # Find absolute earliest slot
                app_date, slot_str = _find_next_available_slot_for_doctor(doctor.id)
                if app_date and slot_str:
                    slot_datetime = datetime.combine(app_date, datetime.strptime(slot_str, '%H:%M').time()); current_earliest_datetime = datetime.combine(earliest_appointment_date, datetime.strptime(earliest_slot_str, '%H:%M').time()) if earliest_appointment_date else None
                    if current_earliest_datetime is None or slot_datetime < current_earliest_datetime: earliest_appointment_date = app_date; earliest_slot_str = slot_str; best_doctor = doctor
            if best_doctor:
                # --- ASK FOR CONFIRMATION ---
                date_spoken = "today" if earliest_appointment_date == timezone.now().date() else earliest_appointment_date.strftime("%B %d")
                time_spoken = datetime.strptime(earliest_slot_str, '%H:%M').strftime('%I:%M %p')
                action_url = f'/api/ivr/confirm-booking/?doctor_id={best_doctor.id}&date={earliest_appointment_date.strftime("%Y-%m-%d")}&time={earliest_slot_str}&phone={caller_phone_number}'
                gather = response.gather(num_digits=1, action=action_url)
                gather.say(f"The next available slot is with Doctor {best_doctor.name} at {time_spoken} on {date_spoken}. Press 1 to confirm, press 2 to cancel.")
                response.redirect(f'/api/ivr/handle-booking-type/{clinic_id}/') # Redirect if no input
                # --- END ASK FOR CONFIRMATION ---
            else:
                response.say(f"Sorry, no doctors have available slots in the coming days at {clinic.name}. Goodbye."); response.hangup()
        elif choice == '2': # Find by specialization
            specializations = list(Doctor.objects.filter(clinic=clinic).values_list('specialization', flat=True).distinct())
            if not specializations: response.say(f"Sorry, no specializations found for {clinic.name}."); response.redirect(f'/api/ivr/handle-clinic/{clinic.district_id}/'); return HttpResponse(str(response), content_type='text/xml')
            num_digits = len(str(len(specializations))) if specializations else 1; gather = response.gather(num_digits=num_digits, action=f'/api/ivr/handle-specialization/{clinic.id}/')
            say_message = "Please select a specialization. ";
            for i, spec in enumerate(specializations): say_message += f"For {spec}, press {i + 1}. "
            gather.say(say_message); response.redirect(f'/api/ivr/handle-booking-type/{clinic.id}/');
        else: response.say("Invalid choice."); response.redirect(f'/api/ivr/handle-booking-type/{clinic_id}/')
    except Clinic.DoesNotExist: response.say("Clinic not found."); response.redirect('/api/ivr/welcome/')
    except Exception as e: print(f"Error in ivr_handle_booking_type: {e}"); response.say("An application error occurred. Goodbye."); response.hangup()
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
    response = VoiceResponse()
    # Get details passed in the action URL's query parameters
    # Prefer GET query params (action URL) but fall back to POST form fields (Twilio sometimes posts From)
    doctor_id = request.GET.get('doctor_id') or request.POST.get('doctor_id')
    date_str = request.GET.get('date') or request.POST.get('date')
    time_str = request.GET.get('time') or request.POST.get('time')
    caller_phone_number = (request.GET.get('phone') or request.POST.get('phone') or request.POST.get('From'))

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
        print(f"IVR Confirm: After fallback parse. PATH={request.get_full_path()} QUERY_STRING={request.META.get('QUERY_STRING')} GET={dict(request.GET)} POST={dict(request.POST)} ParsedFallback_doctor={doctor_id} date={date_str} time={time_str} phone={caller_phone_number}")
        response.say("Sorry, booking information is missing. Please start over.")
        response.redirect('/api/ivr/welcome/')
        return HttpResponse(str(response), content_type='text/xml')

    try:
        if choice == '1': # Confirm booking
            doctor = Doctor.objects.get(id=int(doctor_id))
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Attempt to create the token using the helper
            # This helper now ALSO creates a User and sends a password SMS if it's a new patient
            new_token = _create_ivr_token(doctor, appointment_date, time_str, caller_phone_number)

            if new_token:
                # Booking succeeded
                date_spoken = "today" if new_token.date == timezone.now().date() else new_token.date.strftime("%B %d")
                time_spoken = new_token.appointment_time.strftime('%I:%M %p')
                token_num_spoken = f"Your token number is {new_token.token_number}." if new_token.token_number else ""

                # Send the *appointment confirmation* SMS
                # The "welcome" SMS is sent from the helper
                message = (f"Your appointment with Dr. {doctor.name} is confirmed for "
                           f"{time_spoken} on {date_spoken}. {token_num_spoken}")
                try: send_sms_notification(caller_phone_number, message)
                except Exception as e: print(f"IVR Confirm: Failed to send APPOINTMENT SMS to {caller_phone_number}: {e}")

                response.say(f"Booking confirmed for {time_spoken} on {date_spoken}. Confirmation SMS has been sent. Goodbye.")
                response.hangup()
            else:
                # Booking failed (slot taken, user already booked, db error etc.)
                response.say("Sorry, we could not book this slot. It might have been taken or you may already have an active appointment. Please try again.")
                response.hangup()

        elif choice == '2': # Cancel booking attempt
            response.say("Booking cancelled. Goodbye.")
            response.hangup()
        else: # Invalid digit
            response.say("Invalid choice. Hanging up.")
            response.hangup() # End call on invalid input to avoid loops

    except Doctor.DoesNotExist:
        response.say("Doctor information error. Please start over.")
        response.redirect('/api/ivr/welcome/')
    except ValueError: # Handle potential errors converting date/time/doctor_id
        response.say("Booking information error. Please start over.")
        response.redirect('/api/ivr/welcome/')
    except Exception as e:
        print(f"Error in ivr_confirm_booking: {e}")
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
            
            # Simple extractive summary
            lines = patient_history.split('\n')
            medical_info = []
            
            for line in lines:
                line = line.strip()
                if line and any(word in line.lower() for word in [
                    'patient', 'doctor', 'notes', 'prescription', 'symptoms', 
                    'diagnosis', 'treatment', 'medication', 'complaint', 'pain',
                    'fever', 'blood', 'pressure', 'heart', 'breathing'
                ]):
                    medical_info.append(line)
            
            if medical_info:
                summary = "MEDICAL SUMMARY:\n\n" + "\n".join(medical_info[:5])
            else:
                summary = "Patient medical history available. Key information extracted from consultation records."
            
            return Response({
                'summary': summary,
                'model': 'extractive_summarizer',
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