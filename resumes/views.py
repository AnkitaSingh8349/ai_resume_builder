import json
import re

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Resume
from .forms import ResumeForm


@require_POST
@login_required
def improve(request):
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    text = (data.get("text") or "").strip()
    field = data.get("field", "general")

    # Allow empty input (skills / education start empty)
    if not text:
        text = "Generate professional resume content."

    PROMPTS = {
        "skills": (
            "Generate a clean ATS-friendly list of professional resume skills. "
            "Each skill must be on a new line."
        ),
        "education": (
            "Rewrite the education section in a professional resume format. "
            "Each entry should be on a new line."
        ),
        "experience": (
            "Rewrite work experience using strong action verbs and achievements."
        ),
        "summary": (
            "Write a concise professional resume summary (3–4 lines)."
        ),
    }

    system_prompt = PROMPTS.get(
        field,
        "Rewrite the resume content to be professional and ATS-friendly."
    )

    try:
        result = ai_improve_text(
            text=text,
            system_prompt=system_prompt
        )
        return JsonResponse({"result": result})

    except Exception:
        return JsonResponse({"error": "AI failed"}, status=500)



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
    resume_id = request.GET.get("resume_id")
    template = request.GET.get("template")

    # SAVE INFO
    request.session["pending_resume_id"] = resume_id
    request.session["pending_template"] = template

    stripe = get_stripe()

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Premium Resume"},
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
    request.session["premium_unlocked"] = True

    resume_id = request.session.get("pending_resume_id")
    template = request.session.get("pending_template")

    if not resume_id or not template:
        return redirect("resumes:my_resumes")

    return redirect(
        f"{reverse('resumes:paid_print', args=[resume_id])}?template={template}"
    )
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Resume


@login_required
def paid_print(request, id):
    resume = get_object_or_404(Resume, id=id)

    # Get selected template (from URL or saved resume)
    template_key = request.GET.get("template", resume.template)

    # All available templates
    template_map = {
        "modern": "modern.html",
        "professional": "professional.html",
        "simple": "simple.html",
        "creative": "creative.html",
        "executive": "executive.html",
        "minimalist": "minimalist.html",
    }

    # Premium templates list
    premium_templates = ["creative", "executive", "minimalist"]

    # 🔒 Block premium templates if not paid
    if template_key in premium_templates:
        if not request.session.get("premium_unlocked"):
            return redirect("resumes:resume_preview", id=id)

    template_file = template_map.get(template_key)

    # Safety fallback
    if not template_file:
        return redirect("resumes:resume_preview", id=id)

    return render(
        request,
        "resumes/paid_print.html",
        {
            "resume": resume,
            "template_file": template_file,
        }
    )


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
def save_resume_field(request, id):
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
# DOWNLOAD PDF (WEASYPRINT – RENDER SAFE) ✅


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

    # ✅ READ template from query string
    template = request.GET.get("template", resume.template)
    template = template.strip().lower()

    template_file = template_map.get(template, "modern.html")

    return render(
        request,
        template_file,
        {
            "resume": resume,
            "is_public": True,
        },
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

