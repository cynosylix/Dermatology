from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from doctor.models import Doctor


class DoctorApprovalTests(TestCase):
    def test_doctor_default_approval_status_is_pending(self):
        user = User.objects.create_user(
            username='doctor_default_pending',
            email='doctor_default_pending@example.com',
            password='StrongPass@123',
            first_name='Demo',
            last_name='Doctor',
        )
        doctor = Doctor.objects.create(
            user=user,
            license_number='KLMC 45678',
            specialization='dermatology',
            phone_number='9876543211',
            years_of_experience=5,
        )
        self.assertEqual(doctor.approval_status, 'pending')

    def test_pending_doctor_cannot_login(self):
        user = User.objects.create_user(
            username='pending_doctor',
            email='pending_doctor@example.com',
            password='StrongPass@123',
            first_name='Pending',
            last_name='Doctor',
        )
        Doctor.objects.create(
            user=user,
            license_number='KLMC 45679',
            specialization='dermatology',
            phone_number='9876543212',
            years_of_experience=6,
            approval_status='pending',
        )

        response = self.client.post(
            reverse('doctor_login'),
            data={'username': 'pending_doctor', 'password': 'StrongPass@123'},
            follow=True,
        )
        self.assertContains(
            response,
            'Your registration is under administrative review. You can sign in once approval is completed.',
        )
        self.assertNotIn('_auth_user_id', self.client.session)
