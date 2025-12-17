from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Resume

@login_required
def create_resume(request):
    if request.method == "POST":
        Resume.objects.create(
            user=request.user,
            full_name=request.POST.get("full_name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            summary=request.POST.get("summary"),
            skills=request.POST.get("skills"),
            experience=request.POST.get("experience"),
            education=request.POST.get("education"),
        )

        # ✅ SUCCESS MESSAGE
        messages.success(request, "✅ Resume saved successfully!")

        return redirect("/dashboard/")

    return render(request, "resumes/create.html")
@login_required
def preview_resume(request, id):
    resume = get_object_or_404(Resume, id=id, user=request.user)

    return render(request, "resumes/preview.html", {
        "resume": resume
    })