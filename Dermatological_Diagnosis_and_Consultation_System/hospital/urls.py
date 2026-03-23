from django.urls import path
from . import views

urlpatterns = [
    path('', views.hospital_login_view, name='hospital_login'),
    path('register/', views.hospital_register, name='hospital_register'),
    path('dashboard/', views.hospital_dashboard, name='hospital_dashboard'),
    path('profile/', views.hospital_profile, name='hospital_profile'),
    path('doctors/', views.hospital_doctors, name='hospital_doctors'),
    path('doctors/add/', views.hospital_add_doctor, name='hospital_add_doctor'),
    path('doctors/<int:doctor_id>/appointments/', views.hospital_doctor_appointments, name='hospital_doctor_appointments'),
    path('doctors/<int:doctor_id>/delete/', views.hospital_delete_doctor, name='hospital_delete_doctor'),
    path('logout/', views.hospital_logout_view, name='hospital_logout'),
]

