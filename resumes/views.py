from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string

import json
import pdfkit

from .models import Resume
from .forms import ResumeForm


# ==================================================
# CREATE RESUME
# ==================================================
@login_required
def create_resume(request):
    if request.method == "POST":
        resume = Resume.objects.create(
            user=request.user,
            full_name=request.POST.get("full_name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            summary=request.POST.get("summary"),
            skills=request.POST.get("skills"),
            experience=request.POST.get("experience"),
            education=request.POST.get("education"),
            template="modern",
            color="#2563eb",
        )

        messages.success(request, "Resume created successfully!")
        return redirect("resumes:resume_preview", id=resume.id)

    return render(request, "resumes/create.html")


# ==================================================
# EDIT RESUME
# =================================================
@login_required
def edit_resume(request, id):
    resume = get_object_or_404(Resume, id=id, user=request.user)

    if request.method == "POST":
        form = ResumeForm(request.POST, instance=resume)
        if form.is_valid():
            form.save()
            messages.success(request, "Resume updated successfully!")
            return redirect("resumes:resume_preview", id=resume.id)
        else:
            print("FORM ERRORS:", form.errors)
    else:
        form = ResumeForm(instance=resume)

    return render(request, "resumes/edit.html", {
        "form": form,
        "resume": resume
    })


# ==================================================
# SAVE TEMPLATE (AJAX)
# ==================================================
@login_required
def save_template(request, id):
    if request.method == "POST":
        resume = get_object_or_404(Resume, id=id, user=request.user)
        data = json.loads(request.body)

        resume.template = data.get("template", resume.template)
        resume.color = data.get("color", resume.color)
        resume.save()

        return JsonResponse({"status": "ok"})


# ==================================================
# PREVIEW RESUME (HTML)
# ==================================================

def resume_preview(request, id):
    resume = get_object_or_404(Resume, id=id)

    active = request.GET.get("template", resume.template or "modern")

    if active != resume.template:
        resume.template = active
        resume.save(update_fields=["template"])

    template_map = {
        "modern": "modern.html",
        "professional": "professional.html",
        "creative": "creative.html",
    }

    return render(
        request,
        "resumes/resume_preview.html",
        {
            "resume": resume,
            "active_template": template_map.get(active, "modern.html"),
            "active": active,
        },
    )





# ==================================================
# DOWNLOAD PDF (SAME TEMPLATE AS PREVIEW)
# ==================================================
def download_resume(request, id):
    resume = get_object_or_404(Resume, id=id)

    active = request.GET.get("template", resume.template or "modern")

    template_map = {
        "modern": "modern.html",
        "professional": "professional.html",
        "creative": "creative.html",
    }

    html = render_to_string(
        template_map[active],
        {"resume": resume}
    )

    config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    options = {
        "enable-local-file-access": "",
        "page-size": "A4",
        "encoding": "UTF-8",
        "margin-top": "10mm",
        "margin-bottom": "10mm",
        "margin-left": "10mm",
        "margin-right": "10mm",
    }

    pdf = pdfkit.from_string(
        html,
        False,
        configuration=config,
        options=options
    )

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{resume.full_name}.pdf"'
    )
    return response

# ================================
# PUBLIC RESUME VIEW (RESUME ONLY)
def resume_public(request, id):
    resume = get_object_or_404(Resume, id=id)

    template_map = {
        "modern": "modern.html",
        "professional": "professional.html",
        "creative": "creative.html",
    }

    return render(
        request,
        template_map.get(resume.template, "modern.html"),
        {"resume": resume}
    )

# ==================================================
# MY RESUMES LIST (LOGIN REQUIRED)
# ==================================================
@login_required
def my_resumes(request):
    resumes = Resume.objects.filter(user=request.user).order_by("-id")
    return render(request, "resumes/list.html", {
        "resumes": resumes
    })
