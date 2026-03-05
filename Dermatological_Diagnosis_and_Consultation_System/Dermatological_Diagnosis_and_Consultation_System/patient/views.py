from django.shortcuts import render, redirect
from django.urls import reverse
from urllib.parse import quote
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import os
import sys
from django.contrib.auth.hashers import make_password
from .forms import PatientRegistrationForm, PatientLoginForm, AppointmentBookingForm
from .models import Patient, Appointment, ChatMessage, AppointmentChatMessage, Prescription, PendingPatientRegistration
from .otp_utils import generate_otp, send_otp_email
from doctor.models import Doctor, AppointmentSchedule
from hospital.models import Hospital
from django.shortcuts import get_object_or_404
from datetime import date, datetime, timedelta
from django.utils import timezone

# Import ML model predictor
try:
    from ml_model.predict import predict_skin_disease
    ML_MODEL_AVAILABLE = True
except ImportError as e:
    print(f"ML model module not available: {str(e)}", file=sys.stderr)
    ML_MODEL_AVAILABLE = False

def home(request):
    return render(request, 'home.html')

@never_cache
def patient_register(request):
    # Check if user is already authenticated
    if request.user.is_authenticated:
        # Check if user is a patient
        try:
            Patient.objects.get(user=request.user)
            return redirect('patient_dashboard')
        except Patient.DoesNotExist:
            # User is authenticated but not a patient, allow registration
            pass

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            try:
                email = form.cleaned_data['email']
                otp = generate_otp(6)
                valid_minutes = getattr(settings, 'OTP_VALID_MINUTES', 10)
                otp_expires_at = timezone.now() + timedelta(minutes=valid_minutes)

                # Store or update pending registration
                pending, created = PendingPatientRegistration.objects.update_or_create(
                    email=email,
                    defaults={
                        'otp': otp,
                        'otp_expires_at': otp_expires_at,
                        'username': form.cleaned_data['username'],
                        'first_name': form.cleaned_data['first_name'],
                        'last_name': form.cleaned_data['last_name'],
                        'password_hash': make_password(form.cleaned_data['password1']),
                        'age': form.cleaned_data['age'],
                        'gender': form.cleaned_data['gender'],
                        'phone_number': form.cleaned_data.get('phone_number', ''),
                        'date_of_birth': form.cleaned_data.get('date_of_birth'),
                        'address': form.cleaned_data.get('address', ''),
                    }
                )

                if send_otp_email(email, otp):
                    messages.success(
                        request,
                        f'A 6-digit OTP has been sent to {email}. Enter it below to complete registration.'
                    )
                    return redirect(reverse('patient_verify_otp') + '?email=' + quote(email))
                else:
                    messages.error(request, 'Failed to send OTP email. Please check your email address and try again.')
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PatientRegistrationForm()
    return render(request, 'patient/register.html', {'form': form})


@never_cache
def patient_verify_otp(request):
    """Verify OTP sent to email and complete patient registration."""
    email = request.GET.get('email', '').strip()
    if not email:
        messages.error(request, 'Invalid verification link. Please register again.')
        return redirect('patient_register')

    if request.method == 'POST':
        otp = request.POST.get('otp', '').strip()
        if not otp:
            messages.error(request, 'Please enter the OTP.')
            return render(request, 'patient/verify_otp.html', {'email': email})

        try:
            pending = PendingPatientRegistration.objects.get(email=email)
        except PendingPatientRegistration.DoesNotExist:
            messages.error(request, 'Registration session expired. Please register again.')
            return redirect('patient_register')

        if timezone.now() > pending.otp_expires_at:
            pending.delete()
            messages.error(request, 'OTP has expired. Please register again.')
            return redirect('patient_register')

        if pending.otp != otp:
            messages.error(request, 'Invalid OTP. Please check and try again.')
            return render(request, 'patient/verify_otp.html', {'email': email})

        try:
            from django.contrib.auth.models import User
            user = User(
                username=pending.username,
                email=pending.email,
                first_name=pending.first_name,
                last_name=pending.last_name,
            )
            user.password = pending.password_hash  # already hashed
            user.save()

            patient = Patient.objects.create(
                user=user,
                age=pending.age,
                gender=pending.gender,
                phone_number=pending.phone_number or '',
                date_of_birth=pending.date_of_birth,
                address=pending.address or '',
            )
            pending.delete()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('patient_login')
        except Exception as e:
            messages.error(request, f'Could not complete registration: {str(e)}')
            return render(request, 'patient/verify_otp.html', {'email': email})

    return render(request, 'patient/verify_otp.html', {'email': email})


