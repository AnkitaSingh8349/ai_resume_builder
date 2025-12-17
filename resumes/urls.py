from django.urls import path
from .views import create_resume

urlpatterns = [
    path("create/", create_resume, name="create_resume"),
]
