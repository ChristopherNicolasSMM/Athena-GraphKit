# Integração MCP e backups

## Backup e importação

Use **Backup ZIP** para baixar os projetos disponíveis na conta. **Exportar projeto** salva o JSON do projeto atual. **Importar projeto** recebe um JSON exportado; se o ID já existir, o portal cria um novo ID, preservando o original.

## Servidor MCP opcional

Instale as dependências do servidor MCP.

```bash
python -m pip install -r requirements-mcp.txt
```

Configure o cliente MCP para executar `python mcp_server.py` com transporte `stdio`. As ferramentas disponíveis são `list_themes`, `render_diagram` e `prepare_documentation`.

`render_diagram` suporta apenas flowchart/graph compatíveis com Athena Core. Para sequência, ER, classes e C4, use a prévia Mermaid.js do portal. O retorno de arquivos é em base64 e o cliente precisa decodificá-los. Não há servidor MCP remoto nem conexão automática com outro plugin.

## Segurança

Ao executar `python portal.py` localmente, o Flask escuta em `127.0.0.1`. Em um servidor, use a configuração WSGI com autenticação e HTTPS.
