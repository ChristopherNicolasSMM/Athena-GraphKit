"""Exercise the portable distribution without accessing an external service."""
import base64
import io
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

import portal

root = Path(__file__).resolve().parent
dot = shutil.which("dot")
if dot is None or (root / "runtime") not in Path(dot).resolve().parents:
    raise SystemExit("dot portátil indisponível")

with portal.app.test_client() as client:
    mermaid = client.get("/static/vendor/mermaid/mermaid.min.js")
    assert mermaid.status_code == 200 and len(mermaid.data) > 100_000
    for kind, signature in (("svg", b"<?xml"), ("png", b"\x89PNG"), ("pdf", b"%PDF")):
        rendered = client.post("/api/render", json={
            "content": 'flowchart TB\n A[("Dados")] <--> B("Consulta")',
            "format": kind,
        })
        assert rendered.status_code == 200 and rendered.data.startswith(signature), rendered.get_json()
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><rect width="100" height="40" fill="blue"/></svg>'
    png = client.post("/api/export/png", json={"svg": svg})
    assert png.status_code == 200 and png.data.startswith(b"\x89PNG"), png.get_json()
    doc = client.post("/api/export/documentation", json={
        "project": portal.default_project("smoke"),
        "images": {"fluxo": "data:image/png;base64," + base64.b64encode(png.data).decode("ascii")},
    })
    assert doc.status_code == 200, doc.get_json()
    with ZipFile(io.BytesIO(doc.data)) as archive:
        assert archive.testzip() is None and archive.read("imagens/fluxo.png") == png.data

print(f"OK: {sys.platform}, Mermaid local, Graphviz SVG/PNG/PDF, Cairo PNG e documentação ZIP.")
