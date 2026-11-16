# Athena GraphKit no PythonAnywhere

A publicação usa o modo hospedado com login e SQLite. A execução local
ou portátil também usa login e mantém um SQLite próprio. Importe os
projetos JSON anteriores pelo Studio.

## Instalação inicial

1. Publique a revisão estável aprovada na branch `producao` no GitHub.
   No PythonAnywhere, crie uma aplicação
   **Manual configuration** na aba **Web** e selecione Python 3.12.
   Anote o caminho exato do arquivo WSGI que a aba mostra. Nos exemplos,
   substitua `SEU_USUARIO` pelo usuário real. Para Git e PythonAnywhere EU,
   use as URLs correspondentes à sua conta.
2. Na Bash Console, prepare o checkout e a configuração.

   ```bash
   cd "$HOME"
   git clone --branch producao https://github.com/ChristopherNicolasSMM/Athena-GraphKit.git
   umask 077
   mkdir -p "$HOME/athena-deploy/data"
   cp "$HOME/Athena-GraphKit/deploy/app.example.json" "$HOME/athena-deploy/app.json"
   chmod 600 "$HOME/athena-deploy/app.json"
   python3.12 -c 'import secrets; print(secrets.token_urlsafe(48))'
   command -v dot
   ```

   Edite `app.json` com a chave gerada, o domínio HTTPS, a rota absoluta
   do SQLite e, se disponível, os dados SMTP. Use o domínio sem barra em
   `ATHENA_TRUSTED_HOST`. O envio requer um SMTP alcançável pela conta
   PythonAnywhere e TLS. A porta 465 usa TLS desde a conexão. A 587 usa
   STARTTLS. Se a sua conta restringir o SMTP ou a saída de rede, escolha
   uma modalidade compatível com o provedor antes de publicar.
   O smoke test verifica `dot` e Cairo nativo na máquina. Confirme sua
   disponibilidade na imagem de sistema escolhida.

3. Substitua o conteúdo do **WSGI configuration file** pelo conteúdo de
   `deploy/wsgi.py`. O padrão é `~/athena-deploy`. Caso use outra pasta,
   ajuste `ATHENA_DEPLOY_HOME` no WSGI e use o mesmo caminho em `--base`.
   O WSGI carrega a revisão ativa ou, antes da primeira publicação, o checkout
   em `~/Athena-GraphKit`. Use `ATHENA_REPO` no WSGI se o checkout estiver em
   outro caminho. O primeiro start cria o venv se necessário e instala os
   pacotes. Os próximos starts reutilizam o ambiente pronto. Deixe o campo
   **Virtualenv** na aba **Web** vazio para que o WSGI selecione o ambiente
   da revisão. Use a mesma versão Python no painel e no atualizador.
4. Execute a primeira publicação, usando o caminho WSGI mostrado no painel.

   ```bash
   python3.12 "$HOME/Athena-GraphKit/deploy/update.py" \
     --repo "$HOME/Athena-GraphKit" \
     --base "$HOME/athena-deploy" \
     --branch producao \
     --wsgi /var/www/SEU_USUARIO_pythonanywhere_com_wsgi.py
   ```

5. Crie a primeira conta pelo terminal. A senha é solicitada de modo interativo.

   ```bash
   export ATHENA_CONFIG="$HOME/athena-deploy/app.json"
   cd "$HOME/athena-deploy/current"
   ./.venv/bin/python -m flask --app portal access user responsavel@exemplo.com
   ```

   Abra o domínio HTTPS. Você pode entrar com a conta criada no terminal
   ou usar **Criar conta** para fazer o primeiro acesso no site. O cadastro
   direto funciona sem SMTP. Se habilitar o envio, teste a recuperação com um
   endereço que você controla.

## Atualização a cada dez minutos

Na aba **Tasks**, crie uma **Always-on task** com caminhos absolutos.
O agendador comum do PythonAnywhere oferece execução horária ou diária.
A Always-on task, disponível em contas pagas, mantém o processo que
faz as verificações de dez em dez minutos.

```text
python3.12 /home/SEU_USUARIO/Athena-GraphKit/deploy/update.py --repo /home/SEU_USUARIO/Athena-GraphKit --base /home/SEU_USUARIO/athena-deploy --wsgi /var/www/SEU_USUARIO_pythonanywhere_com_wsgi.py --branch producao --watch
```

A checagem usa `git fetch`, aceita avanço direto da branch com
`git merge --ff-only` e exige checkout sem alterações locais. Com uma
nova revisão, prepara uma pasta de release, cria ou reutiliza um venv conforme
a versão do Python e o `requirements.txt`, testa com o Python desse ambiente
e troca o ponteiro `current`.
Em seguida atualiza a data do arquivo WSGI para o PythonAnywhere recarregar
os workers. Quando a revisão já está ativa, registra a verificação e
não solicita recarga. Falhas de preparação preservam a release ativa.

| Arquivo em `~/athena-deploy/logs/` | Conteúdo |
|---|---|
| `deploy.log` | Checagens, revisão preparada, recarga solicitada e falhas do atualizador. |
| `startup.log` | Revisão carregada por cada processo WSGI e erros de importação ou configuração. |
| `errors.log` | Exceções e falhas registradas pela aplicação durante as requisições. |

A recarga solicitada aparece primeiro em `deploy.log`. Confirme a
inicialização em `startup.log`, consulte os logs da aba **Web** quando
necessário e teste `/healthz` pelo endereço HTTPS. Faça backups de
`data/` com SQLite Online Backup ou com a aplicação parada.
As pastas `releases/` e `venvs/` conservam versões anteriores.
Remova revisões antigas apenas depois de confirmar a versão ativa
e preservar a revisão anterior.

## Migrar um checkout de publicação existente

Pause a Always-on task e confirme que o checkout de publicação está limpo.
Execute na Bash Console:

```bash
cd "$HOME/Athena-GraphKit"
git status --short
git fetch origin refs/heads/producao:refs/remotes/origin/producao
git switch producao
git branch --set-upstream-to=origin/producao producao
```

Execute a publicação manual do passo 4 e altere o comando da Always-on task
para usar `--branch producao` antes de iniciá-la novamente. O atualizador lê
a branch do parâmetro `--branch` e usa `main` se ele for omitido. O
`app.json` contém a configuração da aplicação. Confirme a revisão em
`readlink "$HOME/athena-deploy/current"` e consulte `deploy.log` se a branch
local estiver incorreta, tiver alterações ou divergir do remoto.

Quando `requirements.txt` muda, o runtime prepara outro venv. A dependência
`markdown-it-py` dos manuais é instalada nesse processo. Se continuar usando
um WSGI de uma instalação anterior, compare-o com `deploy/wsgi.py`.

Referências do provedor ([recarga WSGI](https://help.pythonanywhere.com/pages/ReloadWebApp/),
[Always-on tasks](https://help.pythonanywhere.com/pages/AlwaysOnTasks/) e
[tarefas agendadas](https://help.pythonanywhere.com/pages/ScheduledTasks/)).
