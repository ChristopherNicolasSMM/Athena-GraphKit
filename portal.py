"""Athena GraphKit Portal v1.4.2. Local and hosted project/document/diagram editor."""
import base64
import io
import json
import math
import os
import re
import tempfile
import threading
import uuid
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from werkzeug.exceptions import BadRequest
from flask import Flask, abort, jsonify, render_template, request, send_file
from athena import AthenaGraphKit

ROOT = Path(__file__).resolve().parent
from athena_cairo import load_cairosvg, CairoUnavailable

WORKSPACE = ROOT / 'workspace' / 'projects'
WORKSPACE.mkdir(parents=True, exist_ok=True)
app = Flask(__name__, template_folder=str(ROOT/'portal'/'templates'), static_folder=str(ROOT/'portal'/'static'))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
studio = None
PROJECT_WRITE_LOCK = threading.Lock()
THEMES = ('corporativo', 'dark', 'sap_fiori')
FORMATS = ('svg', 'png', 'pdf')
KINDS = ('flowchart', 'sequence', 'usecase', 'bpmn', 'c4', 'er', 'class')
MANUALS = ROOT / 'manuais'
MANUALS.mkdir(exist_ok=True)
DEFAULT = '''flowchart LR
    CLK[Portal de Compras] --> API[API RAP]
    API --> SAP[(SAP S/4HANA)]'''

def payload():
    data=request.get_json(silent=True)
    if not isinstance(data,dict): abort(400,'JSON inválido')
    return data

