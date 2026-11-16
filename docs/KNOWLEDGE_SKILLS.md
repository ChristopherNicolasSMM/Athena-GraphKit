# Athena Knowledge Skills — arquitetura documental e distribuição

As Skills são instruções para agentes compatíveis. **Não são um chatbot hospedado, nem conectam automaticamente um MCP, nem concedem acesso ao banco.**

## Catálogo
| Skill | Papel | Fonte primária |
| --- | --- | --- |
| `athena-graphkit` | Gerar diagramas/artefatos | `athena/`, `core/`, exemplos e referências da Skill |
| `athena-user` | Explicar operação do Studio | `manuais/` |
| `athena-developer` | Arquitetura, investigação, propostas e mudanças autorizadas | `docs/TECHNICAL.md` e código |
| `athena-operations` | Instalação, manutenção e incidentes | `deploy/`, `docs/TECHNICAL.md` |

## Governança
`AGENTS.md` é a instrução geral do repositório. Antes de modificar arquivos, o agente precisa apresentar decisões e alternativas ao arquiteto e aguardar **aprovação explícita**, inclusive para mudanças documentais. Para novos riscos ou mudanças de escopo, renovar aprovação. Um pedido de análise, isoladamente, não autoriza escrita.

## Fontes e atualização
- Código e testes definem o comportamento efetivo; documentação técnica detalha arquitetura e contratos.
- `manuais/` mantém a experiência do usuário; Skills roteiam e aplicam esse conhecimento.
- Revisões de interface, APIs, persistência, renderização, dependências ou deploy devem revisar documentação/Skills aplicáveis.
- Falhas de validação ou indisponibilidade de uma referência devem ser informadas, não encobertas.

## Distribuição
O manifesto `plugin/plugin.json` declara as quatro Skills; `plugin/.codex-plugin/plugin.json` serve às distribuições compatíveis. O diretório `plugin/` pode ser copiado para ambientes que aceitam este formato, preservando licença e referências. Ferramentas de cada host têm regras de instalação e publicação próprias: **estar no GitHub não significa que o plugin esteja instalado ou listado no ChatGPT**. Para distribuição autônoma, incluir no pacote as referências necessárias e verificar os caminhos relativos.

## Checklist de validação
1. Todos os caminhos declarados pelo manifesto existem e contêm `SKILL.md` com nome e descrição.
2. Frontmatter e referências Markdown estão íntegros.
3. Instruções de aprovação estão presentes no `AGENTS.md` e nas Skills de desenvolvimento e operações.
4. Testes existentes de Python/JS passam, quando afetados.
5. Links internos, versões e limitações MCP/Mermaid são revisados em cada release.
