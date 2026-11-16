@echo off
setlocal
cd /d "%~dp0"
set "RUNTIME=%CD%\runtime"
if not exist "%RUNTIME%\python.exe" (
    echo Runtime portatil ausente. Extraia o pacote completo.
    exit /b 1
)
set "PATH=%RUNTIME%;%RUNTIME%\Library\bin;%RUNTIME%\Scripts;%PATH%"
set "CAIROCFFI_DLL_DIRECTORIES=%RUNTIME%\Library\bin"
if not exist "%RUNTIME%\.athena-relocated" (
    "%RUNTIME%\python.exe" "%RUNTIME%\Scripts\conda-unpack-script.py"
    if errorlevel 1 exit /b 1
    type nul > "%RUNTIME%\.athena-relocated"
)
"%RUNTIME%\python.exe" packaging\launch.py %*
