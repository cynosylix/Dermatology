from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Hospital
from doctor.models import Doctor
import re
import uuid


def _is_strong_indian_mobile(phone_number: str) -> bool:
    """Validate Indian mobile format and reject obvious dummy values."""
    if not re.fullmatch(r'[6-9][0-9]{9}', phone_number):
        return False
    if len(set(phone_number)) == 1:
        return False
    if phone_number in {'9876543210', '1234567890'}:
        return False
    return True


def _is_strong_license_number(license_number: str) -> bool:
    if not re.fullmatch(r'[A-Z]{2,10}[ /-]?[0-9]{5,7}', license_number):
        return False

    digits = re.search(r'([0-9]{5,7})$', license_number)
    if digits and len(set(digits.group(1))) == 1:
        return False

    return True

class HospitalRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    hospital_name = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    registration_number = forms.CharField(max_length=50, required=False, widget=forms.HiddenInput())
    address = forms.CharField(required=True, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
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
        ),
    )
    hospital_email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    total_beds = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
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

    def clean_registration_number(self):
        registration_number = (self.cleaned_data.get('registration_number') or '').strip()
        if registration_number:
            return registration_number

        # Keep the DB field populated while hiding it from UI.
        while True:
            generated = f"HOSP-{uuid.uuid4().hex[:10].upper()}"
            if not Hospital.objects.filter(registration_number=generated).exists():
                return generated

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered. Please use another email.")
        return email

    def clean_hospital_email(self):
        hospital_email = (self.cleaned_data.get('hospital_email') or '').strip().lower()
        if User.objects.filter(email__iexact=hospital_email).exists():
            raise forms.ValidationError("This hospital email is already registered. Please use another email.")
        return hospital_email

    def clean_phone_number(self):
        phone_number = (self.cleaned_data.get('phone_number') or '').strip()
        if not _is_strong_indian_mobile(phone_number):
            raise forms.ValidationError(
                "Enter a valid Indian mobile number (10 digits, starts with 6-9, and not a dummy sequence)."
            )
        return phone_number

class HospitalLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class HospitalCreateDoctorForm(UserCreationForm):
    """Form for hospitals to create doctors"""
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
    years_of_experience = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0}))
    
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