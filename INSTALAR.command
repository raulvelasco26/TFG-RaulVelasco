#!/bin/bash
# =============================================================================
# PEF AI Assistant - Instalador Mac
# Doble clic en Finder para instalar.
# NOTA: la primera vez puede que macOS pida permiso en Privacidad y Seguridad.
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
    echo "  Descargalo desde: https://www.python.org/downloads/"
    open https://www.python.org/downloads/
    read -p "  Presiona Enter para salir..."
    exit 1
fi

PY_MAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)")
PY_VER="$PY_MAJOR.$PY_MINOR"

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
    echo "  ERROR: Python $PY_VER detectado. Se necesita 3.10 o superior."
    open https://www.python.org/downloads/
    read -p "  Presiona Enter para salir..."
    exit 1
fi
echo "  OK - Python $PY_VER detectado"

# -----------------------------------------------
# 2. Crear venv e instalar dependencias
# -----------------------------------------------
echo ""
echo "  [2/3] Instalando dependencias (1-2 minutos)..."
cd "$APP_DIR"

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
    read -p "  Presiona Enter para salir..."
    exit 1
fi
echo "  OK - Dependencias instaladas"

# -----------------------------------------------
# 3. Crear lanzador en el escritorio
# -----------------------------------------------
echo ""
echo "  [3/3] Creando acceso directo en el escritorio..."

DESKTOP="$HOME/Desktop"
[ ! -d "$DESKTOP" ] && DESKTOP="$HOME/Escritorio"

LAUNCHER="$DESKTOP/PEF AI Assistant.command"

cat > "$LAUNCHER" << LAUNCHER_SCRIPT
#!/bin/bash
# Lanzador PEF AI Assistant
APP_DIR="$APP_DIR"

# Si ya esta corriendo, solo abrir el navegador
if lsof -i :8501 -t &>/dev/null; then
    open http://localhost:8501
    exit 0
fi

cd "\$APP_DIR"
source venv/bin/activate
python -m streamlit run src/app.py --browser.gatherUsageStats=false --server.headless=false &
sleep 4
open http://localhost:8501
LAUNCHER_SCRIPT

chmod +x "$LAUNCHER"
echo "  OK - Lanzador creado en el escritorio"

# -----------------------------------------------
# Fin
# -----------------------------------------------
echo ""
echo "  ============================================"
echo "   Instalacion completada."
echo ""
echo "   Cierra esta ventana y haz doble clic en"
echo "   'PEF AI Assistant' del escritorio."
echo "  ============================================"
echo ""
read -p "  Presiona Enter para cerrar..."
