from django.urls import path
from . import views

app_name = "resumes"

urlpatterns = [
    path("create/", views.create_resume, name="create_resume"),
    path("edit/<int:id>/", views.edit_resume, name="edit_resume"),
    path("preview/<int:id>/", views.resume_preview, name="resume_preview"),
    path("download/<int:id>/", views.download_resume, name="download_resume"),
    path("public/<int:id>/", views.resume_public, name="resume_public"),
    path("my/", views.my_resumes, name="my_resumes"),
    path("save-field/<int:id>/", views.save_resume_field, name="save_resume_field"),

    # ===============================
    # STRIPE PAYMENT ROUTES
    # ===============================
    path("checkout/", views.create_checkout_session, name="checkout"),
    path("payment-success/", views.payment_success, name="payment_success"),
]
