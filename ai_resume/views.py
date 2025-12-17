import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@csrf_exempt
def ai_resume_improve(request):
    if request.method != "POST":
        return JsonResponse({"improved_text": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        text = data.get("text", "").strip()
    except Exception:
        return JsonResponse({"improved_text": "Invalid JSON"}, status=400)

    if not text:
        text = "Write a professional resume section."

    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a professional resume writer."},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=200,
        )

        return JsonResponse({
            "improved_text": completion.choices[0].message.content.strip()
        })

    except Exception as e:
        print("GROQ ERROR:", e)
        return JsonResponse({
            "improved_text": "AI service error"
        }, status=500)
