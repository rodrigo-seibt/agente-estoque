import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import httpx
from estoque.config import API_BASE_URL, GEMINI_MODEL

print("GOOGLE_API_KEY definida:", bool(os.getenv("GOOGLE_API_KEY")))

try:
    r = httpx.get(f"{API_BASE_URL}/health", timeout=5)
    print("API de estoque:", r.status_code, r.text)
except Exception as exc:
    print("API de estoque FALHOU:", type(exc).__name__, exc)

from estoque.llm import get_llm

try:
    t = time.perf_counter()
    resp = get_llm().invoke("Responda apenas: ok")
    print(f"Gemini OK em {time.perf_counter() - t:.1f} s:", resp.content)
except Exception as exc:
    print("Gemini FALHOU:", type(exc).__name__)
    print(str(exc)[:1500])