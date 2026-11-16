# Plugin Athena GraphKit — Skills para IA

Este diretório contém o manifesto `plugin.json` e quatro Skills independentes:

- `skills/athena-graphkit`: geração e exportação de diagramas;
- `skills/athena-user`: ajuda ao usuário do Studio;
- `skills/athena-developer`: compreensão do código e decisões de engenharia;
- `skills/athena-operations`: operação, hospedagem, diagnósticos e MCP.

## Instalação e compartilhamento

O conteúdo do repositório é público sob a licença MIT; a licença do software não garante publicação automática num marketplace. Para usar este pacote, instale o diretório `plugin/` pelo mecanismo **suportado pelo cliente** de IA, se houver suporte a manifestos de plugins com Skills. Alternativamente, instale uma Skill individual usando o recurso de importação de Skills desse cliente, preservando `SKILL.md`, `references/` e recursos necessários. Não existe instalador universal para ChatGPT, Codex e outros clientes.

**Importante:** as Skills consultam documentos da raiz do repositório. Para obter respostas completas sobre versão, API e manuais, disponibilize o repositório Athena GraphKit ao agente; numa distribuição isolada inclua uma cópia versionada das referências necessárias. Não forneça segredos ou banco de dados ao agente.

A Skill não instala o servidor MCP e não o conecta automaticamente. Para MCP local, instalar `requirements-mcp.txt` compatível, iniciar `mcp_server.py` por um cliente `stdio` e validar ferramentas.

## Governança

O arquivo `../AGENTS.md` define a revisão de arquitetura obrigatória. Antes de alterar arquivos, configuração ou documentação, o agente deve apresentar alternativas e impactos e pedir autorização explícita. Alterações adicionais ou deploy precisam de autorização específica.

## Teste de integridade do pacote

Na raiz do repositório:

```bash
python -m unittest tests.test_skills_manifest -v
```

Em ambientes nos quais `tests/` não seja um pacote Python, usar:

```bash
python -m unittest discover -s tests -p 'test_skills_manifest.py' -v
```

Os testes verificam a presença das Skills e a governança. Não validam automaticamente a compatibilidade do instalador de cada cliente.
