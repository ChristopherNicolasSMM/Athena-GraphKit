---
name: athena-developer
description: Ajuda agentes de programação a compreender e evoluir a arquitetura do Athena GraphKit (Flask, Graphviz, Mermaid, SQLite, permissões, JavaScript, CLI e testes). Use para analisar código, discutir decisões, revisar bugs ou propor mudanças.
---

# Athena Developer Guide

**Regra obrigatória de governança:** antes de qualquer alteração de código, documentação, configuração, dependências ou testes, apresentar as decisões ao arquiteto, alternativas e recomendação, e perguntar se está de acordo. **Aguardar aprovação explícita antes de modificar.** Aplicar `AGENTS.md` integralmente.

## Ordem de leitura
1. `docs/TECHNICAL.md` e `references/mapa-arquitetura.md`.
2. Módulos e testes diretamente afetados; consultar código como fonte de verdade.
3. `deploy/README.md` e `deploy/ACCESS.md` se afetar autenticação ou produção.
4. Manuais e Skill do usuário quando alterar experiência funcional.

## Entrega de proposta antes de editar
Incluir: problema e evidências, alternativas (inclusive não mudar), decisão sugerida e justificativa, arquivos e contratos afetados, impacto em dados e permissões, riscos, compatibilidade, testes, migração/rollback. Perguntar: **"Você aprova essa abordagem e o escopo proposto?"**

## Implementação após aprovação
- Preservar API, formato de projetos e controle otimista de revisão.
- Manter separação entre núcleo Python, aplicação Flask, frontend e acesso.
- Cobrir testes Python e JS aplicáveis, inclusive casos de falha e regressão.
- Não misturar mudanças fora do escopo aprovado.
- Atualizar documentos, exemplos, Skills e release notes afetados.
- Relatar diffs e resultados; não fazer merge/deploy sem autorização específica.
