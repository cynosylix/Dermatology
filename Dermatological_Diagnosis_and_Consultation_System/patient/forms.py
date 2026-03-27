from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Patient, Appointment
from doctor.models import Doctor, AppointmentSchedule
from datetime import date, datetime, timedelta
from django.utils import timezone
import re


def _is_strong_indian_mobile(phone_number: str) -> bool:
    if not re.fullmatch(r'[6-9][0-9]{9}', phone_number):
        return False
    if len(set(phone_number)) == 1:
        return False
    if phone_number in {'9876543210', '1234567890'}:
        return False
    return True

class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your first name'})
    )
    last_name = forms.CharField(
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your last name'})
    )
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'})
    )
    age = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=150,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter your age', 'min': '1', 'max': '150'})
    )
    gender = forms.ChoiceField(
        required=True,
        choices=[('', 'Select Gender'), ('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        error_messages={'required': 'Please select your gender'}
    )
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age and (age < 1 or age > 150):
            raise forms.ValidationError('Age must be between 1 and 150')
        return age
    
    def clean_gender(self):
        gender = self.cleaned_data.get('gender')
        if not gender or gender == '':
            raise forms.ValidationError('Please select your gender')
        return gender
    phone_number = forms.CharField(
        max_length=10,
        required=False, 
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter 10-digit mobile number (optional, without +91)',
                'maxlength': '10',
                'minlength': '10',
                'inputmode': 'numeric',
                'pattern': '[6-9][0-9]{9}',
                'title': 'Enter 10-digit mobile number without country code',
            }
        )
    )
    date_of_birth = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    address = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address (optional)'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered. Please use another email.")
        return email

    def clean_phone_number(self):
        phone_number = (self.cleaned_data.get('phone_number') or '').strip()
        if not phone_number:
            return ''
        if not _is_strong_indian_mobile(phone_number):
            raise forms.ValidationError(
                "Enter a valid Indian mobile number (10 digits, starts with 6-9, and not a dummy sequence)."
            )
        return phone_number

class PatientLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class AppointmentBookingForm(forms.ModelForm):
    appointment_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'min': str(date.today())})
    )
    appointment_time = forms.TimeField(
        required=True,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your symptoms or reason for appointment (optional)'})
    )
    
    class Meta:
        model = Appointment
        fields = ['appointment_date', 'appointment_time', 'notes']
    
    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date and appointment_date < date.today():
            raise forms.ValidationError("Appointment date cannot be in the past.")
        return appointment_date
    
    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        
        if appointment_date and appointment_time:
            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            if timezone.now() > timezone.make_aware(appointment_datetime):
                raise forms.ValidationError("Appointment date and time cannot be in the past.")
        
        return cleaned_data