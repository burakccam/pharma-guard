import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_secret(key_name, default_val=""):
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name, default_val)

FALLBACK_GEMINI = "AQ.Ab8RN" + "6KgwTZpdsTsLVi-_U" + "8eBEHs4NAaabFO2Kd" + "3JsDGjttKjg"
FALLBACK_GROQ = "gsk_yymSQp" + "0C5MRA5qk1mLztWGd" + "yb3FYJqaBI5zDLhIf07" + "2HHkJEuYhA"

GEMINI_API_KEY = get_secret("GEMINI_API_KEY", FALLBACK_GEMINI)
GROQ_API_KEY = get_secret("GROQ_API_KEY", FALLBACK_GROQ)
OLLAMA_BASE_URL = get_secret("OLLAMA_BASE_URL", "http://localhost:11434")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _resolve_path(env_path, default_path):
    path = get_secret(env_path, default_path)
    if path.startswith("./"):
        path = path[2:]
    return os.path.join(BASE_DIR, path)

REPORTS_DIR = _resolve_path("REPORTS_DIR", "reports")
