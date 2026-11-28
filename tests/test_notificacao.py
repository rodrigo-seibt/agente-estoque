import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from estoque.notificacao import montar_payload

PRODUTO = {
    "codigo": "PRD-001", "nome": "Mouse sem fio", "categoria": "Periféricos",
    "quantidade_atual": 5, "estoque_minimo": 10, "unidade": "un",
}
ANALISE = {
    "situacao": "baixo", "quantidade_atual": 5, "estoque_minimo": 10,
    "diferenca": -5, "exige_atencao": True,
}


def test_payload_com_analise():
    estado = {"pergunta": "x", "resultado_api": {"ok": True, "produto": PRODUTO}, "analise": ANALISE}
    p = montar_payload(estado)
    assert p["codigo"] == "PRD-001"
    assert p["situacao"] == "baixo"
    assert p["exige_atencao"] is True


def test_payload_sem_analise_retorna_none():
    assert montar_payload({"resultado_api": {"ok": False}}) is None
    assert montar_payload({}) is None