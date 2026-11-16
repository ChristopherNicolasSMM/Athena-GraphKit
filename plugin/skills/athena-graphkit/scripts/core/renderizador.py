from graphviz import Digraph, nohtml


def renderizar(diagrama, tema, destino, formato):
    dot = Digraph(name=destino.stem, format=formato, engine='dot')
    dot.attr('graph', rankdir=diagrama.direcao, **tema['graph'])
    dot.attr('node', **tema['node'])
    dot.attr('edge', **tema['edge'])
    nos_em_grupos = set()

    def adicionar_no(grafo, nome):
        dados = diagrama.nos[nome]
        grafo.node(nome, label=nohtml(dados['rotulo']), shape=dados['tipo'])

    for chave, grupo in diagrama.grupos.items():
        with dot.subgraph(name=f'cluster_{chave}') as sub:
            sub.attr(label=nohtml(grupo['titulo']), **tema['cluster'])
            for nome in grupo['nos']:
                if nome in nos_em_grupos:
                    raise ValueError(f'Nó {nome} pertence a mais de um subgraph')
                adicionar_no(sub, nome)
                nos_em_grupos.add(nome)
    for nome in diagrama.nos:
        if nome not in nos_em_grupos:
            adicionar_no(dot, nome)
    for origem, alvo, operador, rotulo in diagrama.arestas:
        attrs = {'label': nohtml(rotulo)} if rotulo else {}
        if operador == '---':
            attrs['dir'] = 'none'
        elif operador == '<-->':
            attrs['dir'] = 'both'
        elif operador == '<--':
            attrs['dir'] = 'back'
        elif operador == '-.->':
            attrs['style'] = 'dashed'
        elif operador == '==>':
            attrs['penwidth'] = '3'
        dot.edge(origem, alvo, **attrs)
    destino.parent.mkdir(parents=True, exist_ok=True)
    return dot.render(filename=destino.stem, directory=str(destino.parent), cleanup=True)
