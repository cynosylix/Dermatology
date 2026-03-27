from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from doctor.models import Doctor
from hospital.models import Hospital
from patient.models import Patient, Appointment
from .forms import AdminLoginForm


def _is_admin_user(user: User) -> bool:
    return user.is_staff or user.is_superuser


def _send_status_email(recipient_email: str, subject: str, message: str) -> bool:
    """Send status email without blocking admin action on failures."""
    try:
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@clearderm.example.com'),
            [recipient_email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False


def _admin_required(view_func):
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not _is_admin_user(request.user):
            messages.error(request, 'You are not authorized to access admin control panel.')
            return redirect('home')
        return view_func(request, *args, **kwargs)

    return _wrapped


def admin_login_view(request):
    if request.user.is_authenticated:
        if _is_admin_user(request.user):
            return redirect('adminpanel_dashboard')
        # Clear non-admin session so admin login page is clean
        logout(request)
        messages.info(request, 'Please login with an admin account.')

    if request.method == 'POST':
        form = AdminLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user and _is_admin_user(user):
                login(request, user)
                messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
                return redirect('adminpanel_dashboard')
            messages.error(request, 'Valid credentials, but this account has no admin privileges.')
    else:
        form = AdminLoginForm()
    return render(request, 'adminpanel/login.html', {'form': form})


@_admin_required
def admin_dashboard(request):
    context = {
        'pending_doctors_count': Doctor.objects.filter(approval_status='pending').count(),
        'pending_hospitals_count': Hospital.objects.filter(approval_status='pending').count(),
        'rejected_doctors_count': Doctor.objects.filter(approval_status='rejected').count(),
        'rejected_hospitals_count': Hospital.objects.filter(approval_status='rejected').count(),
        'approved_doctors_count': Doctor.objects.filter(approval_status='approved').count(),
        'approved_hospitals_count': Hospital.objects.filter(approval_status='approved').count(),
        'patients_count': Patient.objects.count(),
        'appointments_count': Appointment.objects.count(),
    }
    return render(request, 'adminpanel/dashboard.html', context)


@_admin_required
def manage_doctors(request):
    query = (request.GET.get('q') or '').strip()
    doctors = Doctor.objects.select_related('user', 'hospital').order_by('-created_at')
    if query:
        doctors = doctors.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(license_number__icontains=query)
        )
    return render(request, 'adminpanel/manage_doctors.html', {'doctors': doctors, 'q': query})


@_admin_required
def manage_hospitals(request):
    query = (request.GET.get('q') or '').strip()
    hospitals = Hospital.objects.select_related('user').order_by('-created_at')
    if query:
        hospitals = hospitals.filter(
            Q(hospital_name__icontains=query)
            | Q(registration_number__icontains=query)
            | Q(user__username__icontains=query)
        )
    return render(request, 'adminpanel/manage_hospitals.html', {'hospitals': hospitals, 'q': query})


@_admin_required
def manage_patients(request):
    query = (request.GET.get('q') or '').strip()
    patients = Patient.objects.select_related('user').order_by('-created_at')
    if query:
        patients = patients.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(phone_number__icontains=query)
        )
    return render(request, 'adminpanel/manage_patients.html', {'patients': patients, 'q': query})


@_admin_required
def pending_doctors(request):
    doctors = Doctor.objects.filter(approval_status='pending').select_related('user', 'hospital').order_by('-created_at')
    return render(request, 'adminpanel/pending_doctors.html', {'doctors': doctors})


@_admin_required
def pending_hospitals(request):
    hospitals = Hospital.objects.filter(approval_status='pending').select_related('user').order_by('-created_at')
    return render(request, 'adminpanel/pending_hospitals.html', {'hospitals': hospitals})


@_admin_required
@require_http_methods(["POST"])
def approve_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    doctor.approval_status = 'approved'
    doctor.approved_by = request.user
    doctor.approved_at = timezone.now()
    doctor.rejection_reason = ''
    doctor.save(update_fields=['approval_status', 'approved_by', 'approved_at', 'rejection_reason'])
    doctor_name = doctor.user.get_full_name() or doctor.user.username
    _send_status_email(
        doctor.user.email,
        'ClearDerm: Doctor Account Approval Confirmation',
        (
            f'Dear Dr. {doctor_name},\n\n'
            'We are pleased to inform you that your doctor account has been approved by the ClearDerm administration team.\n'
            'You may now sign in to your account and access your dashboard.\n\n'
            'If you need any assistance, please contact the support team.\n\n'
            'Best regards,\n'
            'ClearDerm Team'
        ),
    )
    messages.success(request, f'Doctor {doctor.user.get_full_name()} approved.')
    return redirect(request.POST.get('next') or 'adminpanel_pending_doctors')


