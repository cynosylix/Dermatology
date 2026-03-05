from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Doctor, AppointmentSchedule
from patient.models import Prescription

class DoctorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    license_number = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    specialization = forms.ChoiceField(choices=Doctor.SPECIALIZATION_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    years_of_experience = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
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

class DoctorLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

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
