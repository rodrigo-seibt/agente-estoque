import os
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from .config import GEMINI_MODEL

@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("GOOGLE_API_KEY não configurada. Preencha o arquivo .env.")
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, timeout=60, max_retries=2)

def texto_da_resposta(resp) -> str:
    """Extrai o texto da resposta do modelo, seja ela str ou lista de blocos."""
    conteudo = resp.content
    if isinstance(conteudo, str):
        return conteudo.strip()
    if isinstance(conteudo, list):
        partes = []
        for bloco in conteudo:
            if isinstance(bloco, str):
                partes.append(bloco)
            elif isinstance(bloco, dict) and bloco.get("type") == "text":
                partes.append(bloco.get("text", ""))
        return "".join(partes).strip()
    return str(conteudo).strip()