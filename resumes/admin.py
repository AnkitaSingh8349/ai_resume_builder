from django.contrib import admin
from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "created_at")
