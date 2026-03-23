from django.contrib import admin
from .models import Doctor, AppointmentSchedule

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'license_number', 'specialization', 'years_of_experience', 'created_at']
    list_filter = ['specialization', 'created_at']
    search_fields = ['user__username', 'user__email', 'license_number']

@admin.register(AppointmentSchedule)
class AppointmentScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'day_of_week', 'start_time', 'end_time', 'appointment_type', 'is_available', 'duration_minutes']
    list_filter = ['day_of_week', 'appointment_type', 'is_available', 'created_at']
    search_fields = ['doctor__user__username', 'doctor__user__email']
    ordering = ['doctor', 'day_of_week', 'start_time']