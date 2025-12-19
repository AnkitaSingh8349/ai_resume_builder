from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import Resume


class ResumeForm(forms.ModelForm):

    # Email field with validation
    email = forms.EmailField(
        required=True,
        error_messages={
            "required": "Email is required",
            "invalid": "Please enter a valid email address"
        },
        widget=forms.EmailInput(attrs={
            "class": "w-full p-2 border rounded",
            "placeholder": "example@email.com"
        })
    )

    # Work / Portfolio Link
    work_link = forms.URLField(
        required=False,
        label="Work / Portfolio Link",
        widget=forms.URLInput(attrs={
            "class": "w-full p-2 border rounded",
            "placeholder": "https://your-portfolio.com"
        })
    )

    # ✅ Rich Text Fields (CKEditor)
    summary = forms.CharField(
        required=False,
        widget=CKEditorWidget()
    )
    skills = forms.CharField(
        required=False,
        widget=CKEditorWidget()
    )
    experience = forms.CharField(
        required=False,
        widget=CKEditorWidget()
    )
    education = forms.CharField(
        required=False,
        widget=CKEditorWidget()
    )

    class Meta:
        model = Resume
        fields = [
            "full_name",
            "email",
            "phone",
            "summary",
            "skills",
            "experience",
            "education",
            "work_link",
            "template",
            "color",
        ]

        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "w-full p-2 border rounded",
                "placeholder": "Full Name"
            }),
            "phone": forms.TextInput(attrs={
                "class": "w-full p-2 border rounded",
                "placeholder": "Phone Number"
            }),
            "template": forms.Select(attrs={
                "class": "w-full p-2 border rounded"
            }),
            "color": forms.TextInput(attrs={
                "type": "color",
                "class": "w-20 h-10 border rounded"
            }),
        }
