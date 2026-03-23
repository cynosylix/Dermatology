from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from datetime import date


class PendingPatientRegistration(models.Model):
    """Stores registration data until email OTP is verified."""
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    otp_expires_at = models.DateTimeField()
    username = models.CharField(max_length=150)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    password_hash = models.CharField(max_length=128)  # hashed password
    age = models.IntegerField()
    gender = models.CharField(max_length=1)
    phone_number = models.CharField(max_length=15, blank=True, default='')
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Pending: {self.email}"


class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(default=0)  # Default for existing records, form validation ensures new ones have proper values
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='O')  # Default for existing records
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey('doctor.Doctor', on_delete=models.CASCADE, related_name='appointments')
    schedule = models.ForeignKey('doctor.AppointmentSchedule', on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    appointment_type = models.CharField(max_length=10, choices=[('online', 'Online'), ('offline', 'Offline')])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True, help_text="Additional notes or symptoms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        unique_together = ['doctor', 'appointment_date', 'appointment_time']
    
    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.doctor.user.get_full_name()} on {self.appointment_date} at {self.appointment_time}"
    
    def is_past(self):
        from django.utils import timezone
        from datetime import datetime
        appointment_datetime = datetime.combine(self.appointment_date, self.appointment_time)
        return timezone.now() > timezone.make_aware(appointment_datetime)


class AppointmentChatMessage(models.Model):
    """Chat messages for online appointments"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='appointment_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField(blank=True)
    image = models.ImageField(upload_to='chat_uploads/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'patient_appointmentchatmessage'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['appointment', 'created_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} in appointment {self.appointment.id}"


class ChatMessage(models.Model):
    """Chat messages for AI chatbot"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()
    response = models.TextField()
    image = models.ImageField(upload_to='chatbot_uploads/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Chat from {self.patient.user.username} at {self.created_at}"


class Prescription(models.Model):
    """Prescription given by doctor for a specific appointment"""
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='prescription')
    doctor = models.ForeignKey('doctor.Doctor', on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    diagnosis = models.TextField(help_text="Diagnosis / clinical notes")
    medications = models.TextField(help_text="Medicines with dosage and duration")
    advice = models.TextField(blank=True, null=True, help_text="Lifestyle advice / follow-up instructions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prescription for {self.patient.user.get_full_name()} by Dr. {self.doctor.user.get_full_name()}"
