@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Passo 1: GitHub ===
where gh >nul 2>nul || if not exist "C:\Program Files\GitHub CLI\gh.exe" (
  echo Instalando o GitHub CLI...
  winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements
)
echo Instalando bibliotecas do Python...
python -m pip install -q requests google-auth-oauthlib google-api-python-client
python configurar.py
pause
