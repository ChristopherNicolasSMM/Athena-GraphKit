# Athena GraphKit — plugin de Skills para IA

Pacote publico **skills-only**, compativel com o formato portatil Agent Plugins. Inclui quatro Skills: `athena-graphkit`, `athena-user`, `athena-developer` e `athena-operations`. O pacote ZIP incorpora copias versionadas dos manuais, referencias tecnicas e regras de governanca, sem depender do checkout completo do repositório.

## Gerar e validar ZIP no Windows ou Linux

Na raiz do clone, na branch `desenvolvimento`:

```powershell
python -m unittest discover -s tests -p "test_skills_manifest.py" -v
python packaging/plugin_release.py --output dist/athena-graphkit-plugin-1.4.4.zip
```

O segundo comando valida manifestos, assets, quatro Skills, referencia de onboarding e integridade ZIP. A raiz do ZIP contem `plugin.json`, `skills/`, `assets/` e `.codex-plugin/`. Nao envie o ZIP de codigo-fonte do GitHub no lugar do ZIP construido por esse script.

Um workflow [Athena Plugin ZIP](../.github/workflows/plugin-package.yml) tambem produz o artefato de download na aba **Actions**, branch `desenvolvimento`, se a execucao do GitHub Actions estiver habilitada e for concluida com sucesso.

## Submissao ao diretorio publico ChatGPT / Codex

1. Acesse https://platform.openai.com/plugins.
2. Selecione organizacao/projeto e identidade verificada. Publicacao exige permissao de organizacao adequada.
3. Clique em **Upload new or existing plugin**, escolha o arquivo `dist/athena-graphkit-plugin-1.4.4.zip`.
4. Confira a importacao das quatro Skills, texto de listagem e imagens. Resolva problemas indicados na validacao.
5. Envie para revisao. Apos aprovacao, use **Publish plugin** para compartilhar publicamente.

Documentacao oficial: https://developers.openai.com/plugins/deploy/submission

## Limites e seguranca

- O pacote inicial **nao** inclui conexao MCP remota. O servidor local `mcp_server.py` usa `stdio` e nao fica acessivel automaticamente ao ChatGPT web.
- A publicacao de um plugin skills-only nao deve ser feita se ha intencao de adicionar posteriormente MCP remoto **ao mesmo identificador**, pois a submissao atual nao suporta acrescentar MCP a um plugin inicialmente sem MCP. Nessa situacao, planeje publicar um segundo plugin com MCP ou prepare a integracao remota antes de enviar a primeira submissao.
- O plugin nao executa alteracoes automaticamente sem autorizacao: Skills de engenharia e operacao exigem apresentar decisoes e obter a aprovacao explicita do arquiteto.
- O ZIP nao deve incluir credenciais, banco SQLite, ambiente virtual nem dados pessoais.
- Este pacote nao promove automaticamente as branches `main` ou `producao` e nao altera PythonAnywhere.
