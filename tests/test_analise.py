import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from estoque.analise import classificar_estoque


@pytest.mark.parametrize(
    "qtd, minimo, esperado",
    [
        (5, 10, "baixo"),        # PRD-001
        (40, 15, "disponivel"),  # PRD-002
        (0, 20, "esgotado"),     # PRD-004
        (30, 30, "baixo"),       # PRD-005 (no limite)
        (8, 8, "baixo"),         # PRD-009 (no limite)
    ],
)
def test_classificacao(qtd, minimo, esperado):
    produto = {"quantidade_atual": qtd, "estoque_minimo": minimo}
    assert classificar_estoque(produto)["situacao"] == esperado