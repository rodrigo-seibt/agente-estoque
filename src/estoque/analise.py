"""Regra de situação do estoque (determinística).

Decisão documentada (ela vai para o README):
  quantidade_atual == 0                      -> "esgotado"
  0 < quantidade_atual <= estoque_minimo     -> "baixo" (inclui o limite exato)
  quantidade_atual > estoque_minimo          -> "disponivel"
"""


def classificar_estoque(produto: dict) -> dict:
    qtd = produto["quantidade_atual"]
    minimo = produto["estoque_minimo"]

    if qtd == 0:
        situacao = "esgotado"
    elif qtd <= minimo:
        situacao = "baixo"
    else:
        situacao = "disponivel"

    return {
        "situacao": situacao,
        "quantidade_atual": qtd,
        "estoque_minimo": minimo,
        "diferenca": qtd - minimo,
        "exige_atencao": situacao in ("esgotado", "baixo"),
    }