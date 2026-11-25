"""Ferramenta de consulta de produtos na API de estoque.

Finalidade: buscar UM produto pelo código.
Parâmetro: codigo (str) no formato PRD-XXX.
Retorno: dict sempre no mesmo formato:
  {"ok": True,  "produto": {...}}
  {"ok": False, "erro": "<identificador>", "mensagem": "<texto>"}
Nunca lança exceção para falhas previsíveis: o agente decide o que fazer.
"""
import re

import httpx

from .config import API_BASE_URL, API_TIMEOUT

CODIGO_RE = re.compile(r"^PRD-[0-9]{3}$")
CAMPOS_OBRIGATORIOS = {
    "codigo": str,
    "nome": str,
    "categoria": str,
    "quantidade_atual": int,
    "estoque_minimo": int,
    "unidade": str,
}


def _falha(erro: str, mensagem: str) -> dict:
    return {"ok": False, "erro": erro, "mensagem": mensagem}


def _produto_valido(dados: object) -> bool:
    """Confere se o JSON recebido tem os campos e tipos esperados."""
    if not isinstance(dados, dict):
        return False
    for campo, tipo in CAMPOS_OBRIGATORIOS.items():
        valor = dados.get(campo)
        if not isinstance(valor, tipo) or isinstance(valor, bool):
            return False
    return True


def consultar_produto(codigo: str) -> dict:
    # 1) Validação do parâmetro ANTES de chamar a API
    if not isinstance(codigo, str):
        return _falha("codigo_invalido", "O código deve ser um texto.")
    codigo = codigo.strip().upper()
    if not CODIGO_RE.match(codigo):
        return _falha(
            "codigo_invalido",
            "Código inválido. Use o formato PRD-XXX (três dígitos), ex.: PRD-001.",
        )

    # 2) Chamada HTTP com timeout
    try:
        resp = httpx.get(f"{API_BASE_URL}/produtos/{codigo}", timeout=API_TIMEOUT)
    except (httpx.ConnectError, httpx.TimeoutException):
        return _falha(
            "api_indisponivel",
            "Não foi possível conectar à API de estoque. Verifique se ela está rodando.",
        )
    except httpx.HTTPError as exc:
        return _falha("erro_http", f"Falha na requisição: {type(exc).__name__}")

    # 3) Tratamento por status, lendo o campo "erro" quando existir
    if resp.status_code == 200:
        try:
            dados = resp.json()
        except ValueError:
            return _falha("resposta_invalida", "A API não devolveu um JSON válido.")
        if not _produto_valido(dados):
            return _falha("resposta_invalida", "O JSON recebido não tem o formato esperado.")
        return {"ok": True, "produto": dados}

    try:
        corpo = resp.json()
    except ValueError:
        corpo = {}
    erro = corpo.get("erro") if isinstance(corpo, dict) else None
    mensagem = corpo.get("mensagem") if isinstance(corpo, dict) else None

    if resp.status_code == 404:
        return _falha(erro or "produto_nao_encontrado", mensagem or "Produto não encontrado.")
    if resp.status_code == 503:
        return _falha(erro or "servico_indisponivel", mensagem or "Serviço indisponível.")
    return _falha(erro or "erro_inesperado", mensagem or f"Status HTTP {resp.status_code}.")