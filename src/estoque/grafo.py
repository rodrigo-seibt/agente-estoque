r"""Grafo LangGraph do agente de análise de estoque.

Fluxo:
  START -> interpretar --(condicional 1)--> consultar_api | responder_conceitual
                                            | esclarecer | recusar | tratar_erro
  consultar_api --(condicional 2)--> analisar -> redigir_resposta -> END
                                  \-> tratar_erro -> END
Todos os caminhos terminam em END (encerramento controlado) e a execução
tem limite de passos (recursion_limit) como proteção extra.
"""
import json
from typing import Literal, Optional

from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .analise import classificar_estoque
from .estado import EstadoAgente
from .llm import get_llm, texto_da_resposta
from .prompts import PROMPT_CONCEITUAL, PROMPT_INTERPRETADOR, PROMPT_REDATOR
from .tools import consultar_produto

LIMITE_PASSOS = 10
TAMANHO_MAXIMO_PERGUNTA = 500


class Interpretacao(BaseModel):
    """Saída estruturada do LLM no nó 'interpretar'."""
    intencao: Literal["consulta_produto", "conceitual", "ambiguo", "fora_de_escopo"] = Field(
        description="Intenção do usuário."
    )
    codigo_produto: Optional[str] = Field(
        default=None, description="Código do produto como escrito pelo usuário, ou null."
    )
    justificativa: str = Field(description="Motivo curto da classificação.")


def _passo(estado: EstadoAgente, nome: str) -> list:
    return list(estado.get("caminho", [])) + [nome]


# ---------------------------- NÓS ----------------------------

def interpretar(estado: EstadoAgente) -> dict:
    caminho = _passo(estado, "interpretar")
    try:
        modelo = get_llm().with_structured_output(Interpretacao)
        r = modelo.invoke([("system", PROMPT_INTERPRETADOR), ("human", estado["pergunta"])])
        if r is None:
            raise ValueError("O LLM não retornou uma interpretação válida.")
    except Exception as exc:
        return {
            "intencao": "erro_llm",
            "caminho": caminho,
            "resultado_api": {
                "ok": False,
                "erro": "llm_indisponivel",
                "mensagem": f"Não foi possível interpretar a pergunta ({type(exc).__name__}).",
            },
        }
    codigo = (r.codigo_produto or "").strip() or None
    return {"intencao": r.intencao, "codigo_produto": codigo, "caminho": caminho}


def consultar_api(estado: EstadoAgente) -> dict:
    resultado = consultar_produto(estado["codigo_produto"])
    return {"resultado_api": resultado, "caminho": _passo(estado, "consultar_api")}


def analisar(estado: EstadoAgente) -> dict:
    analise = classificar_estoque(estado["resultado_api"]["produto"])
    return {"analise": analise, "caminho": _passo(estado, "analisar")}


def _rodape(produto: dict, analise: dict) -> str:
    return (
        f"Dados da API: {produto['codigo']} | {produto['nome']} | "
        f"quantidade_atual={produto['quantidade_atual']} {produto['unidade']} | "
        f"estoque_minimo={produto['estoque_minimo']} | situação={analise['situacao']}"
    )


def _texto_deterministico(produto: dict, analise: dict) -> str:
    frases = {
        "esgotado": "está ESGOTADO e exige atenção imediata.",
        "baixo": "está com estoque BAIXO (no limite mínimo ou abaixo) e exige atenção.",
        "disponivel": "está com estoque disponível, acima do mínimo.",
    }
    return f"O produto {produto['nome']} ({produto['codigo']}) {frases[analise['situacao']]}"


def redigir_resposta(estado: EstadoAgente) -> dict:
    produto = estado["resultado_api"]["produto"]
    analise = estado["analise"]
    entrada = (
        f"Pergunta do usuário: {estado['pergunta']}\n\n"
        f"Produto (API): {json.dumps(produto, ensure_ascii=False)}\n\n"
        f"Análise do sistema: {json.dumps(analise, ensure_ascii=False)}"
    )
    try:
        resp = get_llm().invoke([("system", PROMPT_REDATOR), ("human", entrada)])
        texto = texto_da_resposta(resp) or _texto_deterministico(produto, analise)
    except Exception:
        # Se o LLM falhar, ainda respondemos com base nos dados reais.
        texto = _texto_deterministico(produto, analise)
    return {
        "resposta": f"{texto}\n\n{_rodape(produto, analise)}",
        "caminho": _passo(estado, "redigir_resposta"),
    }


