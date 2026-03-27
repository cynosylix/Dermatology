from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.db.models import Q
from .forms import (
    DoctorRegistrationForm,
    DoctorLoginForm,
    DoctorProfilePictureForm,
    AppointmentScheduleForm,
    PrescriptionForm,
)
from .models import Doctor, AppointmentSchedule
from patient.models import Appointment, ChatMessage, Prescription
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

def doctor_register(request):
    if request.user.is_authenticated:
        return redirect('doctor_dashboard')
    
    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Save the user
                user = form.save()
                
                # Create Doctor profile
                doctor = Doctor.objects.create(
                    user=user,
                    license_number=form.cleaned_data['license_number'],
                    specialization=form.cleaned_data['specialization'],
                    phone_number=form.cleaned_data['phone_number'],
                    profile_picture=form.cleaned_data['profile_picture'],
                    years_of_experience=form.cleaned_data['years_of_experience'],
                    approval_status='pending'
                )
                # Verify doctor was created
                if doctor.pk:
                    messages.success(
                        request,
                        'Registration submitted. Your account will be active after admin approval.'
                    )
                    return redirect('doctor_login')
                else:
                    messages.error(request, 'Failed to create doctor profile. Please try again.')
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {str(e)}')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = DoctorRegistrationForm()
    return render(request, 'doctor/register.html', {'form': form})

