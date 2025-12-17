import requests
import os

HF_API_TOKEN = os.getenv("HF_API_TOKEN")

def improve_text(text):
    url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}"
    }

    payload = {
        "inputs": f"Improve this resume text professionally:\n{text}"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception("AI service failed")

    data = response.json()
    return data[0]["summary_text"]
