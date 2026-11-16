# Athena GraphKit Studio 1.4.4

## Studio

- Os atalhos **Compartilhamento** e **Permissões** seguem o estilo dos demais controles nos temas claro e escuro.
- **Salvar projeto** persiste as posições dos elementos no Construtor visual. A URL conserva o projeto e o diagrama selecionados ao recarregar.
- O botão **Grade**, ao lado dos controles de zoom, mostra ou oculta os pontos do fundo. A escolha é salva por diagrama. Projetos anteriores exibem a grade por padrão.
- O Studio aplica a revisão retornada pela API após salvar e conserva alterações feitas no navegador durante a requisição. O servidor rejeita revisões divergentes com HTTP 409.

## Manuais e documentação

- O painel **Manuais** renderiza Markdown com títulos, ênfase, listas, links, código e tabelas. O manual integrado e o FAQ documentam layout, grade, permissões e backup.
- A [referência técnica](../TECHNICAL.md) descreve a persistência, a API e a validação local.
- O [guia de deploy](../../deploy/README.md) descreve o checkout na branch `producao` e o uso de `--branch producao` no atualizador.

## Atualização

Com o ambiente virtual ativo, use `python -m pip install -r requirements.txt`
para instalar a dependência Markdown. No PythonAnywhere, o atualizador prepara
o ambiente da nova revisão e solicita a recarga do WSGI. O banco SQLite fica
no caminho persistente definido em `ATHENA_DATABASE`.
