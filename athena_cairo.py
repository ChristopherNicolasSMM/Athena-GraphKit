"""Carregamento opcional de CairoSVG com DLLs portáteis Windows."""
import os
from pathlib import Path

_DLL_HANDLES = []
class CairoUnavailable(RuntimeError):
    pass

def load_cairosvg(root=None):
    root = Path(root or Path(__file__).resolve().parent)
    dll_dir = root / "libs" / "cairo" / "bin"
    if dll_dir.is_dir():
        # Windows: DLLs devem ser carregadas antes de importar cairocffi.
        os.environ["PATH"] = str(dll_dir) + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            _DLL_HANDLES.append(os.add_dll_directory(str(dll_dir)))
    try:
        import cairosvg
        return cairosvg
    except (ImportError, OSError) as exc:
        raise CairoUnavailable(
            "PNG requer CairoSVG e as DLLs Cairo compatíveis. "
            "Copie as DLLs e suas dependências para libs/cairo/bin; "
            "consulte libs/cairo/README.md. Detalhe: " + str(exc)
        ) from exc
