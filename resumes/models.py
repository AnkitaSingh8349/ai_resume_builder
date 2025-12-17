from django.db import models
from django.contrib.auth.models import User

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    summary = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
