from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

indian_mobile_validator = RegexValidator(
    regex=r'^[6-9][0-9]{9}$',
    message='Enter a valid Indian mobile number (10 digits starting with 6-9).'
)

class Doctor(models.Model):
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    SPECIALIZATION_CHOICES = [
        ('dermatology', 'Dermatology'),
        ('general', 'General Practice'),
        ('pediatric', 'Pediatric Dermatology'),
        ('surgical', 'Surgical Dermatology'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=50, unique=True)
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES)
    phone_number = models.CharField(max_length=10, validators=[indian_mobile_validator])
    profile_picture = models.ImageField(upload_to='doctor_profiles/', null=True, blank=True)
    years_of_experience = models.IntegerField()
    hospital = models.ForeignKey('hospital.Hospital', on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors')
    approval_status = models.CharField(max_length=10, choices=APPROVAL_STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_doctors'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_hospital = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

class AppointmentSchedule(models.Model):
    APPOINTMENT_TYPE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]
    
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    appointment_type = models.CharField(max_length=10, choices=APPOINTMENT_TYPE_CHOICES)
    is_available = models.BooleanField(default=True)
    duration_minutes = models.IntegerField(default=30, help_text="Duration of each appointment in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['doctor', 'day_of_week', 'start_time', 'appointment_type']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.doctor.user.get_full_name()} - {self.get_day_of_week_display()} ({self.get_appointment_type_display()}) {self.start_time} - {self.end_time}"