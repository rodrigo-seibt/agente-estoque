import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from estoque.analise import classificar_estoque
from estoque.grafo import executar_agente
from estoque.notificacao import notificar_n8n
from estoque.tools import consultar_produto

USO = (
    "Uso:\n"
    '  python scripts/executar_com_n8n.py "Como está o estoque do PRD-001?"   (agente completo)\n'
    "  python scripts/executar_com_n8n.py --codigo PRD-001                    (sem LLM: tool + n8n)"
)


def estado_sem_llm(codigo: str) -> dict:
    resultado = consultar_produto(codigo)
    estado = {
        "pergunta": f"(teste sem LLM) consulta {codigo}",
        "resultado_api": resultado,
        "caminho": ["consultar_api"],
    }
    if resultado["ok"]:
        estado["analise"] = classificar_estoque(resultado["produto"])
        estado["caminho"].append("analisar")
    else:
        estado["resposta"] = resultado["mensagem"]
    return estado


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--codigo":
        estado = estado_sem_llm(sys.argv[2])
    elif len(sys.argv) >= 2:
        estado = executar_agente(" ".join(sys.argv[1:]))
    else:
        print(USO)
        sys.exit(1)

    print(f"\n[caminho] {' -> '.join(estado.get('caminho', []))}")
    print(f"\n[agente] {estado.get('resposta', '(sem resposta do LLM neste modo)')}")

    retorno = notificar_n8n(estado)
    print("\n[n8n]")
    print(json.dumps(retorno, ensure_ascii=False, indent=2))