def doctor_login_view(request):
    if request.user.is_authenticated:
        return redirect('doctor_dashboard')
    
    if request.method == 'POST':
        form = DoctorLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Check if user is a doctor
                try:
                    doctor = Doctor.objects.get(user=user)
                    if doctor.approval_status != 'approved':
                        if doctor.approval_status == 'rejected':
                            reason = f" Reason: {doctor.rejection_reason}" if doctor.rejection_reason else ''
                            messages.error(
                                request,
                                f'Your doctor account has not been approved by the administrator.{reason}'
                            )
                        else:
                            messages.warning(
                                request,
                                'Your registration is under administrative review. You can sign in once approval is completed.'
                            )
                        return render(request, 'doctor/login.html', {'form': form})
                    login(request, user)
                    messages.success(request, f'Welcome back, Dr. {user.first_name}!')
                    return redirect('doctor_dashboard')
                except Doctor.DoesNotExist:
                    messages.error(request, 'This account is not registered as a doctor.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = DoctorLoginForm()
    return render(request, 'doctor/login.html', {'form': form})

@never_cache
@login_required
def doctor_dashboard(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('doctor_logout')
    response = render(request, 'doctor/dashboard.html', {'doctor': doctor})
    # Add cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def doctor_profile(request):
    """Display doctor profile page with personal information"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('doctor_logout')

    if request.method == 'POST':
        if 'profile_picture' not in request.FILES:
            messages.error(request, 'Please select an image before uploading.')
            return redirect('doctor_profile')
        picture_form = DoctorProfilePictureForm(request.POST, request.FILES, instance=doctor)
        if picture_form.is_valid():
            picture_form.save()
            messages.success(request, 'Profile picture updated successfully.')
            return redirect('doctor_profile')
        messages.error(request, 'Please upload a valid image file.')
    else:
        picture_form = DoctorProfilePictureForm(instance=doctor)

    response = render(request, 'doctor/profile.html', {'doctor': doctor, 'picture_form': picture_form})
    # Add cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def doctor_schedules(request):
    """Display and manage doctor's appointment schedules"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('doctor_logout')
    
    schedules = AppointmentSchedule.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time')
    
    # Group schedules by day
    schedules_by_day = {}
    for schedule in schedules:
        day = schedule.get_day_of_week_display()
        if day not in schedules_by_day:
            schedules_by_day[day] = {'online': [], 'offline': []}
        schedules_by_day[day][schedule.appointment_type].append(schedule)
    
    response = render(request, 'doctor/schedules.html', {
        'doctor': doctor,
        'schedules': schedules,
        'schedules_by_day': schedules_by_day
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def doctor_add_schedule(request):
    """Add new appointment schedule"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('doctor_logout')
    
    if request.method == 'POST':
        form = AppointmentScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.doctor = doctor
            try:
                schedule.save()
                messages.success(request, 'Appointment schedule added successfully!')
                return redirect('doctor_schedules')
            except Exception as e:
                messages.error(request, f'Error saving schedule: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = AppointmentScheduleForm()
    
    response = render(request, 'doctor/add_schedule.html', {
        'doctor': doctor,
        'form': form
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def doctor_edit_schedule(request, schedule_id):
    """Edit existing appointment schedule"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('doctor_logout')
    
    schedule = get_object_or_404(AppointmentSchedule, id=schedule_id, doctor=doctor)
    
    if request.method == 'POST':
        form = AppointmentScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Appointment schedule updated successfully!')
                return redirect('doctor_schedules')
            except Exception as e:
                messages.error(request, f'Error updating schedule: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = AppointmentScheduleForm(instance=schedule)
    
    response = render(request, 'doctor/edit_schedule.html', {
        'doctor': doctor,
        'schedule': schedule,
        'form': form
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def doctor_delete_schedule(request, schedule_id):
    """Delete appointment schedule"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('doctor_logout')
    
    schedule = get_object_or_404(AppointmentSchedule, id=schedule_id, doctor=doctor)
    
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Appointment schedule deleted successfully!')
        return redirect('doctor_schedules')
    
    response = render(request, 'doctor/delete_schedule.html', {
        'doctor': doctor,
        'schedule': schedule
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def doctor_appointments(request):
    """View and manage doctor's appointments"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('doctor_logout')
    
    appointments = Appointment.objects.filter(doctor=doctor).order_by('appointment_date', 'appointment_time')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    # Prefetch prescriptions for efficiency
    from django.db.models import Prefetch
    appointments = appointments.prefetch_related('prescription')
    
    response = render(request, 'doctor/appointments.html', {
        'doctor': doctor,
        'appointments': appointments,
        'status_filter': status_filter
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def confirm_appointment(request, appointment_id):
    """Confirm a pending appointment"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('doctor_logout')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
    
    if request.method == 'POST':
        if appointment.status == 'pending':
            appointment.status = 'confirmed'
            appointment.save()
            messages.success(request, f'Appointment with {appointment.patient.user.get_full_name()} confirmed successfully!')
        else:
            messages.warning(request, 'Only pending appointments can be confirmed.')
        return redirect('doctor_appointments')
    
    response = render(request, 'doctor/confirm_appointment.html', {
        'doctor': doctor,
        'appointment': appointment
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def cancel_appointment_doctor(request, appointment_id):
    """Doctor cancels an appointment"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('doctor_logout')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
        return redirect('doctor_appointments')
    
    response = render(request, 'doctor/cancel_appointment.html', {
        'doctor': doctor,
        'appointment': appointment
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def appointment_chat(request, appointment_id):
    """Chat interface for online appointments (doctor view)"""
    from patient.views import appointment_chat as patient_appointment_chat
    return patient_appointment_chat(request, appointment_id)

@require_http_methods(["POST"])
@login_required
def send_chat_message(request, appointment_id):
    """Send a chat message (AJAX endpoint) - doctor"""
    from patient.views import send_chat_message as patient_send_chat_message
    return patient_send_chat_message(request, appointment_id)

@require_http_methods(["GET"])
@login_required
def get_chat_messages(request, appointment_id):
    """Get chat messages (AJAX endpoint for polling) - doctor"""
    from patient.views import get_chat_messages as patient_get_chat_messages
    return patient_get_chat_messages(request, appointment_id)

@never_cache
@login_required
def create_prescription(request, appointment_id):
    """Create a prescription for a completed appointment"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('doctor_logout')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
    
    # Check if appointment is completed or confirmed
    if appointment.status not in ['completed', 'confirmed']:
        messages.warning(request, 'Prescription can only be created for completed or confirmed appointments.')
        return redirect('doctor_appointments')
    
    # Check if prescription already exists
    if hasattr(appointment, 'prescription'):
        messages.info(request, 'A prescription already exists for this appointment.')
        return redirect('view_prescription', prescription_id=appointment.prescription.id)
    
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.appointment = appointment
            prescription.doctor = doctor
            prescription.patient = appointment.patient
            prescription.save()
            
            # Mark appointment as completed if it was confirmed
            if appointment.status == 'confirmed':
                appointment.status = 'completed'
                appointment.save()
            
            messages.success(request, 'Prescription created successfully!')
            return redirect('view_prescription', prescription_id=prescription.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PrescriptionForm()
    
    response = render(request, 'doctor/create_prescription.html', {
        'doctor': doctor,
        'appointment': appointment,
        'form': form
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def doctor_prescriptions(request):
    """View all prescriptions created by the doctor"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('doctor_logout')
    
    prescriptions = Prescription.objects.filter(doctor=doctor).order_by('-created_at')
    
    response = render(request, 'doctor/prescriptions.html', {
        'doctor': doctor,
        'prescriptions': prescriptions
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def view_prescription(request, prescription_id):
    """View prescription details (accessible by both doctor and patient)"""
    prescription = get_object_or_404(Prescription, id=prescription_id)
    
    # Check authorization
    is_authorized = False
    is_doctor = False
    is_patient = False
    
    try:
        doctor = Doctor.objects.get(user=request.user)
        if prescription.doctor == doctor:
            is_authorized = True
            is_doctor = True
    except Doctor.DoesNotExist:
        pass
    
    if not is_authorized:
        try:
            from patient.models import Patient
            patient = Patient.objects.get(user=request.user)
            if prescription.patient == patient:
                is_authorized = True
                is_patient = True
        except Patient.DoesNotExist:
            pass
    
    if not is_authorized:
        messages.error(request, 'You are not authorized to view this prescription.')
        if request.user.is_authenticated:
            try:
                Doctor.objects.get(user=request.user)
                return redirect('doctor_prescriptions')
            except Doctor.DoesNotExist:
                from patient.models import Patient
                try:
                    Patient.objects.get(user=request.user)
                    return redirect('patient_prescriptions')
                except Patient.DoesNotExist:
                    pass
        return redirect('home')
    
    response = render(request, 'prescription/view.html', {
        'prescription': prescription,
        'is_doctor': is_doctor,
        'is_patient': is_patient
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def doctor_logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('doctor_login')

