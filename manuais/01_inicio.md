# Início rápido

Athena GraphKit Studio 1.4.3 permite criar e compartilhar diagramas e documentação. O mesmo Studio pode rodar localmente ou em um servidor.

## Instalação

1. Instale Python 3.11+ e Graphviz (executável `dot`).
2. No PowerShell, execute `py -m venv .venv`.
3. Ative com `.\.venv\Scripts\Activate.ps1`.
4. Instale dependências: `python -m pip install -r requirements.txt`.
5. Execute `python portal.py` e abra [o Studio local](http://127.0.0.1:5000).
6. Na tela de login, escolha **Criar conta** no primeiro acesso. Após entrar,
   o menu **Minha conta** fica no canto superior direito.

Contas e projetos locais ficam em `workspace/local/athena.sqlite3`.
Para trazer um projeto JSON anterior, use **Importar projeto** após entrar.

Para uso direto sem portal: `python gerador.py --help`.

## Interface

Escolha Português/English e Dark/Light no cabeçalho. O padrão é Dark. A paleta do diagrama (Dark, Corporativo, SAP Fiori) é independente do tema da interface.

## Minha conta e compartilhamento

- Abra **Minha conta** para ver seu perfil, consultar projetos compartilhados ou encerrar a sessão.
- Use **Compartilhamento** para abrir projetos e diagramas recebidos.
- Em um projeto próprio, abra **Permissões** para conceder acesso ao projeto inteiro ou a um diagrama específico. Escolha **Visualizar** ou **Editar** conforme a tarefa de quem vai receber o acesso.
