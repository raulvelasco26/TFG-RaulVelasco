# Guía de Distribución - PEF AI Assistant

Esta guía explica cómo generar el paquete de distribución y las diferentes formas de desplegar la aplicación.

---

## Resumen de opciones

| Método | Dificultad usuario | Requisitos | Ideal para |
|--------|-------------------|------------|------------|
| **1. ZIP** | Baja | Python 3.10+ | Cualquier usuario final |
| **2. Docker** | Media | Docker Desktop | Servidores / técnicos |
| **3. Streamlit Cloud** | Ninguna | Navegador | Demo online |

---

## Opción 1: ZIP (Recomendado para usuarios finales)

### Generar el ZIP

Desde PowerShell en la raíz del proyecto:

```powershell
.\installation\crear_distribucion.ps1
# Genera: PEF-AI-Assistant-v1.0.zip (≈18 MB)
```

### Contenido del ZIP

```
PEF-AI-Assistant-v1.0/
├── INSTALAR.bat         <- Windows: doble clic
├── INSTALAR.command     <- Mac:     doble clic en Finder
├── INSTALAR.sh          <- Linux:   bash INSTALAR.sh
├── installation/
│   ├── setup.bat        <- lógica de instalación Windows
│   ├── launch.vbs       <- lanzador silencioso Windows
│   └── INSTRUCCIONES.txt
├── src/
├── templates/
├── resources/
├── .streamlit/
└── requirements.txt
```

### Experiencia del usuario final

1. Descarga y descomprime el ZIP
2. Ejecuta el instalador de su SO (ver arriba)
3. El instalador:
   - Verifica Python 3.10+ (si no existe, abre la página de descarga)
   - Crea un entorno virtual aislado (`venv/`) — no toca el sistema
   - Instala todas las dependencias
   - Crea el icono "PEF AI Assistant" en el escritorio
4. Desde ese momento: doble clic en el icono → navegador abre con la app

### Publicar en GitHub Releases

1. Ir a **GitHub → Releases → Draft a new release**
2. Tag: `v1.0.0`
3. Subir `PEF-AI-Assistant-v1.0.zip` como asset
4. El usuario descarga directamente (18 MB, no el repositorio completo)

---

## Opción 2: Docker

### Usuario con Docker instalado

```bash
git clone <repositorio>
cd TFG-RaulVelasco
docker-compose -f installation/docker-compose.yml up -d
# Abrir: http://localhost:8501
```

### Distribuir como imagen

```bash
# Construir (desde la raíz del proyecto)
docker build -f installation/Dockerfile -t pef-assistant:1.0 .

# Exportar
docker save pef-assistant:1.0 -o pef-assistant-v1.0-docker.tar

# El usuario carga y ejecuta
docker load -i pef-assistant-v1.0-docker.tar
docker run -p 8501:8501 pef-assistant:1.0
```

---

## Opción 3: Streamlit Community Cloud

El usuario solo necesita una URL, sin instalación.

1. Subir el código a GitHub
2. Ir a [share.streamlit.io](https://share.streamlit.io)
3. Conectar el repositorio y configurar:
   - **Main file path**: `src/app.py`
   - **Secrets**: añadir la API key desde el panel de Streamlit Cloud
4. Deploy → URL pública lista en minutos

---

## Checklist antes de distribuir

- [ ] Ejecutar `.\installation\crear_distribucion.ps1` y verificar el ZIP
- [ ] Comprobar que el ZIP **no contiene** `.env`, `venv/`, `tests/`
- [ ] Probar `INSTALAR.bat` en un Windows sin dependencias previas
- [ ] Verificar que `requirements.txt` está actualizado
- [ ] Subir el ZIP a GitHub Releases con el tag de versión
