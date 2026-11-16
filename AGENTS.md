# Athena GraphKit — instruções para agentes

Este arquivo governa assistentes de IA que analisam, orientam ou propõem alterações neste repositório. A decisão arquitetural é humana.

## Fluxo obrigatório antes de qualquer modificação

1. Ler `README.md`, `docs/TECHNICAL.md` e os contratos dos módulos afetados. Consultar a Skill adequada em `plugin/skills/`.
2. Investigar o código real, identificar dependências, impacto na API, SQLite, fluxos de usuários e ambientes Windows/Linux/PythonAnywhere.
3. **Antes de modificar qualquer arquivo, apresentar ao arquiteto as decisões propostas**: objetivo, alternativas, opção recomendada, arquivos afetados, impactos de compatibilidade, riscos, plano de testes e reversão.
4. **Perguntar explicitamente se o arquiteto concorda e aguardar aprovação.** Não interpretar silêncio como autorização. A aprovação deve cobrir o escopo efetivo; novas decisões materiais exigem nova aprovação. A autorização para investigar não é autorização para editar.
5. Após aprovação, realizar somente as mudanças acordadas, com commits rastreáveis. Proteger dados de usuários, segredos, permissões e versões ativas.
6. Executar testes pertinentes, relatar o que efetivamente foi executado e o que não pôde ser validado. Não declarar sucesso sem evidência.
7. Atualizar documentação técnica, manuais, Skills, exemplos e notas de release quando mudar comportamento, configuração ou contrato.
8. Exibir resumo de diff, migrações, resultados, pendências e recomendações ao arquiteto antes de solicitar merge/deploy.

## Convenções de engenharia

- Preferir `athena/` e `core/` para lógica reutilizável; `portal/` e `portal.py` para apresentação/API; `athena_access/` para identidade/autorização.
- Evitar replicar parsers e modelos de dados. Preservar o formato de projeto e a revisão otimista (HTTP 409).
- Aplicar verificação de autorização no servidor, nunca apenas no navegador.
- Compatibilidade de renderização não é homogênea: o motor Graphviz/MCP tem subconjunto de flowchart; Mermaid.js tem outros tipos.
- Não editar dados de `workspace/` nem segredos em `athena-deploy/app.json`.
- Testes recomendados: `python -m unittest discover -s tests -v`, `node --test tests_js/*.mjs`, `python -m compileall -q .`. Confirmar padrões efetivos antes de executar.
- Não presumir que agentes possuem acesso ao navegador, ao MCP, a conectores ou ao ambiente de produção; verificar capacidades disponíveis.
- Conter ações destrutivas e alterações de produção atrás de aprovação específica.

## Roteamento de conhecimento

- Usuário e suporte: `plugin/skills/athena-user/SKILL.md`; fonte: `manuais/`.
- Arquitetura e implementação: `plugin/skills/athena-developer/SKILL.md`; fonte: `docs/TECHNICAL.md`.
- Instalação, deploy e incidentes: `plugin/skills/athena-operations/SKILL.md`; fonte: `deploy/`.
- Diagramas e exportação: `plugin/skills/athena-graphkit/SKILL.md`.

A Skill explica como trabalhar; a documentação e o código versionado são a fonte de verdade sobre o comportamento. Em conflito, verificar código/testes e comunicar discrepâncias antes de agir.

## Fluxo obrigatório de branches

O repositório mantém três branches de ciclo de vida:

1. `desenvolvimento`: destino padrão de toda alteração aprovada (código, testes, documentação, Skills e configurações versionadas). Validar nesta branch.
2. `main`: receber somente mudanças revisadas, testadas e aprovadas como versão estável. Não promover automaticamente.
3. `producao`: receber a versão estável somente quando o arquiteto solicitar explicitamente a publicação no PythonAnywhere. Nunca atualizar automaticamente em consequência de mudanças na `main`.

Sempre confirmar branch de destino antes de gravar. Branches temporárias de trabalho ou PRs, quando necessários, devem ter como destino `desenvolvimento`, jamais `main` por padrão. Não fazer merge, deploy ou movimentar refs entre estes estágios sem autorização específica.
