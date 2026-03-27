from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_login_view, name='adminpanel_login'),
    path('dashboard/', views.admin_dashboard, name='adminpanel_dashboard'),
    path('doctors/', views.manage_doctors, name='adminpanel_manage_doctors'),
    path('hospitals/', views.manage_hospitals, name='adminpanel_manage_hospitals'),
    path('patients/', views.manage_patients, name='adminpanel_manage_patients'),
    path('doctors/pending/', views.pending_doctors, name='adminpanel_pending_doctors'),
    path('hospitals/pending/', views.pending_hospitals, name='adminpanel_pending_hospitals'),
    path('doctors/<int:doctor_id>/approve/', views.approve_doctor, name='adminpanel_approve_doctor'),
    path('doctors/<int:doctor_id>/reject/', views.reject_doctor, name='adminpanel_reject_doctor'),
    path('doctors/<int:doctor_id>/pending/', views.set_doctor_pending, name='adminpanel_set_doctor_pending'),
    path('hospitals/<int:hospital_id>/approve/', views.approve_hospital, name='adminpanel_approve_hospital'),
    path('hospitals/<int:hospital_id>/reject/', views.reject_hospital, name='adminpanel_reject_hospital'),
    path('hospitals/<int:hospital_id>/pending/', views.set_hospital_pending, name='adminpanel_set_hospital_pending'),
    path('users/<int:user_id>/activate/', views.activate_user, name='adminpanel_activate_user'),
    path('users/<int:user_id>/deactivate/', views.deactivate_user, name='adminpanel_deactivate_user'),
    path('logout/', views.admin_logout_view, name='adminpanel_logout'),
]

