# Genera dist\OrthoimagenDental.exe (app de escritorio en un solo archivo).
# Uso, desde la raíz del repositorio:
#     powershell -ExecutionPolicy Bypass -File construir_exe.ps1
# Requiere Python 3.10+ con el lanzador "py". Instala PyInstaller en un
# entorno virtual local (.venv-build) para no tocar el Python del sistema.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv-build")) {
    py -m venv .venv-build
}
& .\.venv-build\Scripts\python.exe -m pip install --quiet --upgrade pyinstaller

# Las pruebas deben pasar antes de empaquetar.
py -m unittest discover
if ($LASTEXITCODE -ne 0) { throw "Hay pruebas fallidas; no se genera el .exe." }

& .\.venv-build\Scripts\python.exe -m PyInstaller `
    --noconfirm --clean --onefile --windowed `
    --name OrthoimagenDental `
    --icon assets\orthoimagen.ico `
    --add-data "assets\orthoimagen.ico;assets" `
    app_escritorio.py

Write-Host "Listo: dist\OrthoimagenDental.exe"