def slug(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',value): abort(400,'Identificador inválido')
    return value

def project_path(pid): return WORKSPACE / (slug(pid)+'.json')

def validate_project(p):
    if not isinstance(p,dict): abort(400,'Projeto inválido')
    slug(p.get('id'))
    title=p.get('title')
    if not isinstance(title,str) or not 1<=len(title)<=120: abort(400,'Título inválido')
    doc=p.get('markdown','')
    if not isinstance(doc,str) or len(doc)>300000: abort(400,'Markdown inválido')
    ds=p.get('diagrams',[])
    if not isinstance(ds,list) or len(ds)>100: abort(400,'Limite de 100 diagramas')
    ids=set()
    for d in ds:
        if not isinstance(d,dict): abort(400,'Diagrama inválido')
        did=slug(d.get('id'))
        if did in ids: abort(400,'IDs duplicados')
        ids.add(did)
        if d.get('kind') not in KINDS: abort(400,'Tipo inválido')
        if not isinstance(d.get('title'),str) or len(d['title'])>120: abort(400,'Nome inválido')
        if not isinstance(d.get('code'),str) or len(d['code'])>100000: abort(400,'Código inválido')
        nodes=d.get('nodes',[]); edges=d.get('edges',[])
        if not isinstance(nodes,list) or not isinstance(edges,list) or len(nodes)>300 or len(edges)>500: abort(400,'Grafo inválido')
        node_ids=set()
        for node in nodes:
            if not isinstance(node,dict): abort(400,'Nó inválido')
            nid=slug(node.get('id'))
            if nid in node_ids or not isinstance(node.get('label'),str): abort(400,'Nó inválido ou duplicado')
            node_ids.add(nid)
            for axis in ('x','y'):
                coordinate=node.get(axis)
                if type(coordinate) not in (float,int) or not -1e9<=coordinate<=1e9 or not math.isfinite(coordinate):
                    abort(400,'Coordenada inválida')
        for edge in edges:
            if not isinstance(edge,dict): abort(400,'Conexão inválida')
            if slug(edge.get('from')) not in node_ids or slug(edge.get('to')) not in node_ids:
                abort(400,'Conexão referencia nó inexistente')
            if not isinstance(edge.get('label',''),str): abort(400,'Rótulo de conexão inválido')
        if d.get('flowDirection','LR') not in ('LR','RL','TB','TD','BT'): abort(400,'Direção inválida')
    if p.get('theme','dark') not in THEMES: abort(400,'Tema inválido')
    return p

def write_project(path, project, *, create=False):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(project, stream, ensure_ascii=False, indent=2, allow_nan=False)
        with PROJECT_WRITE_LOCK:
            if create and path.exists():
                abort(409,'Projeto já existe')
            temporary.replace(path)
    except ValueError:
        abort(400,'Projeto contém números inválidos')
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def default_project(pid='exemplo'):
    return {'id':pid,'title':'Arquitetura de Integração','theme':'dark','markdown':'# Arquitetura de Integração\n\nEste documento descreve o fluxo principal.\n\n{{diagram:fluxo}}\n','diagrams':[{'id':'fluxo','title':'Integração SAP','kind':'flowchart','code':DEFAULT,'nodes':[{'id':'CLK','label':'Portal de Compras','x':45,'y':80},{'id':'API','label':'API RAP','x':285,'y':80},{'id':'SAP','label':'SAP S/4HANA','x':525,'y':80}],'edges':[{'from':'CLK','to':'API','label':''},{'from':'API','to':'SAP','label':''}]}]}

@app.get('/')
def home(): return render_template('index.html', hosted=studio is not None)

@app.get('/healthz')
def health():
    return jsonify(status='ok')

@app.get('/api/manuals')
def list_manuals():
    return jsonify({'manuals':[{'id':p.stem,'title':p.stem.replace('_',' ').title()} for p in sorted(MANUALS.glob('*.md'))]})

@app.get('/api/manuals/<manual_id>')
def read_manual(manual_id):
    path=MANUALS/(slug(manual_id)+'.md')
    if not path.is_file(): abort(404,'Manual não encontrado')
    return jsonify({'id':manual_id,'markdown':path.read_text(encoding='utf-8')})

@app.get('/api/projects')
def list_projects():
    if studio:
        projects = [{'id': p['id'], 'title': p['title']} for p in studio.list()]
        return jsonify(projects=sorted(projects, key=lambda p: p['title'].casefold()))
    projects=[]
    for p in WORKSPACE.glob('*.json'):
        try:
            d=json.loads(p.read_text(encoding='utf-8'))
            projects.append({'id':p.stem,'title':d.get('title',p.stem)})
        except (ValueError,OSError): continue
    return jsonify({'projects':sorted(projects,key=lambda p:p['title'].lower())})


@app.get('/api/projects/<pid>/download')
def download_project(pid):
    if studio:
        data = studio.get(slug(pid))
        data.pop('_access')
    else:
        path=project_path(pid)
        if not path.is_file(): abort(404,'Projeto não encontrado')
        data=validate_project(json.loads(path.read_text(encoding='utf-8')))
    return send_file(io.BytesIO(json.dumps(data,ensure_ascii=False,indent=2).encode('utf-8')),mimetype='application/json',as_attachment=True,download_name=f'{pid}.json')

@app.post('/api/projects/import')
def import_project():
    data=validate_project(payload())
    if studio:
        data.pop('_access', None)
        data['id'] = 'projeto_' + uuid.uuid4().hex
        studio.create(data)
        return jsonify(id=data['id'], title=data['title']), 201
    # Imported projects receive a new ID if the name is already taken.
    pid=slug(data['id']); path=project_path(pid)
    if path.exists():
        pid=slug(pid[:48]+'_'+uuid.uuid4().hex[:8]);path=project_path(pid)
    data['id']=pid
    write_project(path,data,create=True)
    return jsonify({'id':pid,'title':data['title']}),201

@app.get('/api/projects/backup/all')
def backup_projects():
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        if studio:
            for data in studio.list():
                z.writestr('projects/'+data['id']+'.json',json.dumps(data,ensure_ascii=False,indent=2))
        else:
            for path in sorted(WORKSPACE.glob('*.json')):
                try:
                    data=validate_project(json.loads(path.read_text(encoding='utf-8')))
                    z.writestr('projects/'+path.name,json.dumps(data,ensure_ascii=False,indent=2))
                except (BadRequest,ValueError,OSError):continue
        z.writestr('README.txt','Athena GraphKit v1.4.2 - backup de projetos JSON. Importe um projeto por vez no portal.\n')
    archive.seek(0)
    return send_file(archive,mimetype='application/zip',as_attachment=True,download_name='athena_projetos_backup.zip')

@app.post('/api/projects')
def create_project():
    data=payload()
    pid=slug(data.get('id') or ('projeto_' + uuid.uuid4().hex))
    obj=default_project(pid)
    obj['title']=str(data.get('title') or obj['title'])[:120]
    validate_project(obj)
    if studio:
        studio.create(obj)
    else:
        write_project(project_path(pid),obj,create=True)
    return jsonify(obj),201


@app.get('/api/projects/<pid>')
def get_project(pid):
    if studio:
        return jsonify(studio.get(slug(pid)))
    path=project_path(pid)
    if not path.exists(): abort(404,'Projeto não encontrado')
    return jsonify(json.loads(path.read_text(encoding='utf-8')))

@app.put('/api/projects/<pid>')
def save_project(pid):
    data=validate_project(payload())
    if data.get('id')!=pid: abort(400,'ID inconsistente')
    if studio:
        studio.save(slug(pid),data)
    else:
        write_project(project_path(pid),data)
    return jsonify({'saved':pid})

@app.delete('/api/projects/<pid>')
def delete_project(pid):
    if studio:
        studio.delete(slug(pid))
        return jsonify(deleted=pid)
    path=project_path(pid)
    if not path.exists(): abort(404,'Projeto não encontrado')
    path.unlink(); return jsonify({'deleted':pid})

def embedded_png(value):
    prefix = "data:image/png;base64,"
    if not value.startswith(prefix) or len(value) > 700_000:
        return False
    try:
        raw = base64.b64decode(value[len(prefix):], validate=True)
    except ValueError:
        return False
    if len(raw) < 33 or not raw.startswith(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"):
        return False
    width = int.from_bytes(raw[16:20], "big")
    height = int.from_bytes(raw[20:24], "big")
    return 0 < width <= 1024 and 0 < height <= 1024


def fetch_embedded_image(url, resource_type):
    if not embedded_png(url):
        raise ValueError('Recurso externo não permitido.')
    return base64.b64decode(url.split(',',1)[1], validate=True)


def svg_to_png(svg, theme='dark'):
    """Rasterize on the server, avoiding browser canvas origin restrictions.

    Reject external references and XML entities before passing content to CairoSVG.
    """
    if not isinstance(svg,str) or len(svg.encode('utf-8')) > 2_000_000:
        raise ValueError('SVG ausente ou acima de 2 MB')
    if re.search(r'<!DOCTYPE|<!ENTITY|<script\b|<iframe\b|@import|url\(\s*[\"\']?(?:https?:|file:|//)',svg,re.I):
        raise ValueError('SVG contém recurso externo ou inseguro')
    try: root=ET.fromstring(svg)
    except ET.ParseError as exc: raise ValueError('SVG XML inválido') from exc
    if root.tag != '{http://www.w3.org/2000/svg}svg':
        raise ValueError('Raiz SVG inválida')
    for element in root.iter():
        tag = element.tag.split('}')[-1].lower()
        if tag in ('script','foreignobject','iframe','object'):
            raise ValueError('SVG contém elemento não portátil')
        for key,value in element.attrib.items():
            if key not in ('href', '{http://www.w3.org/1999/xlink}href'):
                continue
            if tag == 'image' and embedded_png(value):
                continue
            if not value.startswith('#'):
                raise ValueError('Referência SVG externa ou imagem inválida')
    viewbox=root.attrib.get('viewBox','').replace(',',' ').split()
    try:
        if len(viewbox)==4:
            width,height=float(viewbox[2]),float(viewbox[3])
        else:
            width=float(re.match(r'[0-9.]+',root.attrib.get('width','1000')).group())
            height=float(re.match(r'[0-9.]+',root.attrib.get('height','600')).group())
    except (ValueError,AttributeError) as exc: raise ValueError('Dimensões SVG inválidas') from exc
    if not (0<width<=12000 and 0<height<=12000 and width*height<=20_000_000):
        raise ValueError('Dimensões SVG excedem o limite')
    scale=min(2.0,4500/max(width,height))
    try:
        cairosvg = load_cairosvg(ROOT)
        return cairosvg.surface.PNGSurface.convert(bytestring=svg.encode('utf-8'),url_fetcher=fetch_embedded_image,output_width=max(1,round(width*scale)),output_height=max(1,round(height*scale)),background_color='#0e1728' if theme=='dark' else '#ffffff')
    except CairoUnavailable as exc:
        raise ValueError('Cairo indisponível: '+str(exc)) from exc
    except Exception as exc:
        raise ValueError('Falha ao converter SVG para PNG: '+str(exc)[:180]) from exc

@app.post('/api/export/png')
def export_png():
    data=payload()
    try: binary=svg_to_png(data.get('svg'),data.get('theme','dark'))
    except ValueError as exc: return jsonify({'error':str(exc)}),422
    return send_file(io.BytesIO(binary),mimetype='image/png',as_attachment=True,download_name='athena.png')

@app.post('/api/export/documentation')
def export_documentation():
    """Receive client-rendered PNG images and produce portable MD+images ZIP."""
    data=payload(); project=validate_project(data.get('project'))
    if studio:
        studio.get(project['id'])
    images=data.get('images')
    if not isinstance(images,dict): abort(400,'Imagens ausentes')
    markdown=project.get('markdown',''); diagram_map={d['id']:d for d in project.get('diagrams',[])}
    markers=re.findall(r'\{\{diagram:([^}]+)\}\}',markdown)
    missing=sorted(set(markers)-set(diagram_map))
    if missing: abort(400,'Referências inexistentes: '+', '.join(missing))
    if len(set(markers))>100: abort(400,'Excesso de diagramas no documento')
    archive=io.BytesIO()
    manifest={'generator':'Athena GraphKit','version':'1.4.2','project':project['id'],'theme':project.get('theme','dark'),'diagrams':[]}
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for did in dict.fromkeys(markers):
            d=diagram_map[did]; image=images.get(did)
            if not isinstance(image,str) or not image.startswith('data:image/png;base64,'):
                abort(400,f'Imagem PNG ausente para {did}')
            try: raw=base64.b64decode(image.split(',',1)[1],validate=True)
            except (ValueError,base64.binascii.Error): abort(400,'Imagem inválida')
            if not raw.startswith(b'\x89PNG\r\n\x1a\n') or len(raw)>5_000_000: abort(400,'PNG inválido ou grande')
            z.writestr(f'imagens/{did}.png',raw)
            markdown=markdown.replace('{{diagram:'+did+'}}',f'![{d["title"]}](imagens/{did}.png)')
            manifest['diagrams'].append({'id':did,'title':d['title'],'kind':d['kind'],'image':f'imagens/{did}.png'})
        z.writestr('documento_athena.md',markdown)
        z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        z.writestr('README.txt','Athena GraphKit v1.4.2: documento_athena.md usa imagens/ em caminhos relativos.\nExtraia o ZIP para manter os caminhos relativos das imagens.\nOs arquivos podem ser utilizados em editores Markdown e geradores de documentos.\n')
    archive.seek(0)
    return send_file(archive,mimetype='application/zip',as_attachment=True,download_name='athena_documentacao.zip')

@app.post('/api/render')
def render_graphviz():
    data=payload(); code=data.get('content',''); theme=data.get('theme','dark'); fmt=data.get('format','svg')
    if theme not in THEMES or fmt not in FORMATS or not isinstance(code,str) or len(code)>100000: abort(400,'Parâmetros inválidos')
    if studio and code.count('\n') > 600: abort(400, 'Limite de 600 linhas no renderizador hospedado.')
    if not re.match(r'^\s*(flowchart|graph)\s+',code,re.I):
        return jsonify({'error':'Graphviz Core suporta flowchart/graph; outros tipos são renderizados via Mermaid.js no navegador.'}),422
    try:
        with tempfile.TemporaryDirectory(prefix='athena-render-') as directory:
            result=AthenaGraphKit(tema=theme,formato=fmt).gerar_texto(code,Path(directory)/'diagram')
            binary=result.caminho.read_bytes()
    except (ValueError,OSError,RuntimeError) as exc: return jsonify({'error':str(exc)}),422
    return send_file(io.BytesIO(binary),mimetype={'svg':'image/svg+xml','png':'image/png','pdf':'application/pdf'}[fmt],as_attachment=True,download_name=f'athena_{theme}.{fmt}')

@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(409)
@app.errorhandler(413)
def error(e): return jsonify({'error':getattr(e,'description',str(e))}),e.code

def configure_hosted(config, *, reset_sender=None, registration_sender=None):
    """Enable the hosted mode once, before Flask starts serving requests."""
    global studio
    from athena_access import AccessStore, Accounts
    from athena_access.admin import install_commands
    from athena_access.delivery import smtp_delivery
    from athena_access.studio import StudioProjects

    app.secret_key = config['ATHENA_SECRET_KEY']
    app.config.update(SESSION_COOKIE_SECURE=True, ACCOUNT_BRAND='Athena GraphKit',
                      ACCOUNT_LOGO='branding/athena-logo-dark.png')
    if config.get('ATHENA_TRUSTED_HOST'):
        app.config['TRUSTED_HOSTS'] = [config['ATHENA_TRUSTED_HOST']]
    database = Path(config['ATHENA_DATABASE'])
    if not database.is_absolute():
        raise ValueError('ATHENA_DATABASE precisa indicar um caminho absoluto persistente.')
    store = AccessStore(database)
    if config.get('ATHENA_ALLOW_REGISTRATION', True) is False:
        registration_sender = None
    elif registration_sender is None and reset_sender is None:
        registration_sender = smtp_delivery(config, registration=True)
    Accounts(app, store, reset_sender if reset_sender is not None else smtp_delivery(config),
             send_registration=registration_sender, public_endpoints={'health'})
    studio = StudioProjects(app, store, validate_project, slug)
    install_commands(app, store, studio)
    return app


if os.getenv('ATHENA_CONFIG'):
    with open(os.environ['ATHENA_CONFIG'], encoding='utf-8') as file:
        configure_hosted(json.load(file))


if __name__=='__main__':
    print('Athena GraphKit Portal: http://127.0.0.1:5000')
    app.run(host='127.0.0.1',port=int(os.getenv('ATHENA_PORT','5000')),debug=False)
