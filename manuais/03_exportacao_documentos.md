# Exportação para documentos Markdown

1. Crie os diagramas e verifique a prévia.
2. No documento Markdown, use `{{diagram:ID}}`, substituindo ID pelo identificador do diagrama.
3. Clique em **Exportar documentação**.
4. Extraia o ZIP com `documento_athena.md` e `imagens/`.
5. Forneça o Markdown e as imagens a ferramentas de documentação para compor documentos técnicos.

O Athena **não chama automaticamente** serviços externos. A exportação prepara os arquivos interoperáveis. O PNG é convertido pelo Flask com CairoSVG para evitar `tainted canvas`.
