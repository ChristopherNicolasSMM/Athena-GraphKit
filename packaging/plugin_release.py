#!/usr/bin/env python3
"""Build a validated skills-only Athena plugin ZIP."""
from __future__ import annotations
import argparse
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'plugin'
SOURCES = {
 'athena-user': ['manuais/01_inicio.md','manuais/02_diagramas.md','manuais/03_exportacao_documentos.md','manuais/04_bpmn.md','manuais/05_atalhos.md','manuais/06_documentos_e_c4.md','manuais/07_mcp_e_backup.md','manuais/08_idiomas_e_temas.md','manuais/09_faq.md'],
 'athena-developer': ['AGENTS.md','docs/TECHNICAL.md','docs/KNOWLEDGE_SKILLS.md','deploy/ACCESS.md'],
 'athena-operations': ['AGENTS.md','docs/TECHNICAL.md','deploy/README.md','deploy/ACCESS.md','plugin/skills/athena-graphkit/references/mcp.md'],
 'athena-graphkit': ['docs/TECHNICAL.md','manuais/02_diagramas.md']
}
SKILL_NAME = re.compile(r'(?m)^name:\s*([a-z0-9-]+)\s*$')
SKILL_DESC = re.compile(r'(?m)^description:\s*.+$')

def validate_package(folder):
    manifest=json.loads((folder/'plugin.json').read_text(encoding='utf-8'))
    if manifest.get('$schema')!='https://agent-plugins.org/schemas/1.0.0/plugin.schema.json':
        raise ValueError('Portable Agent Plugins schema ausente')
    extension=manifest.get('extensions',{}).get('com.openai',{})
    interface=extension.get('interface',{})
    for field in ('displayName','shortDescription','longDescription','developerName','category','composerIcon','logo'):
        if not interface.get(field): raise ValueError(f'Interface sem campo {field}')
    for field in ('composerIcon','logo'):
        if not interface[field].startswith('./') or not (folder/interface[field]).is_file():
            raise ValueError(f'Asset ausente: {field}')
    if (folder/'mcp.json').exists(): raise ValueError('Pacote skills-only nao deve declarar MCP remoto')
    skills=sorted((folder/'skills').glob('*/SKILL.md'))
    if len(skills)!=4: raise ValueError('Esperadas quatro Skills')
    names=set()
    for skill in skills:
        content=skill.read_text(encoding='utf-8')
        if not content.startswith('---\n') or '\n---\n' not in content:
            raise ValueError(f'Frontmatter invalido: {skill}')
        header=content.split('\n---\n',1)[0]
        match=SKILL_NAME.search(header)
        if not match or not SKILL_DESC.search(header):
            raise ValueError(f'Nome ou descricao ausente: {skill}')
        if match.group(1)!=skill.parent.name or match.group(1) in names:
            raise ValueError(f'Nome nao corresponde ao diretorio: {skill}')
        names.add(match.group(1))
        if not (skill.parent/'references'/'bundle').is_dir():
            raise ValueError(f'Referencias autonomas ausentes: {skill}')
    onboarding=extension.get('onboardingSkill')
    if not onboarding or not onboarding.startswith('./') or not (folder/onboarding).is_file():
        raise ValueError('onboardingSkill ausente')
    return {'plugin':manifest['name'],'version':manifest['version'],'skills':sorted(names)}

def build(destination):
    with tempfile.TemporaryDirectory(prefix='athena-plugin-') as temp:
        root=Path(temp)/'athena-graphkit'
        shutil.copytree(SOURCE,root,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
        for skill,documents in SOURCES.items():
            skill_dir=root/'skills'/skill
            bundle=skill_dir/'references'/'bundle'
            bundle.mkdir(parents=True,exist_ok=True)
            for document in documents:
                source=ROOT/document
                if not source.is_file() or source.suffix.lower() not in {'.md','.py','.json','.yaml','.yml','.txt'}:
                    raise FileNotFoundError(f'Referencia nao encontrada: {document}')
                target=bundle/document
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,target)
            with (skill_dir/'SKILL.md').open('a',encoding='utf-8') as stream:
                stream.write('\n\n## Referencias incluidas neste pacote\nQuando o repositorio nao estiver disponivel, consulte os documentos versionados em references/bundle/ desta Skill. O acesso a repositorios, arquivos externos e servidores MCP nao e automatico.\n')
        (root/'PACKAGING.md').write_text(
            '# Athena GraphKit plugin\n\nPacote de quatro Skills, com referencias autonomas. Nao contem dados de usuarios, credenciais ou conexao MCP remota. Modificacoes no projeto exigem aprovacao do arquiteto.\n',
            encoding='utf-8')
        result=validate_package(root)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
            for path in sorted(root.rglob('*')):
                if path.is_file(): archive.write(path,path.relative_to(root).as_posix())
        with zipfile.ZipFile(destination) as archive:
            names=set(archive.namelist())
            if 'plugin.json' not in names or archive.testzip() is not None:
                raise ValueError('Arquivo ZIP invalido')
            if len([p for p in names if p.endswith('/SKILL.md')])!=4:
                raise ValueError('ZIP sem quatro Skills')
        result['archive']=str(destination)
        result['bytes']=destination.stat().st_size
        return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=None)
    parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args()
    manifest=json.loads((SOURCE/'plugin.json').read_text(encoding='utf-8'))
    destination=args.output or ROOT/'dist'/('athena-graphkit-plugin-'+manifest['version']+'.zip')
    result=build(destination)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    if args.check_only: destination.unlink(missing_ok=True)

if __name__=='__main__': main()
