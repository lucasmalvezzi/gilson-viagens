@echo off
chcp 65001 > nul
echo ========================================================
echo   ✈️  FLIGHT PRICE TRACKER - INICIALIZANDO MONOLITO
echo ========================================================
echo.
echo Verificando ambiente Python...
if exist "venv\Scripts\python.exe" (
    echo Usando ambiente virtual do projeto...
    set PYTHON_EXE=venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
)

echo Abrindo aplicacao em: http://127.0.0.1:8000
echo Pressione Ctrl+C para encerrar o servidor.
echo.
%PYTHON_EXE% main.py
pause
