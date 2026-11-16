import re
from pathlib import Path

BLOCO = re.compile(r'```mermaid\s*\n(.*?)```', re.IGNORECASE | re.DOTALL)


def ler_diagramas(caminho: Path):
    texto = caminho.read_text(encoding='utf-8-sig')
    if caminho.suffix.lower() == '.mmd':
        return [texto]
    blocos = BLOCO.findall(texto)
    if not blocos:
        raise ValueError('Nenhum bloco ```mermaid encontrado.')
    return blocos
