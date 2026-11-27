import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "5"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
# A chave GOOGLE_API_KEY NÃO é lida aqui: a biblioteca do Gemini a lê sozinha do ambiente.
