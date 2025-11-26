from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import time

class State(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name='districts'
    )

    def __str__(self):
        return f"{self.name}, {self.state.name}"

class Clinic(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name='doctors',
        null=True,
        blank=True
    )

    def __str__(self):
        if self.clinic:
            return f"{self.name} ({self.clinic.name})"
        return self.name

class Receptionist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name='receptionists'
    )

    def __str__(self):
        return f"{self.user.username} at {self.clinic.name}"

class Patient(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='patient'
    )
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return self.name

class Token(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('confirmed', 'Confirmed'),
        ('in_consultancy', 'In Consultancy'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    token_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    date = models.DateField(default=timezone.now)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='waiting'
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name='tokens',
        null=True,
        blank=True
    )
    appointment_time = models.TimeField(null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    consultation_start_time = models.DateTimeField(null=True, blank=True)
    arrival_confirmed_at = models.DateTimeField(null=True, blank=True)
    predicted_waiting_time = models.IntegerField(null=True, blank=True, help_text="Predicted waiting time in minutes")

    class Meta:
        unique_together = [
            ('token_number', 'clinic', 'date'),
            ('doctor', 'date', 'appointment_time'),
        ]

    def __str__(self):
        if self.appointment_time:
            return (
                f"Appointment for {self.patient.name} at "
                f"{self.appointment_time.strftime('%I:%M %p')} on {self.date}"
            )
        return f"Token {self.token_number} for {self.patient.name} on {self.date}"

    def save(self, *args, **kwargs):
        if self.doctor and not self.clinic:
            self.clinic = self.doctor.clinic

        if not self.pk and not self.appointment_time and self.token_number is None:
            last_token = Token.objects.filter(
                clinic=self.clinic,
                date=self.date,
                appointment_time__isnull=True
            ).order_by('-token_number').first()

            last_token_num = 0
            if last_token and last_token.token_number and last_token.token_number.isdigit():
                last_token_num = int(last_token.token_number)

            self.token_number = str(last_token_num + 1)

        # STRICT PREVENTION OF AUTOMATIC CONFIRMATION
        # Only allow confirmation through manual user action or receptionist action
        if self.pk and self.status == 'confirmed':
            old_instance = Token.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.status != 'confirmed':
                # Check if this is a manual confirmation (has the special flag)
                if not hasattr(self, '_manual_confirmation_allowed'):
                    # Prevent automatic confirmation - revert to original status
                    self.status = old_instance.status
                    print(f"BLOCKED automatic confirmation for token {self.pk}. Status reverted to {self.status}")

        if self.status == 'completed' and self.completed_at is None:
            self.completed_at = timezone.now()

        super(Token, self).save(*args, **kwargs)

class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField()

    def __str__(self):
        return f"Consultation for {self.patient.name} on {self.date.strftime('%Y-%m-%d')}"

class DoctorSchedule(models.Model):
    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE, related_name='schedule')
    start_time = models.TimeField(default='09:00')
    end_time = models.TimeField(default='17:00')
    slot_duration_minutes = models.IntegerField(default=15)
    max_slots_per_day = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Schedule for Dr. {self.doctor.name}"



class PrescriptionItem(models.Model):
    TIMING_CHOICES = [
        ('M', 'Morning'),
        ('A', 'Afternoon'), 
        ('N', 'Night'),
        ('frequency', 'Times Per Day'),
        ('custom', 'Custom Times')
    ]
    
    FOOD_TIMING_CHOICES = [
        ('before', 'Before Food'),
        ('after', 'After Food'),
        ('with', 'With Food')
    ]
    
    consultation = models.ForeignKey(
        Consultation,
        related_name='prescription_items',
        on_delete=models.CASCADE
    )
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    duration_days = models.IntegerField()
    
    # Timing selection - defaults to M,A,N
    timing_type = models.CharField(max_length=10, choices=TIMING_CHOICES, default='M')
    
    # Frequency per day (for timing_type='frequency')
    frequency_per_day = models.IntegerField(default=1, help_text="Number of times per day")
    
    # Standard timing flags
    timing_morning = models.BooleanField(default=True)
    timing_afternoon = models.BooleanField(default=False)
    timing_evening = models.BooleanField(default=False)
    timing_night = models.BooleanField(default=False)
    
    # Dynamic timing fields for frequency-based prescriptions
    timing_1_time = models.TimeField(null=True, blank=True)
    timing_2_time = models.TimeField(null=True, blank=True)
    timing_3_time = models.TimeField(null=True, blank=True)
    timing_4_time = models.TimeField(null=True, blank=True)
    timing_5_time = models.TimeField(null=True, blank=True)
    timing_6_time = models.TimeField(null=True, blank=True)
    timing_7_time = models.TimeField(null=True, blank=True)
    timing_8_time = models.TimeField(null=True, blank=True)
    
    timing_1_food = models.CharField(max_length=10, choices=FOOD_TIMING_CHOICES, blank=True)
    timing_2_food = models.CharField(max_length=10, choices=FOOD_TIMING_CHOICES, blank=True)
    timing_3_food = models.CharField(max_length=10, choices=FOOD_TIMING_CHOICES, blank=True)
    timing_4_food = models.CharField(max_length=10, choices=FOOD_TIMING_CHOICES, blank=True)
    timing_5_food = models.CharField(max_length=10, choices=FOOD_TIMING_CHOICES, blank=True)
    timing_6_food = models.CharField(max_length=10, choices=FOOD_TIMING_CHOICES, blank=True)
    timing_7_food = models.CharField(max_length=10, choices=FOOD_TIMING_CHOICES, blank=True)
    timing_8_food = models.CharField(max_length=10, choices=FOOD_TIMING_CHOICES, blank=True)
    
    # Custom timing fields (only used when timing_type='custom')
    morning_time = models.TimeField(null=True, blank=True, help_text="Custom morning time")
    afternoon_time = models.TimeField(null=True, blank=True, help_text="Custom afternoon time")
    evening_time = models.TimeField(null=True, blank=True, help_text="Custom evening time")
    night_time = models.TimeField(null=True, blank=True, help_text="Custom night time")
    
    # Food timing for each dose
    morning_food = models.CharField(max_length=10, choices=FOOD_TIMING_CHOICES, default='after')
    afternoon_food = models.CharField(max_length=10, choices=FOOD_TIMING_CHOICES, default='after')
    evening_food = models.CharField(max_length=10, choices=FOOD_TIMING_CHOICES, default='after')
    night_food = models.CharField(max_length=10, choices=FOOD_TIMING_CHOICES, default='after')
    
    # Special instructions
    special_instructions = models.TextField(blank=True, help_text="Additional instructions")

    def get_natural_description(self):
        """Generate natural language description"""
        if self.timing_type == 'frequency':
            times_list = []
            for i in range(1, self.frequency_per_day + 1):
                time_field = getattr(self, f'timing_{i}_time', None)
                food_field = getattr(self, f'timing_{i}_food', None)
                
                time_info = f" at {time_field.strftime('%I:%M %p')}" if time_field else ""
                food_info = f" {food_field} food" if food_field else ""
                times_list.append(f"dose {i}{time_info}{food_info}")
            
            timing_str = ", ".join(times_list) if times_list else f"{self.frequency_per_day} times per day"
            description = f"{self.medicine_name} {self.dosage} - {timing_str} for {self.duration_days} days"
        else:
            times = []
            
            if self.timing_morning:
                if self.timing_type == 'custom' and self.morning_time:
                    time_info = f" at {self.morning_time.strftime('%I:%M %p')}"
                else:
                    time_info = ""
                food_info = f" {self.morning_food} food" if self.morning_food else ""
                times.append(f"1 morning{time_info}{food_info}")
                
            if self.timing_afternoon:
                if self.timing_type == 'custom' and self.afternoon_time:
                    time_info = f" at {self.afternoon_time.strftime('%I:%M %p')}"
                else:
                    time_info = ""
                food_info = f" {self.afternoon_food} food" if self.afternoon_food else ""
                times.append(f"1 afternoon{time_info}{food_info}")
                
            if self.timing_evening:
                if self.timing_type == 'custom' and self.evening_time:
                    time_info = f" at {self.evening_time.strftime('%I:%M %p')}"
                else:
                    time_info = ""
                food_info = f" {self.evening_food} food" if self.evening_food else ""
                times.append(f"1 evening{time_info}{food_info}")
                
            if self.timing_night:
                if self.timing_type == 'custom' and self.night_time:
                    time_info = f" at {self.night_time.strftime('%I:%M %p')}"
                else:
                    time_info = ""
                food_info = f" {self.night_food} food" if self.night_food else ""
                times.append(f"1 night{time_info}{food_info}")
            
            timing_str = " and ".join(times) if times else "as needed"
            description = f"{self.medicine_name} {self.dosage} - {timing_str} for {self.duration_days} days"
        
        if self.special_instructions:
            description += f". {self.special_instructions}"
        
        return description

    def __str__(self):
        return f"{self.medicine_name} for Consultation {self.consultation.id}"

class PrescriptionReminder(models.Model):
    prescription = models.ForeignKey(
        PrescriptionItem,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    reminder_time = models.TimeField()
    sent_date = models.DateField()
    dose_info = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['prescription', 'reminder_time', 'sent_date']
    
    def __str__(self):
        return f"Reminder for {self.prescription.medicine_name} at {self.reminder_time}"