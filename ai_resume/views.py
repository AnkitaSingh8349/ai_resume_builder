import json
import os
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from groq import Groq


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    return Groq(api_key=api_key)


@require_POST
@login_required
def ai_resume_improve(request):
    # ---- rate limit ----
    rate_key = f"ai_limit_{request.user.id}"
    if cache.get(rate_key, 0) >= 50:
        return JsonResponse({"error": "Too many requests"}, status=429)
    cache.set(rate_key, cache.get(rate_key, 0) + 1, timeout=60)

    # ---- parse JSON ----
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    text = (data.get("text") or "").strip()
    field = data.get("field", "general")

    if not text:
        text = "Generate professional resume content."

    PROMPTS = {
        "skills": "Generate ATS-friendly resume skills, one per line.",
        "education": "Rewrite education professionally, one entry per line.",
        "experience": "Rewrite experience using action verbs and achievements.",
        "summary": "Write a professional resume summary (3–4 lines).",
    }

    system_prompt = PROMPTS.get(field, "Rewrite resume content professionally.")

    try:
        client = get_groq_client()
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.6,
            max_tokens=200,
        )

        return JsonResponse({
            "result": completion.choices[0].message.content.strip()
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
