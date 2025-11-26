from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Avg, F
from datetime import timedelta
# --- REMOVED: transaction import ---
# from django.db import transaction # No longer needed here
from .models import Doctor, Patient, Token, Consultation, Clinic, Receptionist, PrescriptionItem, DoctorSchedule

User = get_user_model()

# --- Base Serializers ---

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = ['id', 'name', 'address', 'city']

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Doctor
        fields = ['id', 'name', 'specialization', 'user']

class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Patient
        fields = ['id', 'name', 'age', 'user', 'phone_number']

# --- UPDATED: Prescription & Consultation Serializers ---
class PrescriptionItemSerializer(serializers.ModelSerializer):
    natural_description = serializers.CharField(source='get_natural_description', read_only=True)
    
    class Meta:
        model = PrescriptionItem
        fields = [
            'id', 'medicine_name', 'dosage', 'duration_days', 
            'timing_type', 'frequency_per_day',
            'timing_morning', 'timing_afternoon', 'timing_evening', 'timing_night',
            'timing_1_time', 'timing_2_time', 'timing_3_time', 'timing_4_time',
            'timing_5_time', 'timing_6_time', 'timing_7_time', 'timing_8_time',
            'timing_1_food', 'timing_2_food', 'timing_3_food', 'timing_4_food',
            'timing_5_food', 'timing_6_food', 'timing_7_food', 'timing_8_food',
            'morning_time', 'afternoon_time', 'evening_time', 'night_time',
            'morning_food', 'afternoon_food', 'evening_food', 'night_food',
            'special_instructions', 'natural_description'
        ]

class ConsultationCreateSerializer(serializers.ModelSerializer):
    prescription_items = PrescriptionItemSerializer(many=True, required=False)
    
    class Meta:
        model = Consultation
        fields = ['patient', 'notes', 'prescription_items']
    
    def create(self, validated_data):
        prescription_items_data = validated_data.pop('prescription_items', [])
        
        # Get doctor from request user
        doctor = self.context['request'].user.doctor
        consultation = Consultation.objects.create(
            doctor=doctor,
            **validated_data
        )
        
        # Create prescription items
        for prescription_data in prescription_items_data:
            PrescriptionItem.objects.create(
                consultation=consultation,
                **prescription_data
            )
        
        return consultation

class ConsultationSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    prescription_items = PrescriptionItemSerializer(many=True, read_only=True)
    patient = PatientSerializer(read_only=True)

    class Meta:
        model = Consultation
        fields = ['id', 'date', 'notes', 'doctor', 'patient', 'prescription_items']

# --- UPDATED: Token Serializer ---
class TokenSerializer(serializers.ModelSerializer):
    # Nesting these is critical for the Frontend to show Names instead of IDs
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    clinic = ClinicSerializer(read_only=True)
    
    # Keep these ID fields for easier logic access if needed
    doctor_id = serializers.ReadOnlyField(source='doctor.id')
    clinic_id = serializers.ReadOnlyField(source='clinic.id')
    token_number = serializers.CharField(read_only=True)
    
    class Meta:
        model = Token
        fields = ['id', 'token_number', 'patient', 'doctor', 'doctor_id', 'created_at', 'status', 'clinic', 'clinic_id', 'appointment_time']


# --- Special Purpose Serializers ---

# --- REVERTED: PatientRegisterSerializer (Simple, Active User) ---
class PatientRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    name = serializers.CharField(write_only=True, required=True)
    age = serializers.IntegerField(write_only=True, required=True)
    phone_number = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'name', 'age', 'phone_number')
        extra_kwargs = {
            'username': {'required': True},
            # Basic phone validation moved here for simplicity, can be more robust
             'phone_number': {'validators': []}, 
        }

    def validate_phone_number(self, value):
        """ Basic check for format and uniqueness """
        if Patient.objects.filter(phone_number=value, user__is_active=True).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        if not value.startswith('+'):
             raise serializers.ValidationError("Phone number must start with '+' and include country code.")
        return value

    def validate_username(self, value):
        """ Check if username is taken """
        # Disallow reusing any existing username to prevent role/profile clashes
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        # Allow reusing username if user is inactive (optional, adjust if needed)
        # if User.objects.filter(username=value).exists():
        #    raise serializers.ValidationError("This username is already taken.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        attrs.pop('password2')
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            is_staff=False,
            is_superuser=False
        )
        Patient.objects.create(
            user=user,
            name=validated_data['name'],
            age=validated_data['age'],
            phone_number=validated_data['phone_number']
        )
        return user


class ClinicWithDoctorsSerializer(serializers.ModelSerializer):
    doctors = DoctorSerializer(many=True, read_only=True)
    average_wait_time = serializers.SerializerMethodField()
    total_tokens = serializers.SerializerMethodField()

    class Meta:
        model = Clinic
        fields = ['id', 'name', 'address', 'city', 'doctors', 'average_wait_time', 'total_tokens']

    def get_total_tokens(self, obj):
        today = timezone.now().date()
        return Token.objects.filter(clinic=obj, date=today).count()

    def get_average_wait_time(self, obj):
        # Use AI-predicted waiting times if available
        if hasattr(obj, 'avg_waiting_time'):
            return obj.avg_waiting_time
        
        # Fallback to real-time AI predictions
        from .waiting_time_predictor import waiting_time_predictor
        total_predicted_wait = 0
        doctor_count = 0
        
        for doctor in obj.doctors.all():
            try:
                predicted_wait = waiting_time_predictor.predict_waiting_time(doctor.id)
                if predicted_wait:
                    total_predicted_wait += predicted_wait
                    doctor_count += 1
            except Exception:
                pass
        
        return round(total_predicted_wait / doctor_count) if doctor_count > 0 else 15


class DoctorScheduleSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    
    class Meta:
        model = DoctorSchedule
        fields = ['id', 'doctor', 'doctor_name', 'start_time', 'end_time', 'slot_duration_minutes', 'max_slots_per_day', 'is_active']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data

class AnonymizedTokenSerializer(serializers.ModelSerializer):
    token_number = serializers.CharField(read_only=True) 
    class Meta:
        model = Token
        fields = ['id', 'token_number', 'status', 'appointment_time']