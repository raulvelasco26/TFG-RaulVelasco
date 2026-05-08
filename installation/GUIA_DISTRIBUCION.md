# 📦 Guía de Distribución - PEF AI Assistant

Esta guía explica las diferentes formas de empaquetar y distribuir la aplicación para que el usuario final pueda descargarla y usarla fácilmente.

---

## 🎯 Resumen de Opciones

| Método | Dificultad usuario | Requisitos | Ideal para |
|--------|-------------------|------------|------------|
| **1. ZIP + Script** | ⭐ Baja | Python 3.10+ | Usuarios Windows |
| **2. Docker** | ⭐⭐ Media | Docker Desktop | Despliegue servidor |
| **3. Streamlit Cloud** | ⭐ Baja | Navegador | Demo / Usuarios finales |
| **4. pip install** | ⭐⭐ Media | Python 3.10+ | Desarrolladores |

---

## Opción 1: Distribución como ZIP (Recomendado para usuarios finales)

### Preparación del paquete

Crear un ZIP listo para descargar que contenga todo lo necesario:

```
PEF-Assistant-v1.0/
├── installation/
│   ├── instalar_y_ejecutar.bat    ← Doble clic para instalar + ejecutar
│   ├── Dockerfile                 ← Para despliegue Docker
│   ├── docker-compose.yml         ← Para despliegue Docker
│   └── GUIA_DISTRIBUCION.md       ← Esta guía
├── ejecutar_app.bat               ← Ejecución rápida (post-instalación)
├── INSTRUCCIONES.txt              ← Instrucciones en texto plano
├── .env.example                   ← Plantilla de configuración
├── requirements.txt               ← Dependencias Python
├── pyproject.toml                 ← Metadatos del proyecto
├── src/                           ← Código fuente
│   ├── app.py
│   ├── config.py
│   ├── components/
│   └── utils/
├── templates/                     ← Plantillas Excel
├── resources/                     ← Logo, imágenes
└── .streamlit/                    ← Configuración Streamlit
```

### Pasos para crear el ZIP:

```bash
# Desde la raíz del proyecto:
# Crear el ZIP excluyendo archivos de desarrollo
python -m zipfile -c PEF-Assistant-v1.0.zip src/ templates/ resources/ .streamlit/ requirements.txt .env.example pyproject.toml installation/ ejecutar_app.bat INSTRUCCIONES.txt
```

### Experiencia del usuario final:

1. **Descarga** el ZIP desde GitHub Releases
2. **Descomprime** en cualquier carpeta
3. **Doble clic** en `installation/instalar_y_ejecutar.bat`
4. El script:
   - ✅ Verifica Python (si no existe, abre la página de descarga)
   - ✅ Crea entorno virtual automáticamente
   - ✅ Instala todas las dependencias
   - ✅ Inicia la aplicación en el navegador
5. El usuario configura su **API key desde la sidebar** de la app
6. **Siguientes veces**: doble clic en `ejecutar_app.bat` (en la raíz)

### GitHub Releases (recomendado):

1. Ir a **GitHub → Releases → Draft a new release**
2. Tag: `v1.0.0`
3. Subir el ZIP como asset
4. El usuario descarga desde la página de releases

---

## Opción 2: Docker (Recomendado para servidores / técnicos)

### Para el usuario que tiene Docker:

```bash
# 1. Clonar o descargar el proyecto
git clone https://github.com/RaulVelasco/TFG-RaulVelasco.git
cd TFG-RaulVelasco

# 2. Configurar API key (opcional si se configura desde la app)
cp .env.example .env
# Editar .env con tu API key (opcional)

# 3. Ejecutar con Docker Compose
docker-compose -f installation/docker-compose.yml up -d

# 4. Abrir en navegador
# http://localhost:8501
```

### Para distribuir como imagen Docker:

```bash
# Construir la imagen (desde la raíz del proyecto)
docker build -f installation/Dockerfile -t pef-assistant:1.0 .

# Exportar como archivo tar
docker save pef-assistant:1.0 -o pef-assistant-v1.0-docker.tar

# El usuario carga y ejecuta:
docker load -i pef-assistant-v1.0-docker.tar
docker run -p 8501:8501 --env-file .env pef-assistant:1.0
```

---

## Opción 3: Streamlit Community Cloud (Recomendado para demo)

La forma más fácil para el usuario final: **solo necesita un navegador**.

### Pasos de despliegue:

1. **Subir código a GitHub** (ya hecho)
2. Ir a [share.streamlit.io](https://share.streamlit.io)
3. Conectar con GitHub
4. Seleccionar el repositorio `TFG-RaulVelasco`
5. Configurar:
   - **Main file path**: `src/app.py`
   - **Secrets** (API key): Añadir `OPENAI_API_KEY`
6. Deploy

### Resultado:
- URL pública tipo: `https://tu-app.streamlit.app`
- El usuario solo necesita abrir la URL
- La API key se puede configurar desde la propia interfaz de la app

---

## Opción 4: pip install (Para desarrolladores)

```bash
# Instalar desde GitHub
pip install git+https://github.com/RaulVelasco/TFG-RaulVelasco.git

# O desde un wheel local
pip install dist/pef_ai_assistant-1.0.0-py3-none-any.whl

# Ejecutar
pef-assistant
```

### Para crear el wheel:

```bash
pip install build
python -m build
# Genera dist/pef_ai_assistant-1.0.0-py3-none-any.whl
```

---

## 🔧 Mejoras adicionales recomendadas

### 1. API Key desde la interfaz (ya implementado)

La app ya permite configurar la API key de OpenAI/Anthropic desde la barra lateral de Streamlit, sin necesidad de editar archivos `.env`.

### 2. Auto-abrir navegador

El script `instalar_y_ejecutar.bat` ya incluye la apertura automática del navegador.

### 3. Verificar versión de Python

El script verifica que Python 3.10+ esté instalado y muestra un mensaje claro si no lo está.

---

## 📋 Checklist de distribución

- [ ] Probar `installation/instalar_y_ejecutar.bat` en un Windows limpio (sin Python)
- [ ] Verificar que todas las dependencias están en `requirements.txt`
- [ ] Confirmar que `.env.example` tiene instrucciones claras
- [ ] Probar el build de Docker: `docker build -f installation/Dockerfile -t pef-assistant .`
- [ ] Crear GitHub Release con el ZIP adjunto
- [ ] Verificar `INSTRUCCIONES.txt` es claro y completo
- [ ] Probar el despliegue en Streamlit Cloud

---

## 🚀 Flujo recomendado para tu TFG

Para la **defensa del TFG**, recomiendo este orden:

1. **Demo en vivo** → Streamlit Cloud (URL pública, sin instalación)
2. **Entrega al tribunal** → ZIP con `installation/instalar_y_ejecutar.bat`
3. **Código fuente** → GitHub repository público
4. **Documentación técnica** → README.md + esta guía
