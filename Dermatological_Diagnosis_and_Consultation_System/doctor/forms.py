from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Doctor, AppointmentSchedule
from patient.models import Prescription
import re


def _is_strong_indian_mobile(phone_number: str) -> bool:
    """Validate Indian mobile format and reject obvious dummy values."""
    if not re.fullmatch(r'[6-9][0-9]{9}', phone_number):
        return False

    # Reject all-same digits (e.g., 9999999999, 7777777777)
    if len(set(phone_number)) == 1:
        return False

    # Reject obvious sequential placeholders
    if phone_number in {'9876543210', '1234567890'}:
        return False

    return True


def _is_strong_license_number(license_number: str) -> bool:
    """
    Demo license format:
    - 2-10 letters prefix
    - optional separator (space, '/' or '-')
    - 5-7 digits suffix
    Examples: KLMC 45678, TNMC-1234567, ABCD/98765
    """
    if not re.fullmatch(r'[A-Z]{2,10}[ /-]?[0-9]{5,7}', license_number):
        return False

    digits = re.search(r'([0-9]{5,7})$', license_number)
    if digits and len(set(digits.group(1))) == 1:
        return False

    return True

class DoctorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    license_number = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'e.g. KLMC 45678',
                'pattern': '[A-Za-z]{2,10}[ /-]?[0-9]{5,7}',
                'title': 'Use 2-10 letters followed by 5-7 digits (e.g., KLMC 45678)',
            }
        ),
    )
    specialization = forms.ChoiceField(choices=Doctor.SPECIALIZATION_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'maxlength': '10',
                'minlength': '10',
                'inputmode': 'numeric',
                'pattern': '[6-9][0-9]{9}',
                'placeholder': 'Enter 10-digit mobile number (without +91)',
                'title': 'Enter 10-digit mobile number without country code',
            }
        )
    )
    years_of_experience = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    profile_picture = forms.ImageField(
        required=True,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '').strip()
        if not _is_strong_indian_mobile(phone_number):
            raise forms.ValidationError(
                "Enter a valid Indian mobile number (10 digits, starts with 6-9, and not a dummy sequence)."
            )
        return phone_number

    def clean_license_number(self):
        license_number = re.sub(r'\s+', ' ', self.cleaned_data.get('license_number', '').strip().upper())
        if not _is_strong_license_number(license_number):
            raise forms.ValidationError(
                "Enter a valid demo license number (2-10 letters + 5-7 digits), e.g. KLMC 45678."
            )
        return license_number

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered. Please use another email.")
        return email

class DoctorLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class DoctorProfilePictureForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.ClearableFileInput(
                attrs={'class': 'form-control', 'accept': 'image/*'}
            ),
        }


class AppointmentScheduleForm(forms.ModelForm):
    class Meta:
        model = AppointmentSchedule
        fields = ['day_of_week', 'start_time', 'end_time', 'appointment_type', 'is_available', 'duration_minutes']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'appointment_type': forms.Select(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'step': 15}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")
        
        return cleaned_data

class PrescriptionForm(forms.ModelForm):
    diagnosis = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter diagnosis and clinical notes...'
        }),
        help_text='Diagnosis and clinical observations'
    )
    medications = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter medications with dosage and duration. Example:\n- Medicine Name: Dosage, Duration\n- Another Medicine: Dosage, Duration'
        }),
        help_text='List all medications with dosage and duration'
    )
    advice = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Lifestyle advice, follow-up instructions, or any additional recommendations...'
        }),
        help_text='Optional: Lifestyle advice and follow-up instructions'
    )
    
    class Meta:
        model = Prescription
        fields = ['diagnosis', 'medications', 'advice']
