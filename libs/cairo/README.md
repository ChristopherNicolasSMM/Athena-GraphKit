# Cairo portátil (Windows)

Este diretório é destinado a bibliotecas **nativas** Windows x64 do Cairo e dependências.
**As DLLs não estão incluídas nesta distribuição**: o ambiente de preparação não conseguiu acessar um repositório externo confiável. Não renomeie arquivos Linux (.so) para .dll.

## Origem recomendada

- MSYS2 UCRT64: https://packages.msys2.org/package/mingw-w64-ucrt-x86_64-cairo
- Instruções CairoSVG Windows: https://cairosvg.org/documentation/

Use o pacote `mingw-w64-ucrt-x86_64-cairo` e **todas as dependências runtime** de sua mesma distribuição e arquitetura; apenas `libcairo-2.dll` normalmente não é suficiente. Extraia as DLLs de `ucrt64/bin/` para `libs/cairo/bin/`, incluindo as DLLs transitivas exigidas. Não misture pacotes MSVCRT, UCRT64 e CLANG64. Se houver restrições corporativas, peça à TI um pacote portátil aprovado.

O Athena acrescenta `libs/cairo/bin` ao caminho de DLLs **antes** de importar CairoSVG. O portal inicia mesmo sem essas DLLs; apenas a conversão SVG→PNG (e o ZIP de documentação que dela depende) exibirá erro explicativo.

Verificação no ambiente virtual do projeto:

```powershell
.\venv\Scripts\python.exe -c "from athena_cairo import load_cairosvg; print(load_cairosvg().__version__)"
```
