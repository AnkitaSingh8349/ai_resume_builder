import json
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache


# ===============================
# GROQ SAFE LOADER (FIX)
# ===============================
def get_groq_client():
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    return Groq(api_key=api_key)


# ===============================
# AI RESUME IMPROVE
# ===============================
@csrf_exempt
def ai_resume_improve(request):
    """
    Expects JSON POST: {"text": "..."}
    Returns JSON: {"result": "..."} or {"error": "..."}
    """

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    # --------------------------------------------------
    # RATE LIMIT
    # --------------------------------------------------
    user_id = request.user.id if request.user.is_authenticated else "anon"
    page = request.META.get("HTTP_REFERER", "unknown")[:50]

    rate_key = f"ai_limit_{user_id}_{page}"
    MAX_REQ_PER_MIN = 20

    current = cache.get(rate_key, 0)
    if current >= MAX_REQ_PER_MIN:
        return JsonResponse(
            {"error": "Too many AI requests. Please wait 1 minute and try again."},
            status=429
        )

    cache.set(rate_key, current + 1, timeout=60)

    # --------------------------------------------------
    # READ INPUT
    # --------------------------------------------------
    try:
        payload = json.loads(request.body)
        text = payload.get("text", "").strip()
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not text:
        return JsonResponse({"error": "Empty text"}, status=400)

    # --------------------------------------------------
    # GROQ AI CALL
    # --------------------------------------------------
    try:
        client = get_groq_client()

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional resume writer. "
                        "Rewrite the content to be concise, ATS-friendly, and professional."
                    )
                },
                {"role": "user", "content": text}
            ],
            temperature=0.6,
            max_tokens=120,
        )

        return JsonResponse({
            "result": completion.choices[0].message.content.strip()
        })

    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)
