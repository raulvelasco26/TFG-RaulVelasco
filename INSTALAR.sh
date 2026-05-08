#!/bin/bash
# =============================================================================
# PEF AI Assistant - Instalador Linux
# Ejecutar desde terminal: bash INSTALAR.sh
# =============================================================================

APP_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  ============================================"
echo "   PEF AI Assistant - Instalador"
echo "   TFG 2025-26 - Raul Velasco"
echo "  ============================================"
echo ""

# -----------------------------------------------
# 1. Verificar Python 3.10+
# -----------------------------------------------
echo "  [1/3] Verificando Python..."

if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "  ERROR: Python no encontrado."
    echo "  Instalalo con tu gestor de paquetes:"
    echo "    Ubuntu/Debian: sudo apt install python3 python3-venv"
    echo "    Fedora:        sudo dnf install python3"
    echo "    Arch:          sudo pacman -S python"
    exit 1
fi

PY_MAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)")
PY_VER="$PY_MAJOR.$PY_MINOR"

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
    echo "  ERROR: Python $PY_VER detectado. Se necesita 3.10 o superior."
    exit 1
fi
echo "  OK - Python $PY_VER detectado"

# -----------------------------------------------
# 2. Crear venv e instalar dependencias
# -----------------------------------------------
echo ""
echo "  [2/3] Instalando dependencias (1-2 minutos)..."
cd "$APP_DIR"

# Comprobar que python3-venv está disponible
if ! $PYTHON -m venv --help &>/dev/null; then
    echo "  ERROR: Modulo venv no disponible."
    echo "  Instalalo con: sudo apt install python3-venv"
    exit 1
fi

if [ -d "venv" ]; then
    echo "  OK - Entorno virtual existente, actualizando..."
else
    $PYTHON -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip -q 2>/dev/null
pip install -r requirements.txt -q

if [ $? -ne 0 ]; then
    echo "  ERROR: Fallo al instalar dependencias."
    echo "  Comprueba tu conexion a internet e intentalo de nuevo."
    exit 1
fi
echo "  OK - Dependencias instaladas"

# -----------------------------------------------
# 3. Crear lanzador
# -----------------------------------------------
echo ""
echo "  [3/3] Creando lanzador..."

# Script de lanzamiento en la carpeta de la app
LAUNCH_SCRIPT="$APP_DIR/lanzar.sh"
cat > "$LAUNCH_SCRIPT" << LAUNCHER_SCRIPT
#!/bin/bash
APP_DIR="$APP_DIR"
cd "\$APP_DIR"

# Si ya esta corriendo, abrir el navegador y salir
if ss -tlnp 2>/dev/null | grep -q ':8501' || netstat -tlnp 2>/dev/null | grep -q ':8501'; then
    xdg-open http://localhost:8501 2>/dev/null
    exit 0
fi

source venv/bin/activate
python -m streamlit run src/app.py --browser.gatherUsageStats=false --server.headless=false &
sleep 4
xdg-open http://localhost:8501 2>/dev/null || python -m webbrowser http://localhost:8501
LAUNCHER_SCRIPT
chmod +x "$LAUNCH_SCRIPT"

# Intentar crear .desktop en el escritorio del usuario
DESKTOP="$HOME/Desktop"
[ ! -d "$DESKTOP" ] && DESKTOP="$HOME/Escritorio"

if [ -d "$DESKTOP" ]; then
    DESKTOP_FILE="$DESKTOP/pef-assistant.desktop"
    cat > "$DESKTOP_FILE" << DESKTOP_EOF
[Desktop Entry]
Name=PEF AI Assistant
Comment=Plan Economico-Financiero con IA
Exec=bash "$LAUNCH_SCRIPT"
Terminal=false
Type=Application
DESKTOP_EOF
    chmod +x "$DESKTOP_FILE"
    echo "  OK - Acceso directo creado en el escritorio"
else
    echo "  OK - Lanzador creado: lanzar.sh"
    echo "       Ejecuta con: bash lanzar.sh"
fi

# -----------------------------------------------
# Fin
# -----------------------------------------------
echo ""
echo "  ============================================"
echo "   Instalacion completada."
echo ""
echo "   Usa el icono del escritorio o ejecuta:"
echo "   bash lanzar.sh"
echo "  ============================================"
echo ""
