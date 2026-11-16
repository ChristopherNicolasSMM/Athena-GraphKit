"""Parser intencionalmente limitado a flowchart Mermaid comum.

Não é um interpretador completo de Mermaid. Falha explicitamente para evitar
renderizar diagramas incompletos ou semanticamente incorretos.
"""
import re
from dataclasses import dataclass, field

ID = r'[A-Za-z_][\w-]*'
NODE = re.compile(rf'^({ID})(.*)$')
SHAPES = (
    ('[(', ')]', 'cylinder'),
    ('((', '))', 'circle'),
    ('[[', ']]', 'box'),
    ('([', '])', 'oval'),
    ('[/', '/]', 'parallelogram'),
    ('{{', '}}', 'hexagon'),
    ('[', ']', 'box'),
    ('(', ')', 'ellipse'),
    ('{', '}', 'diamond'),
)
EDGE_OPERATORS = r'<-->|<--|-->|---|-\.->|==>'
EDGE = re.compile(rf'^((?:"[^"]*"|[^"])*?)\s*({EDGE_OPERATORS})\s*(?:\|([^|]*)\|\s*)?(.*?)$')
ENTITY = re.compile(r'#(35|34|60|62|38|124|96);')
DIRECT = re.compile(r'^((?:"[^"]*"|[^"])*?)\s*--\s+(.+?)\s+-->\s*(.*?)$')

@dataclass
class Diagrama:
    direcao: str
    nos: dict = field(default_factory=dict)
    arestas: list = field(default_factory=list)
    grupos: dict = field(default_factory=dict)


def parse_node(raw):
    raw = raw.strip()
    match = NODE.fullmatch(raw)
    if match:
        nome, suffix = match.groups()
        if not suffix:
            return nome, nome, 'box'
        for opening, closing, shape in SHAPES:
            if not suffix.startswith(opening) or not suffix.endswith(closing):
                continue
            label = suffix[len(opening):-len(closing)]
            if re.fullmatch(r'"[^"]*"', label):
                label = label[1:-1]
            elif re.search(r'[\[\]{}()"]', label):
                continue
            return nome, ENTITY.sub(lambda entity: chr(int(entity[1])), label), shape
    raise ValueError(f'Expressão de nó não suportada: {raw}')


def interpretar(texto):
    linhas = [(i, linha.strip()) for i, linha in enumerate(texto.splitlines(), 1)
              if linha.strip() and not linha.strip().startswith('%%')]
    if not linhas:
        raise ValueError('Diagrama vazio.')
    cab = re.fullmatch(r'(?:flowchart|graph)\s+(LR|RL|TB|TD|BT)\s*;?', linhas[0][1], re.I)
    if not cab:
        raise ValueError('A primeira linha deve ser flowchart LR/TB/RL/BT ou graph LR/TB/RL/BT.')
    direcao = {'TD': 'TB'}.get(cab.group(1).upper(), cab.group(1).upper())
    resultado = Diagrama(direcao)
    grupo_atual = None
    for numero, linha in linhas[1:]:
        linha = linha.rstrip(';').strip()
        try:
            if linha.lower().startswith('subgraph '):
                if grupo_atual is not None:
                    raise ValueError('Subgraphs aninhados não são suportados')
                titulo = linha[len('subgraph '):].strip().strip('"')
                grupo_atual = f'grupo_{len(resultado.grupos)+1}'
                resultado.grupos[grupo_atual] = {'titulo': titulo, 'nos': []}
                continue
            if linha == 'end':
                if grupo_atual is None:
                    raise ValueError('end sem subgraph')
                grupo_atual = None
                continue
            if linha.startswith(('classDef ', 'class ', 'style ', 'linkStyle ', 'click ', 'direction ')):
                raise ValueError('Diretiva Mermaid não suportada nesta versão')
            # Suporta uma conexão por linha; múltiplas conexões encadeadas são rejeitadas.
            direta = DIRECT.fullmatch(linha)
            if direta:
                esquerda, rotulo, direita = direta.groups()
                operador = '-->'
            else:
                match = EDGE.fullmatch(linha)
                if match:
                    esquerda, operador, rotulo, direita = match.groups()
                else:
                    esquerda = direita = operador = rotulo = None
            if operador:
                if re.search(EDGE_OPERATORS, re.sub(r'"[^"]*"', '', direita)):
                    raise ValueError('Conexões encadeadas não são suportadas; use uma por linha')
                origem, rot_o, tipo_o = parse_node(esquerda)
                destino, rot_d, tipo_d = parse_node(direita)
                for expressao, nome, texto_no, tipo in ((esquerda, origem, rot_o, tipo_o), (direita, destino, rot_d, tipo_d)):
                    if nome not in resultado.nos or expressao.strip() != nome:
                        resultado.nos[nome] = {'rotulo': texto_no, 'tipo': tipo}
                    if grupo_atual and nome not in resultado.grupos[grupo_atual]['nos']:
                        resultado.grupos[grupo_atual]['nos'].append(nome)
                resultado.arestas.append((origem, destino, operador, ENTITY.sub(lambda entity: chr(int(entity[1])), rotulo or '')))
            else:
                nome, rotulo, tipo = parse_node(linha)
                resultado.nos[nome] = {'rotulo': rotulo, 'tipo': tipo}
                if grupo_atual and nome not in resultado.grupos[grupo_atual]['nos']:
                    resultado.grupos[grupo_atual]['nos'].append(nome)
        except ValueError as exc:
            raise ValueError(f'Linha {numero}: {exc}') from exc
    if grupo_atual is not None:
        raise ValueError('Subgraph não foi fechado com end')
    return resultado
