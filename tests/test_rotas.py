import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from estoque.grafo import rota_apos_consulta, rota_apos_interpretar


@pytest.mark.parametrize(
    "estado, esperado",
    [
        ({"intencao": "consulta_produto", "codigo_produto": "PRD-001"}, "consultar_api"),
        ({"intencao": "consulta_produto", "codigo_produto": None}, "esclarecer"),
        ({"intencao": "conceitual"}, "responder_conceitual"),
        ({"intencao": "ambiguo"}, "esclarecer"),
        ({"intencao": "fora_de_escopo"}, "recusar"),
        ({"intencao": "erro_llm"}, "tratar_erro"),
    ],
)
def test_rota_apos_interpretar(estado, esperado):
    assert rota_apos_interpretar(estado) == esperado


def test_rota_apos_consulta():
    assert rota_apos_consulta({"resultado_api": {"ok": True}}) == "analisar"
    assert rota_apos_consulta({"resultado_api": {"ok": False}}) == "tratar_erro"