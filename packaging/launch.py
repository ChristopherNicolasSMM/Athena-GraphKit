"""Dispatch the portable launcher using the bundled Python."""
import runpy
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
commands = {"--check": "packaging_check.py", "--cli": "gerador.py", "--mcp": "mcp_server.py"}
command = sys.argv.pop(1) if len(sys.argv) > 1 else ""
script = root / (commands.get(command) or "portal.py")
if command and command not in commands:
    raise SystemExit("Uso: iniciar_portatil [--cli | --mcp | --check]")
sys.path.insert(0, str(root))
runpy.run_path(str(script), run_name="__main__")
