import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def carregar_tema(nome):
    if not nome.replace('_', '').replace('-', '').isalnum():
        raise ValueError('Nome de tema inválido')
    caminho = RAIZ / 'temas' / f'{nome}.json'
    if not caminho.is_file():
        raise ValueError(f'Tema não encontrado: {nome}')
    return json.loads(caminho.read_text(encoding='utf-8'))
