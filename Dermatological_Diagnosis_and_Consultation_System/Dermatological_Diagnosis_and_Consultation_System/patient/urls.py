from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('patient/', views.patient_login_view, name='patient_login'),
    path('patient/register/', views.patient_register, name='patient_register'),
    path('patient/register/verify-otp/', views.patient_verify_otp, name='patient_verify_otp'),
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/chatbot/page/', views.patient_chatbot_page, name='patient_chatbot_page'),
    path('patient/profile/', views.patient_profile, name='patient_profile'),
    path('patient/logout/', views.patient_logout_view, name='patient_logout'),
    # Chatbot URLs
    path('patient/chatbot/', views.chatbot_view, name='chatbot'),
    path('patient/chatbot/api/', views.chatbot_api, name='chatbot_api'),
    path('patient/chatbot/clear/', views.clear_chat, name='clear_chat'),
    # Appointment system URLs
    path('patient/doctors/', views.doctor_list, name='doctor_list'),
    path('patient/hospitals/', views.hospital_list, name='hospital_list'),
    path('patient/hospitals/<int:hospital_id>/doctors/', views.hospital_doctors, name='hospital_doctors'),
    path('patient/doctors/<int:doctor_id>/schedules/', views.view_doctor_schedules, name='view_doctor_schedules'),
    path('patient/doctors/<int:doctor_id>/schedules/<int:schedule_id>/book/', views.book_appointment, name='book_appointment'),
    path('patient/appointments/', views.patient_appointments, name='patient_appointments'),
    path('patient/appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('patient/appointments/<int:appointment_id>/chat/', views.appointment_chat, name='appointment_chat'),
    path('patient/appointments/<int:appointment_id>/chat/send/', views.send_chat_message, name='send_chat_message'),
    path('patient/appointments/<int:appointment_id>/chat/messages/', views.get_chat_messages, name='get_chat_messages'),
    # Prescription URLs
    path('patient/prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
    path('patient/prescriptions/<int:prescription_id>/', views.view_prescription, name='view_prescription'),
]

