$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = if (Test-Path ".venv/Scripts/python.exe") { ".venv/Scripts/python.exe" } else { "python" }
& $python gerador.py @args
exit $LASTEXITCODE
