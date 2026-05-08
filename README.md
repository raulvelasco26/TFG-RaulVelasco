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

1. Descarga `PEF-AI-Assistant-v1.0.zip` desde Releases y descomprime
2. Ejecuta el instalador de tu sistema operativo:

| SO | Archivo | Cómo |
|---|---|---|
| Windows | `INSTALAR.bat` | Doble clic |
| Mac | `INSTALAR.command` | Doble clic en Finder |
| Linux | `INSTALAR.sh` | `bash INSTALAR.sh` en terminal |

El instalador crea un entorno virtual, instala las dependencias y deja un acceso directo en el escritorio. A partir de ahí, un clic abre la app en el navegador.

> **Requisito:** Python 3.10+. Si no lo tienes, el instalador abre la página de descarga automáticamente.  
> **Mac:** la primera vez macOS puede pedir permiso en Ajustes → Privacidad y Seguridad.

### Opción B: Docker

```bash
docker-compose -f installation/docker-compose.yml up
```

### Opción C: Instalación manual

```bash
git clone https://github.com/tu-usuario/TFG-RaulVelasco.git
cd TFG-RaulVelasco
python -m venv venv
venv\Scripts\activate     # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
streamlit run src/app.py
```

## 🎯 Uso

```bash
# Doble clic en el acceso directo del escritorio (tras instalar)
# O desde terminal:
streamlit run src/app.py
```

## 📦 Distribución

Consulta [`installation/GUIA_DISTRIBUCION.md`](installation/GUIA_DISTRIBUCION.md) para opciones avanzadas de empaquetado y distribución (Docker, Streamlit Cloud, pip, etc.).

## 📁 Estructura

```
TFG-RaulVelasco/
├── INSTALAR.bat / .command / .sh   <- instaladores por SO
├── src/                            <- código fuente
│   ├── app.py
│   ├── components/                 <- motor de cálculo, Excel, LLM
│   └── utils/
├── tests/                          <- batería de tests
├── installation/                   <- scripts de distribución y Docker
├── templates/                      <- plantilla Excel PEF ToolBoard
├── resources/
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
- [x] Testing (Abr 2026)
- [ ] Defensa TFG (Jun 2026)

## 📄 Licencia

MIT License

## ⚠️ Importante

- **NO subir `.env`** con API keys al repositorio
- Proyecto académico (TFG 2025-26)

---

**Versión:** 0.1.0-dev | **Actualización:** Enero 2026
