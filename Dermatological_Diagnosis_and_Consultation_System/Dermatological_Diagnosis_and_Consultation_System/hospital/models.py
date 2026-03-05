from django.db import models
from django.contrib.auth.models import User

class Hospital(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hospital_name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=50, unique=True)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    total_beds = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.hospital_name

