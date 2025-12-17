from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class SignupForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "placeholder": "Enter email address",
        })
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Create password",
        })
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirm password",
        })
    )

    class Meta:
        model = User
        fields = ["username", "email"]
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder": "Choose a username",
            })
        }

    # username validation
    def clean_username(self):
        username = self.cleaned_data.get("username")

        if len(username) < 4:
            raise ValidationError("Username must be at least 4 characters long")

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Username can contain only letters, numbers, and underscore")

        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists")

        return username

    # password validation
    def clean_password1(self):
        password = self.cleaned_data.get("password1")

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number")
        if not re.search(r'[@$!%*?&]', password):
            raise ValidationError("Password must contain at least one special character")

        return password

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise ValidationError("Passwords do not match")
        return cleaned_data
