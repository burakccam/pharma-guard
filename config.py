import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# API Keys & URLs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLAVA_MODEL = os.getenv("LLAVA_MODEL", "llava:latest")

# Dizin Yolları
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _resolve_path(env_path, default_path):
    path = os.getenv(env_path, default_path)
    if path.startswith("./"):
        path = path[2:]
    return os.path.join(BASE_DIR, path)

CHROMA_DB_DIR = _resolve_path("CHROMA_DB_DIR", "chroma_db")
CORPUS_DIR = _resolve_path("CORPUS_DIR", "data/corpus")
REPORTS_DIR = _resolve_path("REPORTS_DIR", "reports")

# Fallback Settings
USE_GEMINI_VISION_FALLBACK = True  # LLaVA (Ollama/HF) çalışmazsa Gemini API kullansın
