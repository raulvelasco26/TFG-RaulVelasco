@echo off
REM ========================================
REM Script para ejecutar PEF AI Assistant
REM ========================================

echo.
echo ==========================================
echo  PEF AI Assistant - TFG 2025-26
echo ==========================================
echo.

REM Navegar al directorio del script
cd /d "%~dp0"

echo [1/3] Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado o no esta en PATH
    pause
    exit /b 1
)

echo.
echo [2/3] Instalando/actualizando dependencias...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

echo.
echo [3/3] Iniciando aplicacion Streamlit...
echo.
echo La aplicacion se abrira en tu navegador en:
echo ^> http://localhost:8501
echo.
echo Para DETENER la aplicacion: Presiona Ctrl+C
echo.
echo ==========================================
echo.

REM Ejecutar Streamlit
python -m streamlit run src/app.py

pause
