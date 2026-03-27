from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from hospital.models import Hospital


class HospitalApprovalTests(TestCase):
    def test_hospital_default_approval_status_is_pending(self):
        user = User.objects.create_user(
            username='hospital_default_pending',
            email='hospital_default_pending@example.com',
            password='StrongPass@123',
            first_name='Demo',
            last_name='Hospital',
        )
        hospital = Hospital.objects.create(
            user=user,
            hospital_name='Demo Hospital',
            registration_number='HOSP-TEST-0001',
            address='Test Address',
            phone_number='9876543213',
            email='hospital_profile_email@example.com',
            total_beds=120,
        )
        self.assertEqual(hospital.approval_status, 'pending')

    def test_pending_hospital_cannot_login(self):
        user = User.objects.create_user(
            username='pending_hospital',
            email='pending_hospital@example.com',
            password='StrongPass@123',
            first_name='Pending',
            last_name='Hospital',
        )
        Hospital.objects.create(
            user=user,
            hospital_name='Pending Hospital',
            registration_number='HOSP-TEST-0002',
            address='Test Address',
            phone_number='9876543214',
            email='pending_hospital_profile@example.com',
            total_beds=80,
            approval_status='pending',
        )

        response = self.client.post(
            reverse('hospital_login'),
            data={'username': 'pending_hospital', 'password': 'StrongPass@123'},
            follow=True,
        )
        self.assertContains(
            response,
            'Your registration is under administrative review. You can sign in once approval is completed.',
        )
        self.assertNotIn('_auth_user_id', self.client.session)
