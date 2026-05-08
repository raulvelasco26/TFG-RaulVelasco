# TFG - Creación de una aplicación basada en IA para confeccionar el plan económico-financiero

**Autor:** Raul Velasco Tello  
**Tutor:** Jaume Teodoro i Sadurní  
**Curso:** 2025-26  
**Universidad:** Universitat Pompeu Fabra - TecnoCampus

## 📋 Descripción

Aplicación web basada en inteligencia artificial que facilita la elaboración de **Planes Económico-Financieros (PEF)** rigurosos a emprendedores sin formación especializada en finanzas.

### ✨ Características principales

- 🤖 **Interfaz conversacional** en español con LLM (GPT-4/Claude)
- 💰 **Cálculos validados** basados en metodología PEF ToolBoard v2.0
- 📊 **Proyecciones a 5 años** (60 meses)
- 🎁 **Completamente gratuito** y de código abierto

## 🚀 Instalación Rápida (Usuario Final)

### Opción A: Windows (Recomendado)

1. **Descarga** el proyecto (ZIP o `git clone`)
2. Haz **doble clic** en `installation/instalar_y_ejecutar.bat`
3. ¡La aplicación se abre automáticamente en el navegador!
4. Configura tu **API key** desde la **barra lateral** de la propia aplicación

> **Requisito previo**: Python 3.10+ instalado ([descargar](https://www.python.org/downloads/))
> ⚠️ Marca "Add Python to PATH" durante la instalación de Python

### Opción B: Docker

```bash
# Configurar API key (opcional, se puede hacer desde la app)
cp .env.example .env

# Ejecutar (desde la raíz del proyecto)
docker-compose -f installation/docker-compose.yml up
```

### Opción C: Instalación manual

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/TFG-RaulVelasco.git
cd TFG-RaulVelasco

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Instalar dependencias
pip install -r requirements.txt
```

## 🎯 Uso

```bash
# Windows: doble clic en ejecutar_app.bat (raíz del proyecto)
# O desde terminal:
streamlit run src/app.py
```

## 📦 Distribución

Consulta [`installation/GUIA_DISTRIBUCION.md`](installation/GUIA_DISTRIBUCION.md) para opciones avanzadas de empaquetado y distribución (Docker, Streamlit Cloud, pip, etc.).

## 📁 Estructura

```
TFG-RaulVelasco/
├── installation/                      # 📦 Archivos de instalación/distribución
│   ├── instalar_y_ejecutar.bat        # Instalador todo-en-uno (Windows)
│   ├── Dockerfile                     # Imagen Docker
│   ├── docker-compose.yml             # Despliegue Docker
│   └── GUIA_DISTRIBUCION.md           # Guía de distribución
├── src/
│   ├── app.py                        # Aplicación principal
│   ├── config.py                     # Configuración
│   ├── components/
│   │   ├── conversation_manager.py   # Gestor LLM
│   │   ├── financial_engine.py       # Motor de cálculo
│   │   └── excel_generator.py        # Generador Excel
│   └── utils/
│       ├── validators.py
│       └── prompts.py
├── tests/
├── templates/
├── resources/
├── .streamlit/
├── ejecutar_app.bat                  # Launcher rápido (post-instalación)
├── pyproject.toml                    # Packaging PEP 621
└── requirements.txt
```

## 🛠️ Tecnologías

- Streamlit 1.28+
- OpenAI GPT-4 / Anthropic Claude
- pandas, numpy, openpyxl
- pytest

## 📈 Roadmap

- [x] Configuración inicial
- [x] Estructura del proyecto
- [x] Motor de cálculo financiero (Feb-Mar 2026)
- [x] Integración LLM (Mar 2026)
- [x] Generador Excel (Mar-Abr 2026)
- [ ] Testing (Abr 2026)
- [ ] Defensa TFG (Jun 2026)

## 📄 Licencia

MIT License

## ⚠️ Importante

- **NO subir `.env`** con API keys al repositorio
- Proyecto académico (TFG 2025-26)

---

**Versión:** 0.1.0-dev | **Actualización:** Enero 2026
