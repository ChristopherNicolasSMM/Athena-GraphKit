---
name: athena-operations
description: Orienta instalação, diagnóstico, deploy PythonAnywhere, ambientes virtuais, versionamento, backups, recuperação e MCP do Athena GraphKit. Use para incidentes, configuração de Windows/Linux, hospedagem e manutenção.
---

# Athena Operations Guide

Usar `references/operacao.md`, `deploy/README.md`, `deploy/ACCESS.md` e `docs/TECHNICAL.md` como fontes, verificando a versão implantada.

## Conduta
1. Distinguir ambiente local, portátil, hospedado e cliente MCP.
2. Diagnosticar com comandos de leitura antes de alterar estado; solicitar logs mínimos e ocultar segredos.
3. Separar sintomas de causa confirmada; não afirmar que um serviço está operacional sem teste.
4. Antes de **qualquer mudança de arquivos, configuração, dependências, atualização, limpeza de disco ou deploy**, propor alternativas, riscos, plano de rollback e **solicitar aprovação explícita do arquiteto** conforme `AGENTS.md`.
5. Proteger SQLite e backups; nunca remover release ativa nem última release válida.
6. Não executar comandos destrutivos, alteração de acesso ou publicação sem autorização específica.
7. Relatar verificações, resultados e pendências.

## MCP
`mcp_server.py` usa `stdio`; não equivale a HTTP. A versão do SDK instalada precisa ser compatível com os imports efetivamente usados. Usar `python -m pip show mcp`, `python -m pip check` e teste de importação antes de recomendar mudança de dependência.
