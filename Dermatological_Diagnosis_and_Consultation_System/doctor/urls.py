from django.urls import path
from . import views

urlpatterns = [
    path('', views.doctor_login_view, name='doctor_login'),
    path('register/', views.doctor_register, name='doctor_register'),
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('profile/', views.doctor_profile, name='doctor_profile'),
    path('schedules/', views.doctor_schedules, name='doctor_schedules'),
    path('schedules/add/', views.doctor_add_schedule, name='doctor_add_schedule'),
    path('schedules/<int:schedule_id>/edit/', views.doctor_edit_schedule, name='doctor_edit_schedule'),
    path('schedules/<int:schedule_id>/delete/', views.doctor_delete_schedule, name='doctor_delete_schedule'),
    path('appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('appointments/<int:appointment_id>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointments/<int:appointment_id>/cancel/', views.cancel_appointment_doctor, name='cancel_appointment_doctor'),
    path('appointments/<int:appointment_id>/chat/', views.appointment_chat, name='doctor_appointment_chat'),
    path('appointments/<int:appointment_id>/chat/send/', views.send_chat_message, name='doctor_send_chat_message'),
    path('appointments/<int:appointment_id>/chat/messages/', views.get_chat_messages, name='doctor_get_chat_messages'),
    # Prescription URLs
    path('appointments/<int:appointment_id>/prescription/create/', views.create_prescription, name='create_prescription'),
    path('prescriptions/', views.doctor_prescriptions, name='doctor_prescriptions'),
    path('prescriptions/<int:prescription_id>/', views.view_prescription, name='view_prescription'),
    path('logout/', views.doctor_logout_view, name='doctor_logout'),
]

