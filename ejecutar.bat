@echo off
cd /d "%~dp0"
if not exist venv\Scripts\activate.bat (
    echo  Entorno virtual no encontrado. Ejecuta INSTALAR_Windows.bat primero.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python -m streamlit run src/app.py
