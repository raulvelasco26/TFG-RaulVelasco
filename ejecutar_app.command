#!/bin/bash
# ========================================
# Script para ejecutar PEF AI Assistant
# ========================================

echo ""
echo "=========================================="
echo " PEF AI Assistant - TFG 2025-26"
echo "=========================================="
echo ""

# Navegar al directorio del script
cd "$(dirname "$0")"

echo "[1/3] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python no está instalado o no está en PATH"
        echo "Instala Python desde: https://www.python.org/downloads/"
        read -p "Presiona Enter para salir..."
        exit 1
    fi
    PYTHON=python
else
    PYTHON=python3
fi

$PYTHON --version

echo ""
echo "[2/3] Verificando dependencias..."
$PYTHON -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "Las dependencias no están instaladas."
    echo "Instalando dependencias..."
    $PYTHON -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudieron instalar las dependencias"
        read -p "Presiona Enter para salir..."
        exit 1
    fi
fi

echo ""
echo "[3/3] Iniciando aplicación Streamlit..."
echo ""
echo "La aplicación se abrirá en tu navegador en:"
echo "> http://localhost:8501"
echo ""
echo "Para DETENER la aplicación: Presiona Ctrl+C"
echo ""
echo "=========================================="
echo ""

# Ejecutar Streamlit
$PYTHON -m streamlit run src/app.py

read -p "Presiona Enter para salir..."
