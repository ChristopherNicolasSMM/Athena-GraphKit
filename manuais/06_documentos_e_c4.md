# Documentos e C4 — Athena GraphKit v1.4.4

## Criar documentação

1. Abra um projeto e crie seus diagramas.
2. Na aba **Documento Markdown**, use **Inserir diagrama** para adicionar `{{diagram:ID}}`.
3. Adicione seções com **+ Seção** ou digite Markdown normalmente.
4. Clique em **Validar referências** para identificar IDs inexistentes.
5. **Baixar .md** mantém os marcadores editáveis. **Exportar documentação** gera o pacote com imagens PNG.

## Estrutura de exportação

- `documento_athena.md`: Markdown com imagens relativas.
- `imagens/`: PNG dos diagramas utilizados.
- `manifest.json`: projeto, tema, IDs e caminhos de imagens.
- `README.txt`: instruções de utilização do pacote Markdown.

Extraia o ZIP antes de utilizar em outro editor. Mantenha a pasta de imagens ao lado do Markdown.

## C4

O construtor visual aceita os níveis C4Context, C4Container e C4Component. O Mermaid C4 é experimental e o importador do Athena cobre somente um subconjunto de instruções. Preserve no editor de código os diagramas que utilizam comandos não suportados.

## Limitações

- A geração de DOCX requer um conversor externo compatível.
- DER/MER e UML possuem formulários estruturados, não um canvas especializado.
- A renderização PNG depende da rota Flask e de CairoSVG.
