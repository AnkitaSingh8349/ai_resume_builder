import json
import re

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.template.loader import render_to_string

from playwright.sync_api import sync_playwright

from .models import Resume
from .forms import ResumeForm
from django.template import TemplateDoesNotExist


# ===============================
# STRIPE SAFE LOADER
# ===============================
def get_stripe():
    if not settings.STRIPE_SECRET_KEY:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")

    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


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
    stripe = get_stripe()

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
    resume, created = Resume.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.get_full_name() or "",
            "email": request.user.email or "",
            "phone": "",
            "skills": "",
            "education": "",
            "experience": "",
            "template": "modern",
            "color": "#2563eb",
        }
    )

    return render(request, "resumes/create.html", {
        "resume": resume
    })


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
# DOWNLOAD PDF (PLAYWRIGHT ONLY)
# ==================================================
@login_required
def download_resume(request, id):
    resume = get_object_or_404(Resume, id=id, user=request.user)

    FREE_TEMPLATES = ["modern", "simple", "professional"]
    PREMIUM_TEMPLATES = ["creative", "executive", "minimalist"]

    template = request.GET.get("template") or resume.template or "simple"
    template = template.strip().lower()

    # ===============================
    # 🔒 PREMIUM CHECK
    # ===============================
    if template in PREMIUM_TEMPLATES:
        if not request.session.get("paid_for_download"):
            # Save pending download info
            request.session["pending_resume_id"] = resume.id
            request.session["pending_template"] = template

            # Redirect to Stripe Checkout
            return redirect(reverse("resumes:checkout"))

        # Payment used once → reset
        request.session.pop("paid_for_download", None)

    # ===============================
    # PDF GENERATION
    # ===============================
    try:
        html = render_to_string(
            f"{template}.html",
            {
                "resume": resume,
                "is_public": True,
                "STATIC_URL": request.build_absolute_uri(settings.STATIC_URL),
            }
        )
    except TemplateDoesNotExist:
        return HttpResponse(
            f"Resume template '{template}' not found.",
            status=404
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        pdf = page.pdf(format="A4", print_background=True)
        browser.close()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{resume.full_name or "resume"}.pdf"'
    )
    return response


# ==================================================
# SAVE RESUME FIELD (AJAX)
# ==================================================
@login_required
def save_resume_field(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    resume = get_object_or_404(Resume, id=id, user=request.user)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    field = data.get("field")
    content = data.get("content", "")

    allowed_fields = [
        "skills",
        "education",
        "experience",
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
