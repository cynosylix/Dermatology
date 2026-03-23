"""OTP generation and email sending for registration verification."""
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


def generate_otp(length=6):
    """Generate a numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(to_email, otp):
    """Send OTP to the given email address. Returns True on success."""
    valid_minutes = getattr(settings, 'OTP_VALID_MINUTES', 10)
    subject = 'Your ClearDerm registration OTP'
    message = (
        f'Your one-time password for completing ClearDerm patient registration is: {otp}\n\n'
        f'This code is valid for {valid_minutes} minutes. Do not share it with anyone.\n\n'
        'If you did not request this, please ignore this email.'
    )
    try:
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@clearderm.example.com'),
            [to_email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False
