from django.contrib import admin
from .models import Hospital

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ['hospital_name', 'registration_number', 'phone_number', 'total_beds', 'created_at']
    list_filter = ['created_at']
    search_fields = ['hospital_name', 'registration_number', 'user__username', 'user__email']

