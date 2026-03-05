from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from .forms import HospitalRegistrationForm, HospitalLoginForm, HospitalCreateDoctorForm
from .models import Hospital
from doctor.models import Doctor
from patient.models import Appointment

def hospital_register(request):
    if request.user.is_authenticated:
        return redirect('hospital_dashboard')
    
    if request.method == 'POST':
        form = HospitalRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Save the user
                user = form.save()
                
                # Create Hospital profile
                hospital = Hospital.objects.create(
                    user=user,
                    hospital_name=form.cleaned_data['hospital_name'],
                    registration_number=form.cleaned_data['registration_number'],
                    address=form.cleaned_data['address'],
                    phone_number=form.cleaned_data['phone_number'],
                    email=form.cleaned_data['hospital_email'],
                    total_beds=form.cleaned_data['total_beds']
                )
                # Verify hospital was created
                if hospital.pk:
                    messages.success(request, 'Registration successful! Please login.')
                    return redirect('hospital_login')
                else:
                    messages.error(request, 'Failed to create hospital profile. Please try again.')
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {str(e)}')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = HospitalRegistrationForm()
    return render(request, 'hospital/register.html', {'form': form})

def hospital_login_view(request):
    if request.user.is_authenticated:
        return redirect('hospital_dashboard')
    
    if request.method == 'POST':
        form = HospitalLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Check if user is a hospital
                try:
                    hospital = Hospital.objects.get(user=user)
                    login(request, user)
                    messages.success(request, f'Welcome back, {hospital.hospital_name}!')
                    return redirect('hospital_dashboard')
                except Hospital.DoesNotExist:
                    messages.error(request, 'This account is not registered as a hospital.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = HospitalLoginForm()
    return render(request, 'hospital/login.html', {'form': form})

@never_cache
@login_required
def hospital_dashboard(request):
    try:
        hospital = Hospital.objects.get(user=request.user)
    except Hospital.DoesNotExist:
        messages.error(request, 'Hospital profile not found.')
        return redirect('hospital_logout')
    response = render(request, 'hospital/dashboard.html', {'hospital': hospital})
    # Add cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def hospital_profile(request):
    """Display hospital profile page with information"""
    try:
        hospital = Hospital.objects.get(user=request.user)
    except Hospital.DoesNotExist:
        messages.error(request, 'Hospital profile not found.')
        return redirect('hospital_logout')
    response = render(request, 'hospital/profile.html', {'hospital': hospital})
    # Add cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def hospital_doctors(request):
    """Display list of doctors under this hospital"""
    try:
        hospital = Hospital.objects.get(user=request.user)
    except Hospital.DoesNotExist:
        messages.error(request, 'Hospital profile not found.')
        return redirect('hospital_logout')
    
    doctors = Doctor.objects.filter(hospital=hospital).order_by('-created_at')
    response = render(request, 'hospital/doctors.html', {
        'hospital': hospital,
        'doctors': doctors
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def hospital_add_doctor(request):
    """Allow hospital to create a new doctor"""
    try:
        hospital = Hospital.objects.get(user=request.user)
    except Hospital.DoesNotExist:
        messages.error(request, 'Hospital profile not found.')
        return redirect('hospital_logout')
    
    if request.method == 'POST':
        form = HospitalCreateDoctorForm(request.POST)
        if form.is_valid():
            try:
                # Save the user
                user = form.save()
                
                # Create Doctor profile linked to this hospital
                doctor = Doctor.objects.create(
                    user=user,
                    license_number=form.cleaned_data['license_number'],
                    specialization=form.cleaned_data['specialization'],
                    phone_number=form.cleaned_data['phone_number'],
                    years_of_experience=form.cleaned_data['years_of_experience'],
                    hospital=hospital,
                    created_by_hospital=True
                )
                
                if doctor.pk:
                    messages.success(request, f'Doctor {user.get_full_name()} has been successfully added to your hospital!')
                    return redirect('hospital_doctors')
                else:
                    messages.error(request, 'Failed to create doctor profile. Please try again.')
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = HospitalCreateDoctorForm()
    
    response = render(request, 'hospital/add_doctor.html', {
        'hospital': hospital,
        'form': form
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def hospital_delete_doctor(request, doctor_id):
    """Allow hospital to remove a doctor"""
    try:
        hospital = Hospital.objects.get(user=request.user)
    except Hospital.DoesNotExist:
        messages.error(request, 'Hospital profile not found.')
        return redirect('hospital_logout')
    
    doctor = get_object_or_404(Doctor, id=doctor_id, hospital=hospital)
    
    if request.method == 'POST':
        doctor_name = doctor.user.get_full_name()
        doctor.user.delete()  # This will also delete the doctor due to CASCADE
        messages.success(request, f'Doctor {doctor_name} has been removed from your hospital.')
        return redirect('hospital_doctors')
    
    response = render(request, 'hospital/delete_doctor.html', {
        'hospital': hospital,
        'doctor': doctor
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def hospital_doctor_appointments(request, doctor_id):
    """Allow hospital to view a specific doctor's appointments (activities)"""
    try:
        hospital = Hospital.objects.get(user=request.user)
    except Hospital.DoesNotExist:
        messages.error(request, 'Hospital profile not found.')
        return redirect('hospital_logout')

    # Ensure the doctor belongs to this hospital
    doctor = get_object_or_404(Doctor, id=doctor_id, hospital=hospital)

    appointments = Appointment.objects.filter(doctor=doctor).order_by('-appointment_date', '-appointment_time')

    status_filter = request.GET.get('status', '')
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    response = render(request, 'hospital/doctor_appointments.html', {
        'hospital': hospital,
        'doctor': doctor,
        'appointments': appointments,
        'status_filter': status_filter,
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def hospital_logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('hospital_login')

