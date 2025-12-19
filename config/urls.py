from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import home

urlpatterns = [
    path("", home, name="home"),              # Home
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("resume/", include("resumes.urls")),
    path("ai/", include("ai_resume.urls")),

    # CKEditor
    path("ckeditor/", include("ckeditor_uploader.urls")),
]

# Media files (for image upload in editor)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
