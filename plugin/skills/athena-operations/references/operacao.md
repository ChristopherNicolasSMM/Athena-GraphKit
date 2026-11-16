# Fluxos operacionais e diagnósticos

## Local
- Windows: `iniciar_portal.ps1` ou `python portal.py`.
- Persistência local: `workspace/local/athena.sqlite3`.
- Verificar versão do Python, ambiente virtual, Graphviz `dot`, dependências e logs.

## PythonAnywhere
- O espelho Git acompanha a branch `producao`; atualização prepara releases e venvs, faz smoke test, altera o link `current` e solicita reload do WSGI.
- Consulte `deploy/README.md`, `deploy/update.py`, `deploy/runtime.py`, `deploy/wsgi.py`.
- Configuração e banco ficam fora da release em `athena-deploy/`.
- Diagnóstico de cota: comparar o consumo de `releases/`, `venvs/`, cache pip e logs; **não apagar sem identificar release ativa e obter autorização**.

## MCP
- `mcp_server.py` disponibiliza `list_themes`, `render_diagram` e `prepare_documentation`.
- O transporte atual é `stdio`, para cliente local compatível.
- Falhas de importação devem expor traceback original; `requirements-mcp.txt` pode ter versão incompatível com API Python do servidor. Conferir versão e contratos antes de atualizar.

## Segurança e recuperação
- Nunca expor `app.json`, chaves, cookies ou dados pessoais.
- Usar backup consistente de SQLite antes de migração e alterações de dados.
- Documentar estado anterior, efeito esperado, evidência pós-mudança e rollback.
