from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_premium = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class Resume(models.Model):

    TEMPLATE_CHOICES = [
        ("modern", "Modern Resume"),
        ("professional", "Professional Resume"),
        ("simple", "Simple Resume"),
        ("creative", "Creative Resume"),
        ("executive", "Executive Resume"),
        ("minimalist", "Minimalist Resume"),
    ]

    # ✅ CHANGED HERE (MOST IMPORTANT LINE)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="resumes"
    )

    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)

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
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.template})"

    def is_premium_template(self):
        return self.template in ["creative", "executive", "minimalist"]
