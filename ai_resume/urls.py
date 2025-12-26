from django.urls import path
from .views import ai_resume_improve

urlpatterns = [
    path("improve/", ai_resume_improve, name="ai_resume_improve"),
    
]
