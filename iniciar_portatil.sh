#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
runtime="$PWD/runtime"
if [[ ! -x "$runtime/bin/python" ]]; then
    echo 'Runtime portátil ausente. Extraia o pacote completo.' >&2
    exit 1
fi
export PATH="$runtime/bin:$PATH"
export LD_LIBRARY_PATH="$runtime/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if [[ ! -f "$runtime/.athena-relocated" ]]; then
    "$runtime/bin/python" "$runtime/bin/conda-unpack"
    touch "$runtime/.athena-relocated"
fi
case "${1:-}" in
    --cli) shift; exec "$runtime/bin/python" gerador.py "$@" ;;
    --mcp) shift; exec "$runtime/bin/python" mcp_server.py "$@" ;;
    --check) exec "$runtime/bin/python" packaging_check.py ;;
    '') exec "$runtime/bin/python" portal.py ;;
    *) echo "Uso: $0 [--cli | --mcp | --check]" >&2; exit 2 ;;
esac
