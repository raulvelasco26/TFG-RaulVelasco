# =============================================================================
# Dockerfile - PEF AI Assistant
# Empaqueta la aplicación Streamlit en un contenedor listo para usar
# =============================================================================
# Uso (desde la raíz del proyecto):
#   docker build -f installation/Dockerfile -t pef-assistant .
#   docker run -p 8501:8501 --env-file .env pef-assistant
# =============================================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="Raul Velasco Tello"
LABEL description="PEF AI Assistant - Plan Económico-Financiero con IA"
LABEL version="1.0"

# Evitar prompts interactivos durante la instalación
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema (mínimas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para cache de capas Docker)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY src/ ./src/
COPY templates/ ./templates/
COPY resources/ ./resources/
COPY .streamlit/ ./.streamlit/

# Crear directorio de salida
RUN mkdir -p output

# Exponer puerto de Streamlit
EXPOSE 8501

# Configurar salud del contenedor
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando por defecto
ENTRYPOINT ["python", "-m", "streamlit", "run", "src/app.py"]

# Argumentos por defecto de Streamlit
CMD ["--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false", \
     "--theme.primaryColor=#1B5E20"]
