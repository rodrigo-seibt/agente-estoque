from dotenv import load_dotenv

load_dotenv()

from google import genai

client = genai.Client()  # lê GOOGLE_API_KEY do ambiente

for m in client.models.list():
    nome = (m.name or "").replace("models/", "")
    acoes = getattr(m, "supported_actions", None)
    if acoes is None or "generateContent" in acoes:
        print(nome)