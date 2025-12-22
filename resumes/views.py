import json
import stripe
from io import BytesIO

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from .models import Resume
from .forms import ResumeForm


# ===============================
# STRIPE CONFIG
# ===============================
stripe.api_key = settings.STRIPE_SECRET_KEY


# ===============================
# TEMPLATES
# ===============================
FREE_TEMPLATES = ["modern", "professional", "simple"]
PREMIUM_TEMPLATES = ["creative", "executive", "minimalist"]


# ==================================================
# STRIPE CHECKOUT
# ==================================================
@login_required
def create_checkout_session(request):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "Premium Resume Download",
                },
                "unit_amount": 500,
            },
            "quantity": 1,
        }],
        success_url=request.build_absolute_uri(
            reverse("resumes:payment_success")
        ),
        cancel_url=request.build_absolute_uri("/"),
    )
    return redirect(session.url)


# ==================================================
# PAYMENT SUCCESS
# ==================================================
@login_required
def payment_success(request):
    request.session["paid_for_download"] = True

    resume_id = request.session.get("pending_resume_id")
    template = request.session.get("pending_template")

    if resume_id and template:
        return redirect(
            f"{reverse('resumes:download_resume', args=[resume_id])}?template={template}"
        )

    return redirect("dashboard")


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
# ==================================================
@login_required
def edit_resume(request, id):
    resume = get_object_or_404(Resume, id=id, user=request.user)

    if request.method == "POST":
        resume.full_name = request.POST.get("full_name", "")
        resume.email = request.POST.get("email", "")
        resume.phone = request.POST.get("phone", "")
        resume.summary = request.POST.get("summary", "")
        resume.skills = request.POST.get("skills", "")
        resume.experience = request.POST.get("experience", "")
        resume.education = request.POST.get("education", "")
        resume.save()

        return redirect("resumes:resume_preview", id=resume.id)

    return render(request, "resumes/edit.html", {"resume": resume})


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
# PREVIEW RESUME
# ==================================================
def resume_preview(request, id):
    resume = get_object_or_404(Resume, id=id)

    active = request.GET.get("template") or resume.template or "modern"

    if active != resume.template:
        resume.template = active
        resume.save(update_fields=["template"])

    template_map = {
        "modern": "modern.html",
        "professional": "professional.html",
        "simple": "simple.html",
        "creative": "creative.html",
        "executive": "executive.html",
        "minimalist": "minimalist.html",
    }

    return render(
        request,
        "resumes/resume_preview.html",
        {
            "resume": resume,
            "active": active,
            "active_template": template_map.get(active, "modern.html"),
            "free_templates": FREE_TEMPLATES,
            "premium_templates": PREMIUM_TEMPLATES,
        },
    )


# ==================================================
# DOWNLOAD PDF (REPORTLAB VERSION)
# ==================================================
@login_required
def download_resume(request, id):
    resume = get_object_or_404(Resume, id=id, user=request.user)
    active = request.GET.get("template", resume.template or "modern")

    if active in PREMIUM_TEMPLATES:
        if not request.session.get("paid_for_download"):
            request.session["pending_resume_id"] = resume.id
            request.session["pending_template"] = active
            messages.warning(
                request,
                "This is a premium template. Please complete payment to download."
            )
            return redirect("resumes:checkout")

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50

    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, y, resume.full_name)
    y -= 30

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Email: {resume.email}")
    y -= 20
    p.drawString(50, y, f"Phone: {resume.phone}")
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Summary")
    y -= 20
    p.setFont("Helvetica", 11)
    p.textLine(resume.summary or "")
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Skills")
    y -= 20
    p.setFont("Helvetica", 11)
    p.textLine(resume.skills or "")
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Experience")
    y -= 20
    p.setFont("Helvetica", 11)
    p.textLine(resume.experience or "")
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Education")
    y -= 20
    p.setFont("Helvetica", 11)
    p.textLine(resume.education or "")

    p.showPage()
    p.save()

    buffer.seek(0)

    request.session.pop("paid_for_download", None)
    request.session.pop("pending_resume_id", None)
    request.session.pop("pending_template", None)

    return HttpResponse(
        buffer,
        content_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{resume.full_name}.pdf"'
        }
    )


# ==================================================
# SAVE RESUME FIELD (AJAX)
# ==================================================
@login_required
def save_resume_field(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    resume = get_object_or_404(Resume, id=id, user=request.user)

    data = json.loads(request.body)
    field = data.get("field")
    content = data.get("content")

    allowed_fields = [
        "summary",
        "skills",
        "experience",
        "education",
        "full_name",
        "email",
        "phone",
    ]

    if field not in allowed_fields:
        return JsonResponse({"error": "Invalid field"}, status=400)

    setattr(resume, field, content)
    resume.save(update_fields=[field])

    return JsonResponse({"status": "saved"})


# ==================================================
# RESUME CUSTOMIZE
# ==================================================
@login_required
def resume_customize(request, id):
    resume = get_object_or_404(Resume, id=id, user=request.user)

    if request.method == "POST":
        resume.color = request.POST.get("color")

        if request.FILES.get("photo"):
            resume.photo = request.FILES["photo"]

        resume.save()
        messages.success(request, "Customization saved successfully.")

    return render(request, "resumes/modern.html", {
        "resume": resume,
        "is_public": False
    })


# ==================================================
# PUBLIC RESUME VIEW
# ==================================================
def resume_public(request, id):
    resume = get_object_or_404(Resume, id=id)

    template_map = {
        "modern": "modern.html",
        "professional": "professional.html",
        "simple": "simple.html",
        "creative": "creative.html",
        "executive": "executive.html",
        "minimalist": "minimalist.html",
    }

    return render(
        request,
        template_map.get(resume.template, "modern.html"),
        {
            "resume": resume,
            "is_public": True
        }
    )


# ==================================================
# MY RESUMES
# ==================================================
@login_required
def my_resumes(request):
    resumes = Resume.objects.filter(user=request.user).order_by("-id")
    return render(request, "resumes/list.html", {
        "resumes": resumes
    })
