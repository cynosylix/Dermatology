cmd
git pull
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
# Dermatological_Diagnosis_and_Consultation_System

ClearDerm is an advanced dermatological diagnosis and consultation platform aimed at enhancing the accuracy, accessibility, and efficiency of skin disease detection and management.

## Features

- **Patient Module**: Registration and login for patients
- **Doctor Module**: Registration and login for doctors with specialization tracking
- **Hospital Module**: Registration and login for hospitals

## Installation

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser** (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

7. **Access the application**:
   - Home page: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Usage

### Patient Registration/Login
- Visit http://127.0.0.1:8000/patient/ to login
- Visit http://127.0.0.1:8000/patient/register/ to register as a new patient

### Doctor Registration/Login
- Visit http://127.0.0.1:8000/doctor/ to login
- Visit http://127.0.0.1:8000/doctor/register/ to register as a new doctor

### Hospital Registration/Login
- Visit http://127.0.0.1:8000/hospital/ to login
- Visit http://127.0.0.1:8000/hospital/register/ to register as a new hospital

## Project Structure

```
dermatology_system/
├── dermatology_system/     # Main project settings
├── patient/                # Patient app
├── doctor/                 # Doctor app
├── hospital/               # Hospital app
├── templates/              # HTML templates
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## Technologies Used

- Django 4.2.7
- Bootstrap 5.3.0 (via CDN)
- SQLite (default database)