def responder_conceitual(estado: EstadoAgente) -> dict:
    try:
        resp = get_llm().invoke([("system", PROMPT_CONCEITUAL), ("human", estado["pergunta"])])
        texto = texto_da_resposta(resp) or "Não consegui elaborar uma resposta agora."
    except Exception:
        texto = "Não consegui responder agora porque o modelo está indisponível. Tente novamente."
    return {"resposta": texto, "caminho": _passo(estado, "responder_conceitual")}


def esclarecer(estado: EstadoAgente) -> dict:
    texto = (
        "Para consultar o estoque preciso do código de UM produto no formato PRD-XXX "
        "(três dígitos), por exemplo: PRD-001. Qual código você quer consultar?"
    )
    return {"resposta": texto, "caminho": _passo(estado, "esclarecer")}


def recusar(estado: EstadoAgente) -> dict:
    texto = (
        "Só consigo consultar e analisar a situação de estoque de um produto pelo código "
        "(esgotado, baixo ou disponível) e explicar conceitos de estoque. "
        "Não realizo cadastros, alterações ou exclusões."
    )
    return {"resposta": texto, "caminho": _passo(estado, "recusar")}


def tratar_erro(estado: EstadoAgente) -> dict:
    r = estado.get("resultado_api") or {}
    erro = r.get("erro", "erro_desconhecido")
    mensagem = r.get("mensagem", "Falha sem detalhes.")
    codigo = estado.get("codigo_produto")
    if erro == "produto_nao_encontrado":
        texto = f"Não encontrei o produto {codigo} na API de estoque. Confira o código e tente de novo."
    else:
        texto = f"Não consegui concluir a consulta ({erro}). {mensagem}"
    return {"resposta": texto, "caminho": _passo(estado, "tratar_erro")}


# ------------------- TRANSIÇÕES CONDICIONAIS -------------------

def rota_apos_interpretar(estado: EstadoAgente) -> str:
    intencao = estado.get("intencao")
    if intencao == "erro_llm":
        return "tratar_erro"
    if intencao == "consulta_produto":
        return "consultar_api" if estado.get("codigo_produto") else "esclarecer"
    if intencao == "conceitual":
        return "responder_conceitual"
    if intencao == "ambiguo":
        return "esclarecer"
    return "recusar"


def rota_apos_consulta(estado: EstadoAgente) -> str:
    resultado = estado.get("resultado_api") or {}
    return "analisar" if resultado.get("ok") else "tratar_erro"


# ------------------------- MONTAGEM -------------------------

def construir_grafo():
    g = StateGraph(EstadoAgente)
    g.add_node("interpretar", interpretar)
    g.add_node("consultar_api", consultar_api)
    g.add_node("analisar", analisar)
    g.add_node("redigir_resposta", redigir_resposta)
    g.add_node("responder_conceitual", responder_conceitual)
    g.add_node("esclarecer", esclarecer)
    g.add_node("recusar", recusar)
    g.add_node("tratar_erro", tratar_erro)

    g.add_edge(START, "interpretar")
    g.add_conditional_edges(
        "interpretar",
        rota_apos_interpretar,
        {
            "consultar_api": "consultar_api",
            "responder_conceitual": "responder_conceitual",
            "esclarecer": "esclarecer",
            "recusar": "recusar",
            "tratar_erro": "tratar_erro",
        },
    )
    g.add_conditional_edges(
        "consultar_api",
        rota_apos_consulta,
        {"analisar": "analisar", "tratar_erro": "tratar_erro"},
    )
    g.add_edge("analisar", "redigir_resposta")
    for no in ("redigir_resposta", "responder_conceitual", "esclarecer", "recusar", "tratar_erro"):
        g.add_edge(no, END)
    return g.compile()


def executar_agente(pergunta: str) -> EstadoAgente:
    """Ponto de entrada: valida a entrada, roda o grafo e devolve o estado final."""
    pergunta = (pergunta or "").strip()
    if not pergunta:
        return {"pergunta": pergunta, "resposta": "Digite uma pergunta sobre o estoque.", "caminho": []}
    if len(pergunta) > TAMANHO_MAXIMO_PERGUNTA:
        return {
            "pergunta": pergunta[:50] + "...",
            "resposta": f"A pergunta excede {TAMANHO_MAXIMO_PERGUNTA} caracteres. Seja mais breve.",
            "caminho": [],
        }
    app = construir_grafo()
    try:
        return app.invoke(
            {"pergunta": pergunta, "caminho": []},
            config={"recursion_limit": LIMITE_PASSOS},
        )
    except GraphRecursionError:
        return {
            "pergunta": pergunta,
            "resposta": "A execução excedeu o limite de passos e foi interrompida.",
            "caminho": [],
        }