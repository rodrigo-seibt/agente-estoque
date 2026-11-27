from typing import Optional, TypedDict


class EstadoAgente(TypedDict, total=False):
    pergunta: str                    # entrada do usuário
    intencao: str                    # definida pelo LLM no nó "interpretar"
    codigo_produto: Optional[str]    # código extraído da pergunta
    resultado_api: Optional[dict]    # retorno da tool consultar_produto
    analise: Optional[dict]          # retorno de classificar_estoque
    resposta: str                    # resposta final ao usuário
    caminho: list                    # nós visitados (serve de evidência nos testes)