@never_cache
def patient_login_view(request):
    # Check if user is already authenticated
    if request.user.is_authenticated:
        # Check if user is a patient
        try:
            Patient.objects.get(user=request.user)
            return redirect('patient_dashboard')
        except Patient.DoesNotExist:
            # User is authenticated but not a patient, show login
            pass
    
    if request.method == 'POST':
        form = PatientLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Check if user is a patient
                try:
                    patient = Patient.objects.get(user=user)
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    return redirect('patient_dashboard')
                except Patient.DoesNotExist:
                    messages.error(request, 'This account is not registered as a patient.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = PatientLoginForm()
    return render(request, 'patient/login.html', {'form': form})

@never_cache
@login_required
def patient_dashboard(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient_logout')
    response = render(request, 'patient/dashboard.html', {'patient': patient})
    # Add cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def patient_profile(request):
    """Display patient profile page with personal information"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient_logout')
    response = render(request, 'patient/profile.html', {'patient': patient})
    # Add cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def patient_logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@never_cache
@login_required
def patient_chatbot_page(request):
    """Render a dedicated page for the dermatology chatbot"""
    response = render(request, 'patient/chatbot.html')
    # Add cache control headers similar to dashboard
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def doctor_list(request):
    """Display list of available doctors for patients to contact"""
    doctors = Doctor.objects.all().order_by('-years_of_experience', 'user__first_name')
    return render(request, 'patient/doctor_list.html', {'doctors': doctors})

@never_cache
@login_required
def hospital_list(request):
    """Display list of available hospitals for patients"""
    hospitals = Hospital.objects.all().order_by('hospital_name')
    return render(request, 'patient/hospital_list.html', {'hospitals': hospitals})

@login_required
def hospital_doctors(request, hospital_id):
    """Display doctors under a specific hospital"""
    hospital = Hospital.objects.get(id=hospital_id)
    doctors = Doctor.objects.filter(hospital=hospital).order_by('-years_of_experience', 'user__first_name')
    return render(request, 'patient/hospital_doctors.html', {
        'hospital': hospital,
        'doctors': doctors
    })

@never_cache
@login_required
def view_doctor_schedules(request, doctor_id):
    """View doctor's appointment schedules"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient_logout')
    
    doctor = get_object_or_404(Doctor, id=doctor_id)
    schedules = AppointmentSchedule.objects.filter(doctor=doctor, is_available=True).order_by('day_of_week', 'start_time')
    
    # Group schedules by day
    schedules_by_day = {}
    for schedule in schedules:
        day = schedule.get_day_of_week_display()
        if day not in schedules_by_day:
            schedules_by_day[day] = {'online': [], 'offline': []}
        schedules_by_day[day][schedule.appointment_type].append(schedule)
    
    response = render(request, 'patient/view_schedules.html', {
        'patient': patient,
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
def book_appointment(request, doctor_id, schedule_id):
    """Book an appointment with a doctor"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient_logout')
    
    doctor = get_object_or_404(Doctor, id=doctor_id)
    schedule = get_object_or_404(AppointmentSchedule, id=schedule_id, doctor=doctor, is_available=True)
    
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment_date = form.cleaned_data['appointment_date']
            appointment_time = form.cleaned_data['appointment_time']
            notes = form.cleaned_data.get('notes', '')
            
            # Check if appointment slot is already taken
            existing_appointment = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['pending', 'confirmed']
            ).exists()
            
            if existing_appointment:
                messages.error(request, 'This time slot is already booked. Please choose another time.')
            else:
                # Validate day of week matches schedule
                day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                selected_day = day_names[appointment_date.weekday()]
                
                if selected_day != schedule.day_of_week:
                    day_display = dict(AppointmentSchedule.DAY_CHOICES)[schedule.day_of_week]
                    messages.error(request, f'This schedule is only available on {day_display}. Please select a {day_display} for your appointment.')
                # Validate time is within schedule
                elif appointment_time < schedule.start_time or appointment_time >= schedule.end_time:
                    from django.template.defaultfilters import time as time_filter
                    messages.error(request, f'Appointment time must be between {time_filter(schedule.start_time, "H:i")} and {time_filter(schedule.end_time, "H:i")}.')
                else:
                    appointment = Appointment.objects.create(
                        patient=patient,
                        doctor=doctor,
                        schedule=schedule,
                        appointment_date=appointment_date,
                        appointment_time=appointment_time,
                        appointment_type=schedule.appointment_type,
                        notes=notes,
                        status='pending'
                    )
                    messages.success(request, f'Appointment booked successfully! Waiting for doctor confirmation.')
                    return redirect('patient_appointments')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Pre-fill form with schedule details
        form = AppointmentBookingForm(initial={
            'appointment_type': schedule.appointment_type
        })
    
    response = render(request, 'patient/book_appointment.html', {
        'patient': patient,
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
def patient_appointments(request):
    """View patient's appointments"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient_logout')
    
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date', '-appointment_time')
    
    # Prefetch prescriptions for efficiency
    appointments = appointments.prefetch_related('prescription')
    
    response = render(request, 'patient/appointments.html', {
        'patient': patient,
        'appointments': appointments
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient_logout')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=patient)
    
    if request.method == 'POST':
        if appointment.status == 'confirmed':
            messages.warning(request, 'Cannot cancel a confirmed appointment. Please contact the doctor.')
        else:
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, 'Appointment cancelled successfully.')
        return redirect('patient_appointments')
    
    response = render(request, 'patient/cancel_appointment.html', {
        'patient': patient,
        'appointment': appointment
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def appointment_chat(request, appointment_id):
    """Chat interface for online appointments"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if user is authorized (either patient or doctor)
    is_patient = False
    is_doctor = False
    
    try:
        patient = Patient.objects.get(user=request.user)
        if appointment.patient == patient:
            is_patient = True
    except Patient.DoesNotExist:
        pass
    
    try:
        from doctor.models import Doctor
        doctor = Doctor.objects.get(user=request.user)
        if appointment.doctor == doctor:
            is_doctor = True
    except:
        pass
    
    if not (is_patient or is_doctor):
        messages.error(request, 'You are not authorized to access this chat.')
        if is_patient:
            return redirect('patient_appointments')
        else:
            return redirect('doctor_appointments')
    
    # Only allow chat for online appointments
    if appointment.appointment_type != 'online':
        messages.error(request, 'Chat is only available for online appointments.')
        if is_patient:
            return redirect('patient_appointments')
        else:
            return redirect('doctor_appointments')
    
    # Get chat messages
    chat_messages = AppointmentChatMessage.objects.filter(appointment=appointment).order_by('created_at')
    
    # Mark messages as read for the other party
    AppointmentChatMessage.objects.filter(
        appointment=appointment
    ).exclude(sender=request.user).update(is_read=True)
    
    # Determine the other party
    if is_patient:
        other_party = appointment.doctor.user
        other_party_name = appointment.doctor.user.get_full_name()
    else:
        other_party = appointment.patient.user
        other_party_name = appointment.patient.user.get_full_name()
    
    response = render(request, 'patient/appointment_chat.html', {
        'appointment': appointment,
        'chat_messages': chat_messages,
        'other_party': other_party,
        'other_party_name': other_party_name,
        'is_patient': is_patient,
        'is_doctor': is_doctor,
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@require_http_methods(["POST"])
@login_required
def send_chat_message(request, appointment_id):
    """Send a chat message (AJAX endpoint, supports optional image)"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check authorization
    is_authorized = False
    try:
        patient = Patient.objects.get(user=request.user)
        if appointment.patient == patient:
            is_authorized = True
    except Patient.DoesNotExist:
        pass
    
    if not is_authorized:
        try:
            from doctor.models import Doctor
            doctor = Doctor.objects.get(user=request.user)
            if appointment.doctor == doctor:
                is_authorized = True
        except:
            pass
    
    if not is_authorized:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if appointment.appointment_type != 'online':
        return JsonResponse({'error': 'Chat is only available for online appointments'}, status=400)

    # Support both JSON (text-only) and multipart (text + image)
    message_text = ''
    image_file = None

    if request.content_type and 'application/json' in request.content_type:
        data = json.loads(request.body.decode('utf-8'))
        message_text = data.get('message', '').strip()
    else:
        message_text = request.POST.get('message', '').strip()
        image_file = request.FILES.get('image')

    if not message_text and not image_file:
        return JsonResponse({'error': 'Message or image is required'}, status=400)

    chat_message = AppointmentChatMessage.objects.create(
        appointment=appointment,
        sender=request.user,
        message=message_text or '',
        image=image_file
    )

    image_url = chat_message.image.url if chat_message.image else None

    return JsonResponse({
        'success': True,
        'message': {
            'id': chat_message.id,
            'sender': chat_message.sender.get_full_name(),
            'message': chat_message.message,
            'image_url': image_url,
            'created_at': chat_message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_sender': True,
        }
    })

@require_http_methods(["GET"])
@login_required
def get_chat_messages(request, appointment_id):
    """Get chat messages (AJAX endpoint for polling)"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check authorization
    is_authorized = False
    try:
        patient = Patient.objects.get(user=request.user)
        if appointment.patient == patient:
            is_authorized = True
    except Patient.DoesNotExist:
        pass
    
    if not is_authorized:
        try:
            from doctor.models import Doctor
            doctor = Doctor.objects.get(user=request.user)
            if appointment.doctor == doctor:
                is_authorized = True
        except:
            pass
    
    if not is_authorized:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get last message ID from query params (for polling)
    last_message_id = request.GET.get('last_message_id', 0)
    try:
        last_message_id = int(last_message_id)
    except:
        last_message_id = 0
    
    # Get new messages
    if last_message_id > 0:
        chat_messages = AppointmentChatMessage.objects.filter(
            appointment=appointment,
            id__gt=last_message_id
        ).order_by('created_at')
    else:
        chat_messages = AppointmentChatMessage.objects.filter(appointment=appointment).order_by('created_at')
    
    # Mark messages as read for the current user (messages from other party)
    AppointmentChatMessage.objects.filter(
        appointment=appointment,
        id__gt=last_message_id
    ).exclude(sender=request.user).update(is_read=True)
    
    messages_list = []
    for msg in chat_messages:
        messages_list.append({
            'id': msg.id,
            'sender': msg.sender.get_full_name(),
            'message': msg.message,
            'image_url': msg.image.url if msg.image else None,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_sender': msg.sender == request.user,
        })
    
    return JsonResponse({
        'messages': messages_list,
        'last_message_id': chat_messages.last().id if chat_messages.exists() else last_message_id
    })

@login_required
def chatbot_view(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient_logout')
    
    # Don't load chat history - start fresh each time
    response = render(request, 'patient/chatbot.html', {
        'patient': patient
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
@require_http_methods(["POST"])
def chatbot_api(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient profile not found.'}, status=403)
    
    try:
        user_message = request.POST.get('message', '').strip()
        image_file = request.FILES.get('image', None)
        
        if not user_message and not image_file:
            return JsonResponse({'error': 'Message or image is required.'}, status=400)
        
        # Initialize prediction results
        prediction_results = None
        
        # If image is uploaded, run ML model prediction
        image_saved_path = None
        if image_file:
            if not ML_MODEL_AVAILABLE:
                prediction_results = {
                    'success': False,
                    'error': 'ML model is not available. Please ensure skin_disease_model.h5 is in ml_model/models/ directory.'
                }
            else:
                try:
                    # Sanitize filename to avoid issues with special characters
                    import re
                    from io import BytesIO
                    from django.core.files.uploadedfile import InMemoryUploadedFile
                    
                    safe_filename = re.sub(r'[^\w\-_\.]', '_', image_file.name)
                    temp_image_path = os.path.join(settings.MEDIA_ROOT, 'chatbot_uploads', f'temp_{patient.user.id}_{safe_filename}')
                    os.makedirs(os.path.dirname(temp_image_path), exist_ok=True)
                    
                    # Read all chunks into memory first
                    image_content = BytesIO()
                    for chunk in image_file.chunks():
                        image_content.write(chunk)
                    image_content.seek(0)
                    
                    # Save to disk for prediction
                    with open(temp_image_path, 'wb+') as destination:
                        destination.write(image_content.getvalue())
                    
                    # Verify image was saved
                    if not os.path.exists(temp_image_path) or os.path.getsize(temp_image_path) == 0:
                        raise ValueError("Failed to save image file")
                    
                    # Run prediction with improved preprocessing (try both normalization methods)
                    prediction_results = predict_skin_disease(temp_image_path, try_both_norms=True)
                    
                    # Keep the file path for database storage
                    image_saved_path = temp_image_path
                    
                    # Reset the BytesIO object for database storage
                    image_content.seek(0)
                    # Create a new InMemoryUploadedFile from the content
                    image_file = InMemoryUploadedFile(
                        image_content,
                        None,
                        safe_filename,
                        image_file.content_type,
                        image_content.tell(),
                        None
                    )
                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"Error in image prediction: {str(e)}", file=sys.stderr)
                    print(f"Traceback: {error_trace}", file=sys.stderr)
                    prediction_results = {
                        'success': False,
                        'error': f'Error analyzing image: {str(e)}'
                    }
                    # Clean up temp file if it exists
                    if 'temp_image_path' in locals() and os.path.exists(temp_image_path):
                        try:
                            os.remove(temp_image_path)
                        except:
                            pass
        
        # Generate bot response based on user message and prediction
        bot_response = generate_chatbot_response(user_message, image_file is not None, prediction_results)
        
        # Save chat message
        try:
            chat_message_data = {
                'patient': patient,
                'message': user_message or 'Image uploaded',
                'response': bot_response,
            }
            if image_file:
                chat_message_data['image'] = image_file
                chat_message = ChatMessage.objects.create(**chat_message_data)
                # Clean up temp file if it exists
                if image_saved_path and os.path.exists(image_saved_path):
                    try:
                        os.remove(image_saved_path)
                    except:
                        pass
            else:
                chat_message = ChatMessage.objects.create(**chat_message_data)
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error saving chat message: {str(e)}", file=sys.stderr)
            print(f"Traceback: {error_trace}", file=sys.stderr)
            # Clean up temp file if it exists
            if image_saved_path and os.path.exists(image_saved_path):
                try:
                    os.remove(image_saved_path)
                except:
                    pass
            # Still return response even if saving fails
            chat_message = None
        
        response_data = {
            'success': True,
            'response': bot_response,
        }
        
        # Add timestamp if chat message was saved
        if chat_message:
            response_data['timestamp'] = chat_message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            # Include image URL if image was uploaded
            if chat_message.image:
                try:
                    response_data['image_url'] = chat_message.image.url
                except:
                    pass
        
        # Include prediction results in response (use ml_prediction to match JavaScript)
        if prediction_results:
            response_data['ml_prediction'] = prediction_results
        
        return JsonResponse(response_data)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        # Log the error for debugging
        print(f"Error in chatbot_api: {error_msg}", file=sys.stderr)
        print(f"Traceback: {error_trace}", file=sys.stderr)
        # Return a user-friendly error message
        return JsonResponse({'error': error_msg, 'success': False}, status=500)

@login_required
@require_http_methods(["POST"])
def clear_chat(request):
    """Clear all chat messages for the current patient"""
    try:
        patient = Patient.objects.get(user=request.user)
        # Delete all chat messages for this patient
        deleted_count = ChatMessage.objects.filter(patient=patient).delete()[0]
        return JsonResponse({
            'success': True,
            'message': f'Cleared {deleted_count} chat message(s).'
        })
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient profile not found.'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def generate_chatbot_response(user_message, has_image=False, prediction_results=None):
    """Generate a response based on user message and ML prediction"""
    user_message_lower = user_message.lower()
    
    # Greetings
    if any(word in user_message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        return "Hello! I'm ClearDerm AI Assistant. I'm here to help you with questions about skin conditions and dermatology. You can upload an image of a skin condition for AI analysis, or ask me questions. How can I assist you today?"
    
    # Image-related responses with ML prediction
    if has_image:
        response = "Thank you for sharing the image. I've analyzed it using our AI model.\n\n"
        
        if prediction_results and prediction_results.get('success'):
            top_prediction = prediction_results.get('top_prediction')
            all_predictions = prediction_results.get('predictions', [])
            
            if top_prediction:
                disease_name = top_prediction['disease']
                confidence = top_prediction['confidence']
                
                response += f"**AI Prediction Results:**\n\n"
                response += f"🔍 **Most Likely Condition:** {disease_name}\n"
                response += f"📊 **Confidence Level:** {confidence}%\n\n"
                
                if len(all_predictions) > 1:
                    response += "**Other Possible Conditions:**\n"
                    for i, pred in enumerate(all_predictions[1:], 1):
                        response += f"{i}. {pred['disease']} ({pred['confidence']}%)\n"
                    response += "\n"
                
                # Add information about the predicted disease
                response += get_disease_information(disease_name)
            else:
                response += "I was unable to make a confident prediction. Please consult with a dermatologist for proper evaluation.\n\n"
        else:
            if prediction_results and not prediction_results.get('success'):
                error_msg = prediction_results.get('error', 'Unknown error')
                response += f"⚠️ I encountered an issue analyzing the image: {error_msg}\n\n"
            else:
                response += "I'm processing your image. Please wait a moment...\n\n"
        
        response += "⚠️ **Important Disclaimer:** This AI prediction is for informational purposes only and should not be used as a medical diagnosis. The results are based on image analysis and may not be accurate. Please consult with a qualified dermatologist for proper diagnosis and treatment."
        
        return response
    
    # Common skin conditions
    if any(word in user_message_lower for word in ['melanoma', 'cancer']):
        return "Melanoma is a serious form of skin cancer. Early detection is crucial. If you notice any changes in moles or skin lesions (asymmetry, irregular borders, color variation, diameter >6mm, or evolution), please consult a dermatologist immediately. I cannot diagnose, but I recommend professional evaluation."
    
    if any(word in user_message_lower for word in ['eczema', 'atopic']):
        return "Eczema (atopic dermatitis) is a common skin condition characterized by dry, itchy, and inflamed skin. Common symptoms include redness, itching, and dry patches. Treatment often involves moisturizing, avoiding triggers, and sometimes topical corticosteroids. For proper diagnosis and treatment, please consult a dermatologist."
    
    if any(word in user_message_lower for word in ['psoriasis']):
        return "Psoriasis is an autoimmune condition that causes red, scaly patches on the skin. It can affect various parts of the body. Treatment options include topical treatments, light therapy, and systemic medications. A dermatologist can provide proper diagnosis and create a treatment plan tailored to your needs."
    
    if any(word in user_message_lower for word in ['acne', 'pimple', 'pimples']):
        return "Acne is a common skin condition that affects many people. It can be caused by various factors including hormones, bacteria, and excess oil production. Treatment options range from over-the-counter products to prescription medications. For persistent or severe acne, consulting a dermatologist is recommended."
    
    if any(word in user_message_lower for word in ['rash', 'irritation', 'itchy']):
        return "Rashes and skin irritations can have many causes including allergies, infections, or skin conditions. It's important to identify the cause for proper treatment. If the rash persists, worsens, or is accompanied by other symptoms, please consult a dermatologist for evaluation."
    
    if any(word in user_message_lower for word in ['mole', 'moles', 'nevus']):
        return "Moles (nevi) are common skin growths. Most are harmless, but it's important to monitor them for changes. Use the ABCDE rule: Asymmetry, Border irregularity, Color variation, Diameter >6mm, and Evolution (changes). If you notice any concerning changes, please see a dermatologist."
    
    # General help
    if any(word in user_message_lower for word in ['help', 'what can you do', 'how can you help']):
        return "I can provide general information about common skin conditions, symptoms, and when to seek medical attention. However, I cannot provide medical diagnoses or replace professional medical advice. For any concerns about your skin health, please consult with a qualified dermatologist. What would you like to know?"
    
    # Appointment/scheduling
    if any(word in user_message_lower for word in ['appointment', 'schedule', 'book', 'consultation']):
        return "To schedule an appointment with a dermatologist, please use the doctor portal or contact your healthcare provider. You can also check the hospital portal for available appointments. Would you like information about finding a dermatologist?"
    
    # Default response
    return "Thank you for your message. I'm here to help with general information about skin conditions and dermatology. You can upload an image of a skin condition for AI analysis, or ask me questions. However, I cannot provide medical diagnoses. For specific concerns about your skin health, I strongly recommend consulting with a qualified dermatologist. Is there a particular skin condition or topic you'd like to learn more about?"

def get_disease_information(disease_name):
    """Get information about a specific disease"""
    disease_info = {
        "Atopic Dermatitis": "Atopic dermatitis (eczema) is a condition that makes your skin red and itchy. It's common in children but can occur at any age. Common symptoms include dry, scaly skin, intense itching, and red or brownish-gray patches. Treatment typically involves moisturizing regularly, avoiding triggers, and using prescribed medications.",
        
        "Basal Cell Carcinoma": "Basal cell carcinoma is the most common type of skin cancer. It usually appears as a waxy bump, flat brown or flesh-colored lesion, or a bleeding sore that heals and returns. It rarely spreads to other parts of the body but should be treated promptly. Early detection and treatment are important.",
        
        "Benign Keratosis-like Lesions": "Benign keratosis-like lesions are non-cancerous skin growths that can appear as warty, scaly patches. They're typically harmless but can be removed if they cause discomfort or cosmetic concerns. A dermatologist can help determine if removal is necessary.",
        
        "Eczema": "Eczema is a group of conditions that cause inflammation of the skin. Symptoms include itchy, red, and dry skin. Common types include atopic dermatitis, contact dermatitis, and seborrheic dermatitis. Treatment involves moisturizing, avoiding irritants, and sometimes prescription medications.",
        
        "Melanocytic Nevi": "Melanocytic nevi (moles) are common skin growths that are usually harmless. Most people have 10-40 moles. It's important to monitor moles for changes using the ABCDE rule: Asymmetry, Border irregularity, Color variation, Diameter >6mm, and Evolution. Regular skin checks are recommended.",
        
        "Melanoma": "Melanoma is a serious form of skin cancer that develops in melanocytes. It can appear as a new mole or a change in an existing mole. Early detection is crucial for successful treatment. If you notice any suspicious changes, consult a dermatologist immediately. Regular skin examinations are important.",
        
        "Psoriasis pictures Lichen Planus and related diseases": "Psoriasis is an autoimmune condition causing rapid skin cell buildup, resulting in scaly patches. Lichen planus is an inflammatory condition that can affect the skin, hair, nails, and mucous membranes. Both conditions require medical evaluation and treatment. A dermatologist can provide proper diagnosis and management.",
        
        "Seborrheic Keratoses and other Benign Tumors": "Seborrheic keratoses are common, non-cancerous skin growths that appear as waxy, scaly, slightly raised lesions. They're typically brown, black, or light tan. These are harmless and don't require treatment unless they cause discomfort or cosmetic concerns.",
        
        "Tinea Ringworm Candidiasis and other Fungal Infections": "Fungal skin infections like ringworm (tinea) and candidiasis are caused by fungi. Symptoms include red, itchy, scaly patches or rashes. These infections are treatable with antifungal medications. Proper hygiene and avoiding sharing personal items can help prevent spread.",
        
        "Warts Molluscum and other Viral Infections": "Viral skin infections like warts and molluscum contagiosum are caused by viruses. Warts appear as rough, raised bumps, while molluscum appears as small, pearly bumps. These conditions are usually harmless but can be treated if they cause discomfort or spread. A dermatologist can recommend appropriate treatment."
    }
    
    return disease_info.get(disease_name, f"Information about {disease_name} is available. Please consult a dermatologist for detailed information and proper diagnosis.")

@never_cache
@login_required
def patient_prescriptions(request):
    """View all prescriptions for the patient"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('patient_logout')
    
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')
    
    response = render(request, 'patient/prescriptions.html', {
        'patient': patient,
        'prescriptions': prescriptions
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def view_prescription(request, prescription_id):
    """View prescription details - wrapper to use doctor's view"""
    from doctor.views import view_prescription as doctor_view_prescription
    return doctor_view_prescription(request, prescription_id)
