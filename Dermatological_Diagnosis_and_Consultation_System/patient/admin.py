from django.contrib import admin
from .models import Patient, Appointment, ChatMessage, Prescription, PendingPatientRegistration

@admin.register(PendingPatientRegistration)
class PendingPatientRegistrationAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'otp_expires_at', 'created_at']
    list_filter = ['created_at']
    search_fields = ['email', 'username']
    readonly_fields = ['password_hash']

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'gender', 'phone_number', 'date_of_birth', 'created_at']
    list_filter = ['gender', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'appointment_type', 'status', 'created_at']
    list_filter = ['status', 'appointment_type', 'appointment_date', 'created_at']
    search_fields = ['patient__user__username', 'patient__user__email', 'doctor__user__username', 'doctor__user__email']
    ordering = ['-appointment_date', '-appointment_time']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('patient', 'message_preview', 'response_preview', 'has_image', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('patient__user__username', 'message', 'response')
    readonly_fields = ('created_at',)
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'
    
    def response_preview(self, obj):
        return obj.response[:50] + '...' if len(obj.response) > 50 else obj.response
    response_preview.short_description = 'Response'
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Has Image'

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'appointment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['patient__user__username', 'doctor__user__username']