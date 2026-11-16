"""CLI do Athena GraphKit. Compatível com os parâmetros da versão 1.1."""
import argparse
import json
import sys
from pathlib import Path
from athena import AthenaGraphKit

RAIZ = Path(__file__).resolve().parent

def main():
    config = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
    cli = argparse.ArgumentParser(description="Athena GraphKit — Markdown/Mermaid para Graphviz")
    entrada = cli.add_mutually_exclusive_group()
    entrada.add_argument("--arquivo", type=Path, help="Arquivo .md ou .mmd")
    entrada.add_argument("--pasta", type=Path, help="Pasta de entrada")
    cli.add_argument("--tema", default=config["tema"])
    cli.add_argument("--formato", choices=["svg", "png", "pdf"], default=config["formato"])
    cli.add_argument("--saida", type=Path, default=RAIZ / config["saida"])
    args = cli.parse_args()
    try:
        motor = AthenaGraphKit(tema=args.tema, formato=args.formato)
        if args.arquivo:
            resultados = motor.gerar_arquivo(args.arquivo, args.saida)
        else:
            resultados = motor.gerar_pasta(args.pasta or RAIZ / config["entrada"], args.saida)
        for resultado in resultados:
            print(f"OK: {resultado.origem} -> {resultado.caminho}")
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