@_admin_required
@require_http_methods(["POST"])
def reject_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    reason = (request.POST.get('rejection_reason') or '').strip()
    doctor.approval_status = 'rejected'
    doctor.approved_by = request.user
    doctor.approved_at = timezone.now()
    doctor.rejection_reason = reason
    doctor.save(update_fields=['approval_status', 'approved_by', 'approved_at', 'rejection_reason'])
    doctor_name = doctor.user.get_full_name() or doctor.user.username
    reason_line = f'\nReason: {reason}\n' if reason else '\n'
    _send_status_email(
        doctor.user.email,
        'ClearDerm: Doctor Account Application Update',
        (
            f'Dear Dr. {doctor_name},\n\n'
            'Thank you for your interest in joining ClearDerm.\n'
            'After review, your doctor account application has not been approved at this time.'
            f'{reason_line}\n'
            'You may update your details and contact support for further guidance.\n\n'
            'Best regards,\n'
            'ClearDerm Team'
        ),
    )
    messages.warning(request, f'Doctor {doctor.user.get_full_name()} disapproved.')
    return redirect(request.POST.get('next') or 'adminpanel_pending_doctors')


@_admin_required
@require_http_methods(["POST"])
def set_doctor_pending(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    doctor.approval_status = 'pending'
    doctor.approved_by = None
    doctor.approved_at = None
    doctor.rejection_reason = ''
    doctor.save(update_fields=['approval_status', 'approved_by', 'approved_at', 'rejection_reason'])
    messages.info(request, f'Doctor {doctor.user.get_full_name()} marked as pending review.')
    return redirect(request.POST.get('next') or 'adminpanel_manage_doctors')


@_admin_required
@require_http_methods(["POST"])
def approve_hospital(request, hospital_id):
    hospital = get_object_or_404(Hospital, id=hospital_id)
    hospital.approval_status = 'approved'
    hospital.approved_by = request.user
    hospital.approved_at = timezone.now()
    hospital.rejection_reason = ''
    hospital.save(update_fields=['approval_status', 'approved_by', 'approved_at', 'rejection_reason'])
    _send_status_email(
        hospital.user.email,
        'ClearDerm: Hospital Account Approval Confirmation',
        (
            f'Dear {hospital.hospital_name},\n\n'
            'We are pleased to inform you that your hospital account has been approved by the ClearDerm administration team.\n'
            'You may now sign in to your account and access your dashboard.\n\n'
            'If you need any assistance, please contact the support team.\n\n'
            'Best regards,\n'
            'ClearDerm Team'
        ),
    )
    messages.success(request, f'Hospital {hospital.hospital_name} approved.')
    return redirect(request.POST.get('next') or 'adminpanel_pending_hospitals')


@_admin_required
@require_http_methods(["POST"])
def reject_hospital(request, hospital_id):
    hospital = get_object_or_404(Hospital, id=hospital_id)
    reason = (request.POST.get('rejection_reason') or '').strip()
    hospital.approval_status = 'rejected'
    hospital.approved_by = request.user
    hospital.approved_at = timezone.now()
    hospital.rejection_reason = reason
    hospital.save(update_fields=['approval_status', 'approved_by', 'approved_at', 'rejection_reason'])
    reason_line = f'\nReason: {reason}\n' if reason else '\n'
    _send_status_email(
        hospital.user.email,
        'ClearDerm: Hospital Account Application Update',
        (
            f'Dear {hospital.hospital_name},\n\n'
            'Thank you for your interest in joining ClearDerm.\n'
            'After review, your hospital account application has not been approved at this time.'
            f'{reason_line}\n'
            'You may update your details and contact support for further guidance.\n\n'
            'Best regards,\n'
            'ClearDerm Team'
        ),
    )
    messages.warning(request, f'Hospital {hospital.hospital_name} disapproved.')
    return redirect(request.POST.get('next') or 'adminpanel_pending_hospitals')


@_admin_required
@require_http_methods(["POST"])
def set_hospital_pending(request, hospital_id):
    hospital = get_object_or_404(Hospital, id=hospital_id)
    hospital.approval_status = 'pending'
    hospital.approved_by = None
    hospital.approved_at = None
    hospital.rejection_reason = ''
    hospital.save(update_fields=['approval_status', 'approved_by', 'approved_at', 'rejection_reason'])
    messages.info(request, f'Hospital {hospital.hospital_name} marked as pending review.')
    return redirect(request.POST.get('next') or 'adminpanel_manage_hospitals')


@_admin_required
@require_http_methods(["POST"])
def activate_user(request, user_id):
    target = get_object_or_404(User, id=user_id)
    target.is_active = True
    target.save(update_fields=['is_active'])
    messages.success(request, f'User {target.username} activated.')
    return redirect(request.POST.get('next') or 'adminpanel_dashboard')


@_admin_required
@require_http_methods(["POST"])
def deactivate_user(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target.id == request.user.id:
        messages.error(request, 'You cannot deactivate your own admin account.')
        return redirect(request.POST.get('next') or 'adminpanel_dashboard')
    target.is_active = False
    target.save(update_fields=['is_active'])
    messages.warning(request, f'User {target.username} deactivated.')
    return redirect(request.POST.get('next') or 'adminpanel_dashboard')


def admin_logout_view(request):
    logout(request)
    messages.success(request, 'Admin logged out successfully.')
    return redirect('adminpanel_login')

