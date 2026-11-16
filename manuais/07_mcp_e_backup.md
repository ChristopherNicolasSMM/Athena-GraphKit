# Integração MCP e backups — Athena GraphKit v1.4.3

## Backup e importação

Use **Backup ZIP** para baixar os projetos locais. **Exportar projeto** salva o JSON do projeto atual. **Importar projeto** recebe um JSON exportado; se o ID já existir, o portal cria um novo ID, preservando o original.

## Servidor MCP opcional

Instale `python -m pip install -r requirements-mcp.txt` e execute `python mcp_server.py` via cliente MCP com transporte stdio. Ferramentas: `list_themes`, `render_diagram`, `prepare_documentation`.

`render_diagram` suporta apenas flowchart/graph compatíveis com Athena Core. Para sequência, ER, classes e C4, use a prévia Mermaid.js do portal. O retorno de arquivos é em base64 e o cliente precisa decodificá-los. Não há servidor MCP remoto nem conexão automática com outro plugin.

## Segurança

O Flask continua vinculado a `127.0.0.1`. Não exponha o servidor à internet sem autenticação, TLS e limites adicionais. Evite processar SVG de origem desconhecida.
