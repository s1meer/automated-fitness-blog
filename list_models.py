import os
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCnJhKSKLg17LIEwFu0NAYV7-t_eHCgGF4")
client = genai.Client(api_key=GEMINI_API_KEY)

print("Listing models...")
for model in client.models.list():
    print(f"Name: {model.name}, Supported: {model.supported_actions}")
