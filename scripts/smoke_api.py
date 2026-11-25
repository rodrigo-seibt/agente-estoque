import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from estoque.analise import classificar_estoque
from estoque.tools import consultar_produto

for codigo in ["PRD-001", "PRD-004", "PRD-999", "ABC-1", "PRD-503"]:
    print(f"\n=== {codigo} ===")
    r = consultar_produto(codigo)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if r["ok"]:
        print("Análise:", classificar_estoque(r["produto"]))