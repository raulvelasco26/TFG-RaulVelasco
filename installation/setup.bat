@echo off
chcp 65001 >nul 2>&1
title PEF AI Assistant - Instalador

REM Moverse a la raiz del proyecto (un nivel arriba de installation\)
cd /d "%~dp0.."
set "APP_DIR=%CD%"

echo.
echo  ============================================
echo   PEF AI Assistant - Instalador
echo   TFG 2025-26 - Raul Velasco
echo  ============================================
echo.

REM -----------------------------------------------
REM 1. Verificar Python 3.10+
REM -----------------------------------------------
echo  [1/3] Verificando Python...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Python no encontrado.
    echo.
    echo  Instala Python 3.10 o superior desde:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANTE: marca "Add Python to PATH"
    echo  durante la instalacion.
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)
if %PY_MAJOR% LSS 3 goto :py_old
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 10 goto :py_old
goto :py_ok

:py_old
echo.
echo  ERROR: Python %PY_VER% detectado. Se necesita 3.10 o superior.
echo.
pause
exit /b 1

:py_ok
echo  OK - Python %PY_VER% detectado

REM -----------------------------------------------
REM 2. Crear venv e instalar dependencias
REM -----------------------------------------------
echo.
echo  [2/3] Instalando dependencias (1-2 minutos)...

if exist "venv\" (
    echo  OK - Entorno virtual existente, actualizando...
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo  ERROR: No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
pip install --upgrade pip --quiet >nul 2>&1
pip install -r requirements.txt --quiet

if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Fallo al instalar dependencias.
    echo  Comprueba tu conexion a internet e intentalo de nuevo.
    pause
    exit /b 1
)
echo  OK - Dependencias instaladas

REM -----------------------------------------------
REM 3. Crear acceso directo en el escritorio
REM -----------------------------------------------
echo.
echo  [3/3] Creando acceso directo en el escritorio...

set "SHORTCUT=%USERPROFILE%\Desktop\PEF AI Assistant.lnk"
set "LAUNCHER=%APP_DIR%\installation\launch.vbs"
set "ICON=%APP_DIR%\venv\Scripts\python.exe"

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%LAUNCHER%\"'; $s.WorkingDirectory = '%APP_DIR%'; $s.IconLocation = '%ICON%,0'; $s.Description = 'Abrir PEF AI Assistant'; $s.Save()"

if %errorlevel% neq 0 (
    echo  AVISO: No se pudo crear el acceso directo automaticamente.
    echo  Puedes crearlo manualmente: clic derecho en launch.vbs
    echo  y elige "Enviar a - Escritorio".
) else (
    echo  OK - Acceso directo creado en el escritorio
)

REM -----------------------------------------------
REM Fin
REM -----------------------------------------------
echo.
echo  ============================================
echo   Instalacion completada.
echo.
echo   Cierra esta ventana y haz doble clic en
echo   "PEF AI Assistant" del escritorio.
echo  ============================================
echo.
pause
