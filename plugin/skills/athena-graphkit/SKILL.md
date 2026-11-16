---
name: athena-graphkit
description: Gera e estiliza diagramas de engenharia e documentação a partir de Markdown e Mermaid, com temas Dark, Corporativo e SAP Fiori. Use quando o usuário solicitar converter Mermaid em SVG, PNG ou PDF, preparar imagens para documentos Markdown ou criar fluxos de integração, sequência, arquitetura e documentação.
---

# Athena GraphKit

- Identificar o tipo Mermaid solicitado. Não afirmar que o parser Graphviz suporta `sequenceDiagram`, `erDiagram` ou `classDiagram`: esses formatos usam Mermaid.js no portal.
- Para `flowchart` compatível, executar `scripts/gerar.py` e verificar o resultado.
- Para outros tipos, utilizar renderização Mermaid suportada pelo ambiente, sem converter a sintaxe silenciosamente.
- Aplicar o tema solicitado (`dark`, `corporativo`, `sap_fiori`); na ausência, usar `dark`.
- Entregar os arquivos renderizados diretamente ao usuário.
- Para documentos Markdown, preparar Markdown com imagens PNG e preservar caminhos relativos. Não afirmar que a chamada automática entre plugins está habilitada.
- Consultar `references/compatibilidade.md` para limitações.

- Para uso MCP opcional, consultar `references/mcp.md`; não afirmar que há conexão automática com outros plugins.

## Autoria
Criador: Christopher N. S. M. Mauricio.
