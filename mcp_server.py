"""Athena GraphKit MCP server (local stdio; optional dependency: mcp)."""
import base64
import io
import json
import re
import tempfile
import zipfile
from pathlib import Path
from athena import AthenaGraphKit, __version__

THEMES = ('dark', 'corporativo', 'sap_fiori')
FORMATS = ('svg', 'png', 'pdf')

def list_themes():
    return [{'id': t, 'default': t == 'dark'} for t in THEMES]

def render_diagram(code: str, theme: str = 'dark', format: str = 'svg') -> dict:
    """Return an encoded artifact for compatible Mermaid flowcharts only."""
    if theme not in THEMES or format not in FORMATS:
        raise ValueError('Tema ou formato não suportado')
    if not isinstance(code, str) or len(code) > 100_000:
        raise ValueError('Código inválido ou muito longo')
    if not re.match(r'^\s*(flowchart|graph)\s+', code, re.I):
        raise ValueError('O motor MCP Graphviz aceita flowchart/graph; sequence, ER, UML e C4 exigem Mermaid.js no portal')
    with tempfile.TemporaryDirectory(prefix='athena_mcp_') as temp:
        artifact = AthenaGraphKit(tema=theme, formato=format).gerar_texto(code, Path(temp)/'diagram')
        raw = artifact.caminho.read_bytes()
    if len(raw) > 8_000_000:
        raise ValueError('Arquivo excede 8 MB')
    return {'filename': f'athena_{theme}.{format}', 'mime_type': {'svg':'image/svg+xml','png':'image/png','pdf':'application/pdf'}[format], 'base64':base64.b64encode(raw).decode('ascii')}

def prepare_documentation(markdown: str, images: dict[str,str]) -> dict:
    """Create portable Markdown+PNG ZIP. images maps diagram ID to PNG base64."""
    if not isinstance(markdown,str) or len(markdown)>300_000 or not isinstance(images,dict):
        raise ValueError('Parâmetros inválidos')
    markers=list(dict.fromkeys(re.findall(r'\{\{diagram:([a-zA-Z0-9_-]{1,64})\}\}',markdown)))
    if len(markers)>100:raise ValueError('Máximo de 100 diagramas')
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for did in markers:
            encoded=images.get(did)
            if not isinstance(encoded,str):raise ValueError(f'Imagem ausente: {did}')
            if encoded.startswith('data:image/png;base64,'):encoded=encoded.split(',',1)[1]
            try:raw=base64.b64decode(encoded,validate=True)
            except Exception as exc:raise ValueError(f'PNG inválido: {did}') from exc
            if not raw.startswith(b'\x89PNG\r\n\x1a\n') or len(raw)>5_000_000:
                raise ValueError(f'PNG inválido ou grande: {did}')
            z.writestr(f'imagens/{did}.png',raw)
            markdown=markdown.replace('{{diagram:'+did+'}}',f'![{did}](imagens/{did}.png)')
        z.writestr('documento_athena.md',markdown)
        z.writestr('manifest.json',json.dumps({'generator':'Athena GraphKit','version':__version__,'images':markers},ensure_ascii=False))
    return {'filename':'athena_documentacao.zip','mime_type':'application/zip','base64':base64.b64encode(archive.getvalue()).decode('ascii')}

def main():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit('Instale o MCP opcional: python -m pip install -r requirements-mcp.txt') from exc
    mcp=FastMCP('Athena GraphKit')
    mcp.tool()(list_themes)
    mcp.tool()(render_diagram)
    mcp.tool()(prepare_documentation)
    mcp.run(transport='stdio')

if __name__=='__main__':main()
