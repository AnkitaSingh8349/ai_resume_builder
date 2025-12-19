from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField

class Resume(models.Model):

    TEMPLATE_CHOICES = [
        ("modern", "Modern Resume"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    # ✅ RICH TEXT FIELDS
    summary = RichTextField(blank=True)
    skills = RichTextField(blank=True)
    experience = RichTextField(blank=True)
    education = RichTextField(blank=True)

    work_link = models.URLField(blank=True, null=True)

    template = models.CharField(
        max_length=50,
        choices=TEMPLATE_CHOICES,
        default="modern"
    )

    color = models.CharField(max_length=20, default="#2563eb")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
