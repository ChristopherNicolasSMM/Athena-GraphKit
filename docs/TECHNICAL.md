# Referência técnica do Athena GraphKit Studio

Esta referência descreve o Athena GraphKit Studio 1.4.4.
Para operação, consulte o [deploy no PythonAnywhere](../deploy/README.md)
e o [modelo de acesso](../deploy/ACCESS.md).

## Execução e armazenamento

| Entrada | Configuração | Persistência |
| --- | --- | --- |
| `python portal.py` | Flask em `127.0.0.1`, autenticação habilitada, porta padrão 5000 (`ATHENA_PORT`) | SQLite em `workspace/local/athena.sqlite3` |
| `deploy/wsgi.py` | WSGI com `athena-deploy/app.json`, cookies seguros e host confiável quando configurado | SQLite no caminho absoluto de `ATHENA_DATABASE`, fora da pasta de release |
| `python gerador.py --help` | CLI do núcleo de geração | Arquivos de entrada e saída da CLI |

O Studio usa `portal.py` para as rotas, `portal/static/app.js` para o
editor e `athena_access/` para sessões, permissões e armazenamento de
projetos. Projetos legados em JSON podem ser migrados com **Importar projeto**.
As instalações local e hospedada têm contas e bases independentes.

## Layout, grade e salvamento

Cada item em `project.diagrams` guarda o layout do canvas em
`nodes[].x` e `nodes[].y`. O campo opcional `showGrid` é um booleano
por diagrama. Quando ausente em um projeto anterior, a grade aparece.
O controle **Grade** está disponível no Construtor visual para quem pode
editar o projeto.

Arrastar um elemento ou alternar a grade altera o estado no navegador.
**Salvar projeto** envia o documento inteiro ao servidor. Os parâmetros
`projeto` e `diagrama` na URL indicam o que reabrir ao recarregar.
O servidor verifica o acesso normalmente, inclusive ao abrir um link direto.
Um diagrama ausente faz o editor abrir o primeiro disponível no projeto.

| Operação | Contrato com autenticação |
| --- | --- |
| `GET /api/projects/<pid>` | Retorna o projeto e `_access.level` / `_access.revision`. |
| `PUT /api/projects/<pid>` | Salva o projeto JSON com o mesmo `id`, a revisão recebida na leitura e o cabeçalho `X-CSRF-Token` da sessão. Responde com `saved` e a nova `revision`. |

A revisão é um inteiro incrementado no SQLite após cada alteração.
Uma revisão divergente retorna HTTP 409. Recarregue os dados atuais e reconcilie
as alterações antes de repetir o salvamento. O editor atualiza a revisão após
salvar e conserva alterações feitas enquanto a requisição estava em andamento.

## Manuais no portal

O Studio lê arquivos UTF-8 de `manuais/*.md`. Use um nome de arquivo
com prefixo numérico para definir a ordem e um título H1 na primeira linha
para o menu. O FAQ está em `manuais/09_faq.md`.

| Operação | Resposta |
| --- | --- |
| `GET /api/manuals` | Objeto `manuals` com os pares `id` e `title`. O ID vem do nome do arquivo, sem a extensão. |
| `GET /api/manuals/<id>` | Objeto com `id`, Markdown original em `markdown` e HTML renderizado em `html`. Um manual inexistente retorna HTTP 404. |

O Flask renderiza os manuais com `markdown-it-py`, no modo CommonMark
com tabelas habilitadas e interpretação de HTML bruto desabilitada.
Blocos cercados de Mermaid são apresentados como exemplos de código.
A aba **Documento Markdown** do projeto tem sua própria prévia
e substitui referências de diagrama no fluxo de exportação.

## Validação local

Com o ambiente virtual ativo na raiz do repositório:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests
node --test tests_js/*.test.mjs
python portal.py
```

No navegador, mova um nó no segundo diagrama, alterne **Grade**, salve
e recarregue. Confira a seleção e o layout. Em **Manuais**, abra
**Integração MCP e backups** e **Perguntas frequentes (FAQ)** para
conferir a formatação de código e a tabela de permissões.
