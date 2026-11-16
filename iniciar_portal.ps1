# Athena GraphKit - inicializacao local sem privilegios de administrador
param([switch]$NoBrowser, [switch]$SkipInstall)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$venv = Join-Path $root 'venv'
$python = Join-Path $venv 'Scripts\python.exe'
$req = Join-Path $root 'requirements.txt'

function Find-Python {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return @{ Cmd = 'py'; Args = @('-3') } }
    $p = Get-Command python -ErrorAction SilentlyContinue
    if ($p) { return @{ Cmd = 'python'; Args = @() } }
    throw 'Python 3 nao encontrado. Instale/forneca Python antes de iniciar.'
}

if (!(Test-Path $python)) {
    if (Test-Path $venv) {
        throw "A pasta venv existe mas nao contem Scripts\python.exe. Renomeie-a para venv_backup e execute novamente: $venv"
    }
    $base = Find-Python
    Write-Host 'Criando ambiente virtual local venv...'
    & $base.Cmd @($base.Args) -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o venv.' }
}
Write-Host "Python do projeto: $python"
& $python -c 'import sys; print(sys.executable)'
if ($LASTEXITCODE -ne 0) { throw 'Ambiente virtual invalido.' }

if (-not $SkipInstall) {
    Write-Host 'Verificando dependencias Python...'
    & $python -c 'import importlib.metadata as m; [m.version(x) for x in ("Flask","graphviz","CairoSVG","markdown-it-py")]'
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Instalando dependencias no venv (pode exigir acesso ao PyPI)...'
        & $python -m pip install -r $req
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependencias. Verifique acesso ao PyPI ou use -SkipInstall.' }
    }
}

# DLLs nativas: PATH para subprocessos; Python faz add_dll_directory antes do CairoSVG.
$cairo = Join-Path $root 'libs\cairo\bin'
if (Test-Path $cairo) { $env:PATH = "$cairo;$env:PATH" }

$port = 5000
$url = "http://127.0.0.1:$port"
if (-not $NoBrowser) {
    $chromeCandidates = @(
      "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
      "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
      "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
    )
    $chrome = $chromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    # Abre depois que o servidor responder, em outro processo PowerShell.
    $openScript = @'
param($Target,$ChromePath)
for ($i=0; $i -lt 40; $i++) {
    try {
        $response = Invoke-WebRequest -Uri $Target -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            if ($ChromePath) { Start-Process -FilePath $ChromePath -ArgumentList $Target }
            else { Start-Process $Target }
            break
        }
    } catch { Start-Sleep -Milliseconds 500 }
}
'@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes("& { $openScript } '$url' '$chrome'"))
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @('-NoProfile','-EncodedCommand',$encoded)
}
Write-Host "Iniciando Athena GraphKit em $url (Ctrl+C para parar)"
& $python (Join-Path $root 'portal.py')
if ($LASTEXITCODE -ne 0) { throw "Portal terminou com codigo $LASTEXITCODE" }
