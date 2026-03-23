# Portal Registration and Login Guide

## Overview
All three portals (Patient, Doctor, and Hospital) are fully configured with registration and login functionality.

## Portal URLs

### Patient Portal
- **Home Page**: http://127.0.0.1:8000/
- **Login**: http://127.0.0.1:8000/patient/
- **Register**: http://127.0.0.1:8000/patient/register/
- **Dashboard**: http://127.0.0.1:8000/patient/dashboard/
- **Logout**: http://127.0.0.1:8000/patient/logout/

### Doctor Portal
- **Login**: http://127.0.0.1:8000/doctor/
- **Register**: http://127.0.0.1:8000/doctor/register/
- **Dashboard**: http://127.0.0.1:8000/doctor/dashboard/
- **Logout**: http://127.0.0.1:8000/doctor/logout/

### Hospital Portal
- **Login**: http://127.0.0.1:8000/hospital/
- **Register**: http://127.0.0.1:8000/hospital/register/
- **Dashboard**: http://127.0.0.1:8000/hospital/dashboard/
- **Logout**: http://127.0.0.1:8000/hospital/logout/

## Registration Fields

### Patient Registration
- Username
- First Name
- Last Name
- Email
- Phone Number
- Date of Birth
- Address
- Password
- Confirm Password

### Doctor Registration
- Username
- First Name
- Last Name
- Email
- License Number (unique)
- Specialization (Dermatology, General Practice, Pediatric Dermatology, Surgical Dermatology)
- Phone Number
- Years of Experience
- Password
- Confirm Password

### Hospital Registration
- Username
- Contact Person First Name
- Contact Person Last Name
- Contact Email
- Hospital Name
- Registration Number (unique)
- Address
- Phone Number
- Hospital Email
- Total Beds
- Password
- Confirm Password

## Features

✅ **Registration**
- All three portals have complete registration forms
- Data validation and error handling
- User accounts are created in Django's User model
- Profile data is stored in respective models (Patient, Doctor, Hospital)

✅ **Login**
- Secure authentication using Django's built-in system
- Portal-specific login validation (users can only login to their registered portal)
- Automatic redirect to dashboard after successful login
- Error messages for invalid credentials

✅ **Dashboard**
- Protected routes (require login)
- Display user-specific information
- Logout functionality

✅ **Security**
- CSRF protection enabled
- Password hashing
- Session management
- Portal isolation (patients can't login as doctors, etc.)

## Testing the Portals

1. **Start the server**:
   ```bash
   python manage.py runserver
   ```

2. **Test Patient Portal**:
   - Go to http://127.0.0.1:8000/patient/register/
   - Fill in the registration form
   - Submit and verify registration
   - Login at http://127.0.0.1:8000/patient/
   - Access dashboard

3. **Test Doctor Portal**:
   - Go to http://127.0.0.1:8000/doctor/register/
   - Fill in the registration form
   - Submit and verify registration
   - Login at http://127.0.0.1:8000/doctor/
   - Access dashboard

4. **Test Hospital Portal**:
   - Go to http://127.0.0.1:8000/hospital/register/
   - Fill in the registration form
   - Submit and verify registration
   - Login at http://127.0.0.1:8000/hospital/
   - Access dashboard

## Database Tables

- `auth_user` - Django's user accounts
- `patient_patient` - Patient profiles
- `doctor_doctor` - Doctor profiles
- `hospital_hospital` - Hospital profiles

## Notes

- Each user type is isolated - a patient cannot login through the doctor portal
- All forms have CSRF protection
- All forms have explicit action URLs to prevent routing issues
- Error messages are displayed for validation failures
- Success messages confirm successful registration/login

