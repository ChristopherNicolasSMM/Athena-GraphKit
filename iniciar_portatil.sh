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
exec "$runtime/bin/python" packaging/launch.py "$@"
