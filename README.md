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
- ✅ **Compatible con ENISA** y entidades financieras
- 🎁 **Completamente gratuito** y de código abierto

## 🚀 Instalación

### Requisitos previos
- Python 3.10+
- Cuenta de OpenAI o Anthropic

### Pasos

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

# Configurar API key
cp .env.example .env
# Edita .env y añade tu OPENAI_API_KEY
```

## 🎯 Uso

```bash
streamlit run src/app.py
```

## 📁 Estructura

```
TFG-RaulVelasco/
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
├── docs/
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
