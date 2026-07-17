import sys
import google.generativeai as genai
from config import GEMINI_API_KEY
print("Key:", GEMINI_API_KEY[:10])
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content("Hello")
    print(response.text)
except Exception as e:
    print("Error:", e)
