"""Envia o resultado da análise de estoque ao webhook do n8n.

O LangGraph decide e analisa; o n8n apenas reage ao resultado
(montar alerta ou mensagem normal). Esta função nunca lança exceção
para falhas previsíveis: devolve {"ok": False, "erro": ..., "mensagem": ...}.
"""
import httpx

from .config import N8N_TIMEOUT, N8N_WEBHOOK_URL


def _falha(erro: str, mensagem: str) -> dict:
    return {"ok": False, "erro": erro, "mensagem": mensagem}


def montar_payload(estado: dict) -> dict | None:
    """Monta o JSON enviado ao n8n. Devolve None se não houver análise."""
    resultado = estado.get("resultado_api") or {}
    analise = estado.get("analise")
    if not resultado.get("ok") or not analise:
        return None
    produto = resultado["produto"]
    return {
        "origem": "agente-estoque",
        "pergunta": estado.get("pergunta", ""),
        "codigo": produto["codigo"],
        "nome": produto["nome"],
        "categoria": produto["categoria"],
        "unidade": produto["unidade"],
        "quantidade_atual": analise["quantidade_atual"],
        "estoque_minimo": analise["estoque_minimo"],
        "diferenca": analise["diferenca"],
        "situacao": analise["situacao"],
        "exige_atencao": analise["exige_atencao"],
        "resposta_agente": estado.get("resposta", ""),
    }


def notificar_n8n(estado: dict) -> dict:
    if not N8N_WEBHOOK_URL:
        return _falha("n8n_nao_configurado", "Defina N8N_WEBHOOK_URL no arquivo .env.")

    payload = montar_payload(estado)
    if payload is None:
        return _falha("sem_analise", "Não há análise de estoque para enviar ao n8n.")

    try:
        resp = httpx.post(N8N_WEBHOOK_URL, json=payload, timeout=N8N_TIMEOUT)
    except (httpx.ConnectError, httpx.TimeoutException):
        return _falha("n8n_indisponivel", "Não foi possível conectar ao n8n (ou o prazo expirou).")
    except httpx.HTTPError as exc:
        return _falha("erro_http", f"Falha na requisição ao n8n: {type(exc).__name__}")

    if resp.status_code == 404:
        return _falha(
            "webhook_nao_registrado",
            "O n8n respondeu 404: no modo de teste, clique em 'Listen for test event' antes; "
            "no modo produção, publique o workflow.",
        )
    if resp.status_code != 200:
        return _falha("n8n_erro_http", f"O n8n respondeu com status {resp.status_code}.")

    try:
        dados = resp.json()
    except ValueError:
        return _falha("n8n_resposta_invalida", "O n8n não devolveu um JSON válido.")
    return {"ok": True, "resposta_n8n": dados}