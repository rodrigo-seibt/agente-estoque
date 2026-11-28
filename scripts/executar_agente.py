import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from estoque.grafo import executar_agente


def rodar(pergunta: str) -> None:
    estado = executar_agente(pergunta)
    print(f"\n[intenção] {estado.get('intencao', '-')}")
    print(f"[caminho]  {' -> '.join(estado.get('caminho', []))}")
    print(f"\n{estado['resposta']}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        rodar(" ".join(sys.argv[1:]))
    else:
        print("Agente de estoque. Digite 'sair' para encerrar.")
        while True:
            entrada = input("\nPergunta: ").strip()
            if entrada.lower() in ("sair", "exit", "q"):
                break
            rodar(entrada)