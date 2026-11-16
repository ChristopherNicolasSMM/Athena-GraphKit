# Mapa arquitetural

Fonte canônica: `docs/TECHNICAL.md` e o código do commit consultado.

- Entradas: `portal.py` (Flask), `gerador.py` (CLI), `mcp_server.py` (MCP local).
- Núcleo: `athena/` (API reutilizável), `core/` (interpretação/geração Graphviz).
- Interface: `portal/static/` e templates em `portal/`; prévia via Mermaid.js.
- Acesso e dados: `athena_access/`, SQLite e formato de projeto; a aplicação local e a hospedada usam bancos próprios.
- Implantação: `deploy/`; empacotamento: `packaging/`; testes: `tests/`, `tests_js/`.
- Documentos: `manuais/` (usuário), `docs/` (engenharia), `plugin/` (Skills).
- Limites: renderização Graphviz/CLI/MCP não equivale à renderização Mermaid.js. Não inventar suporte de tipos.

Antes de editar: localizar chamadas e consumidores, conferir autenticação/CSRF, testar compatibilidade e aguardar aprovação explícita.
