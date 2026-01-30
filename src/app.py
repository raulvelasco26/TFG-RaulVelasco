"""
Aplicación principal - PEF AI Assistant
Streamlit app para elaboración de Planes Económico-Financieros con IA

TFG 2025-26 - Raul Velasco Tello
Tutor: Jaume Teodoro i Sadurní
Universitat Pompeu Fabra - TecnoCampus
"""
import streamlit as st
from config import Config

# =============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# =============================================================================
st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# ESTILOS CSS PERSONALIZADOS
# =============================================================================
st.markdown("""
<style>
    /* Estilo general */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        font-size: 1.1rem;
        color: #6B7280;
        margin-bottom: 2rem;
    }

    /* Etapas del sidebar */
    .stage-complete {
        color: #059669;
        font-weight: 600;
    }

    .stage-current {
        color: #2563EB;
        font-weight: 700;
        background-color: #DBEAFE;
        padding: 0.5rem;
        border-radius: 0.5rem;
    }

    .stage-pending {
        color: #9CA3AF;
    }

    /* Cards de información */
    .info-card {
        background-color: #F0F9FF;
        border-left: 4px solid #2563EB;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        color: #1E3A8A;
    }

    .success-card {
        background-color: #ECFDF5;
        border-left: 4px solid #059669;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        color: #065F46;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #9CA3AF;
        font-size: 0.85rem;
        padding: 2rem 0;
        border-top: 1px solid #E5E7EB;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# INICIALIZACIÓN DEL ESTADO DE LA SESIÓN
# =============================================================================
def init_session_state():
    """Inicializa las variables de estado de la sesión"""

    # Etapa actual de la navegación
    if "current_stage" not in st.session_state:
        st.session_state.current_stage = "inicio"

    # Historial de mensajes del chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Datos del proyecto (se irán llenando)
    if "proyecto" not in st.session_state:
        st.session_state.proyecto = {}

    if "capex" not in st.session_state:
        st.session_state.capex = []

    if "financiacion" not in st.session_state:
        st.session_state.financiacion = {}

    if "opex" not in st.session_state:
        st.session_state.opex = []

    if "ingresos" not in st.session_state:
        st.session_state.ingresos = []

    # Estado de completitud de cada etapa
    if "stages_status" not in st.session_state:
        st.session_state.stages_status = {
            "inicio": "current",
            "proyecto": "pending",
            "capex": "pending",
            "financiacion": "pending",
            "opex": "pending",
            "ingresos": "pending",
            "analisis": "pending"
        }

# =============================================================================
# DEFINICIÓN DE ETAPAS
# =============================================================================
STAGES = {
    "inicio": {
        "icon": "🏠",
        "title": "Inicio",
        "short": "Bienvenida"
    },
    "proyecto": {
        "icon": "📌",
        "title": "Datos del Proyecto",
        "short": "Proyecto"
    },
    "capex": {
        "icon": "💰",
        "title": "Inversiones (CAPEX)",
        "short": "CAPEX"
    },
    "financiacion": {
        "icon": "🏦",
        "title": "Financiación",
        "short": "Financiación"
    },
    "opex": {
        "icon": "📊",
        "title": "Gastos Operativos (OPEX)",
        "short": "OPEX"
    },
    "ingresos": {
        "icon": "📈",
        "title": "Proyección de Ingresos",
        "short": "Ingresos"
    },
    "analisis": {
        "icon": "📑",
        "title": "Análisis y Resultados",
        "short": "Análisis"
    }
}

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================
def get_stage_status_icon(stage_key):
    """Devuelve el icono de estado para una etapa"""
    status = st.session_state.stages_status.get(stage_key, "pending")
    if status == "complete":
        return "✅"
    elif status == "current":
        return "▶️"
    elif status == "incomplete":
        return "⚠️"
    else:
        return "⬚"

def calculate_progress():
    """Calcula el progreso general del PEF"""
    statuses = st.session_state.stages_status
    complete_count = sum(1 for s in statuses.values() if s == "complete")
    return complete_count / len(statuses)

def change_stage(stage_key):
    """Cambia a una etapa específica"""
    # Actualizar etapa anterior si estaba en 'current'
    for key, status in st.session_state.stages_status.items():
        if status == "current":
            # Marcar como pendiente o completa según tenga datos
            st.session_state.stages_status[key] = "pending"

    st.session_state.stages_status[stage_key] = "current"
    st.session_state.current_stage = stage_key

# =============================================================================
# COMPONENTE: SIDEBAR
# =============================================================================
def render_sidebar():
    """Renderiza la barra lateral con navegación y estado"""

    with st.sidebar:
        # === LOGO Y TÍTULO ===
        st.markdown("## 📊 PEF AI Assistant")
        st.caption("Asistente para Planes Económico-Financieros")

        st.divider()

        # === BARRA DE PROGRESO ===
        st.markdown("### 📈 Progreso General")
        progress = calculate_progress()
        st.progress(progress)
        st.caption(f"{int(progress * 100)}% completado")

        st.divider()

        # === NAVEGACIÓN POR ETAPAS ===
        st.markdown("### 📋 Etapas del PEF")

        for stage_key, stage_info in STAGES.items():
            status_icon = get_stage_status_icon(stage_key)
            is_current = st.session_state.current_stage == stage_key

            # Crear botón para cada etapa
            button_label = f"{status_icon} {stage_info['icon']} {stage_info['short']}"

            if is_current:
                st.markdown(f"**🔵 {stage_info['icon']} {stage_info['short']}**")
            else:
                if st.button(button_label, key=f"nav_{stage_key}", use_container_width=True):
                    change_stage(stage_key)
                    st.rerun()

        st.divider()

        # === RESUMEN DE DATOS ===
        st.markdown("### 📝 Datos Introducidos")

        with st.expander("Ver resumen", expanded=False):
            if st.session_state.proyecto:
                st.write("**Proyecto:**")
                st.write(f"- Nombre: {st.session_state.proyecto.get('nombre', '-')}")
                st.write(f"- Sector: {st.session_state.proyecto.get('sector', '-')}")
            else:
                st.caption("Sin datos de proyecto")

            if st.session_state.capex:
                total_capex = sum(item.get('importe', 0) for item in st.session_state.capex)
                st.metric("Total CAPEX", f"{total_capex:,.0f} €")

            if st.session_state.ingresos:
                st.write(f"**Líneas de ingreso:** {len(st.session_state.ingresos)}")

        st.divider()

        # === ACCIONES ===
        st.markdown("### ⚡ Acciones")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Guardar", use_container_width=True, help="Guardar progreso actual"):
                st.toast("Funcionalidad en desarrollo", icon="🔧")

        with col2:
            if st.button("🔄 Reiniciar", use_container_width=True, help="Comenzar de nuevo"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        # Botón de exportar (solo si está completo)
        st.markdown("---")
        if progress >= 1.0:
            if st.button("📥 Descargar Excel", type="primary", use_container_width=True):
                st.toast("Funcionalidad en desarrollo", icon="🔧")
        else:
            st.info("💡 Completa todas las etapas para generar el Excel")

        # === DEBUG (solo en modo desarrollo) ===
        if Config.DEBUG:
            st.divider()
            st.markdown("### 🔧 Debug")
            st.json({
                "current_stage": st.session_state.current_stage,
                "model": Config.MODEL_NAME,
                "provider": Config.MODEL_PROVIDER
            })

# =============================================================================
# COMPONENTE: ÁREA DE CHAT
# =============================================================================
def render_chat_interface():
    """Renderiza la interfaz de chat con el asistente"""

    # Contenedor para el historial de mensajes
    chat_container = st.container()

    with chat_container:
        # Mostrar mensajes existentes
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input del usuario
    if prompt := st.chat_input("Escribe tu mensaje aquí..."):
        # Añadir mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Mostrar mensaje del usuario
        with st.chat_message("user"):
            st.markdown(prompt)

        # Respuesta del asistente (placeholder - será reemplazado por LLM)
        with st.chat_message("assistant"):
            response = f"[Respuesta del asistente IA - En desarrollo]\n\nHas escrito: *{prompt}*\n\nEsta funcionalidad se conectará con {Config.MODEL_NAME} para proporcionar asistencia contextualizada."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# =============================================================================
# CONTENIDO DE CADA ETAPA
# =============================================================================
def render_stage_inicio():
    """Pantalla de inicio y bienvenida"""

    st.markdown('<p class="main-header">📊 PEF AI Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Tu asistente inteligente para crear Planes Económico-Financieros profesionales</p>', unsafe_allow_html=True)

    # Descripción principal
    st.markdown("""
    ### 👋 ¡Bienvenido!

    Esta herramienta te guiará paso a paso en la elaboración de un **Plan Económico-Financiero (PEF)**
    completo y riguroso para tu proyecto emprendedor.

    ---

    ### 🎯 ¿Qué es un Plan Económico-Financiero?

    Un PEF es un documento esencial que proyecta la evolución financiera de tu negocio durante
    los próximos **5 años (60 meses)**. Incluye:

    - **Cuenta de Resultados**: Ingresos, gastos y beneficios previstos
    - **Flujo de Tesorería**: Entradas y salidas de dinero efectivo
    - **Balance de Situación**: Patrimonio, activos y pasivos
    - **Ratios Financieros**: Indicadores de viabilidad y rentabilidad

    ---

    ### 🤖 ¿Cómo funciona este asistente?

    1. **Conversación guiada**: Un asistente IA te hará preguntas sobre tu proyecto
    2. **Explicaciones claras**: Si no entiendes algún concepto, te lo explicará
    3. **Sugerencias inteligentes**: Te propondrá valores típicos de tu sector
    4. **Cálculos automáticos**: Todo se calcula siguiendo la metodología PEF ToolBoard v2.0
    5. **Excel profesional**: Al final, descargarás un archivo compatible con ENISA

    ---

    ### 📋 Información que necesitarás

    Para completar tu PEF siguiendo la metodología **PEF ToolBoard v2.0**, prepara:
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **📌 Tu Proyecto**
        - Nombre y descripción
        - Sector de actividad
        - Equipo fundador

        **💰 Inversiones (CAPEX)**
        - Intangibles: I+D, patentes, software
        - Materiales: equipos, mobiliario, vehículos
        - Fianzas y depósitos

        **🏦 Financiación**
        - Capital de los fundadores
        - Préstamos (importe, plazo, carencia, interés)
        """)

    with col2:
        st.markdown("""
        **📊 Gastos Operativos (OPEX)**
        - Servicios exteriores: alquiler, suministros, marketing
        - Nóminas: perfiles, salarios, meses de alta/baja

        **📈 Ingresos (hasta 3 líneas de producto)**
        - Mercado potencial (SAM) y cuota objetivo (SOM)
        - Precios de venta e incrementos anuales
        - Costes variables y márgenes
        - Plazos de cobro y pago
        """)

    st.markdown("---")

    # Botón para comenzar
    st.markdown("### 🚀 ¿Listo para empezar?")

    if st.button("Comenzar mi Plan Económico-Financiero", type="primary", use_container_width=True):
        change_stage("proyecto")
        st.rerun()

    # Información adicional
    with st.expander("ℹ️ Más información sobre el proyecto"):
        st.markdown("""
        **Sobre esta herramienta:**

        Este asistente ha sido desarrollado como Trabajo de Fin de Grado (TFG) para la
        Universitat Pompeu Fabra - TecnoCampus, con el objetivo de democratizar el acceso
        a herramientas de planificación financiera.

        **Metodología utilizada:**

        Los cálculos siguen la metodología **PEF ToolBoard v2.0**, una plantilla Excel
        validada en contextos educativos y profesionales que garantiza la rigurosidad
        de las proyecciones financieras.

        **Compatibilidad:**

        El archivo Excel generado es compatible con los requisitos de **ENISA**
        (Empresa Nacional de Innovación) para solicitudes de financiación.
        """)


def render_stage_proyecto():
    """Etapa 1: Datos del proyecto"""

    st.markdown("## 📌 Etapa 1: Datos del Proyecto")
    st.markdown("---")

    # Descripción de la etapa
    st.markdown("""
    <div class="info-card">
    <strong>🎯 Objetivo de esta etapa:</strong><br>
    Recopilar la información básica de identificación de tu proyecto emprendedor.
    Estos datos aparecerán en la portada del PEF y ayudarán al asistente a contextualizar
    sus sugerencias según tu sector de actividad.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 💬 Asistente")
    st.markdown("El asistente IA te guiará mediante preguntas conversacionales:")

    # Mensaje inicial del asistente para esta etapa
    if not any(m.get("stage") == "proyecto" for m in st.session_state.messages):
        welcome_msg = """¡Perfecto! Vamos a empezar con los datos básicos de tu proyecto.

**Cuéntame sobre tu idea de negocio:**

1. 📝 **¿Cómo se llama tu proyecto o empresa?**
2. 🏢 **¿En qué sector opera?** (tecnología, hostelería, comercio, servicios...)
3. 👥 **¿Cuántas personas forman el equipo fundador?**
4. 📅 **¿Cuándo tienes previsto comenzar la actividad?**

Puedes responderme de forma natural, por ejemplo:
*"Mi proyecto se llama TechStore, es una tienda online de electrónica. Somos 2 socios y queremos empezar en marzo de 2026."*"""

        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_msg,
            "stage": "proyecto"
        })

    # Renderizar chat
    render_chat_interface()

    st.markdown("---")

    # Panel de datos recopilados
    st.markdown("### 📋 Datos Recopilados")
    st.caption("Los datos que el asistente extraiga de la conversación aparecerán aquí:")

    col1, col2 = st.columns(2)

    with col1:
        nombre = st.text_input("Nombre del proyecto", value=st.session_state.proyecto.get("nombre", ""), disabled=True)
        sector = st.text_input("Sector de actividad", value=st.session_state.proyecto.get("sector", ""), disabled=True)

    with col2:
        equipo = st.text_input("Número de socios", value=st.session_state.proyecto.get("equipo", ""), disabled=True)
        fecha_inicio = st.text_input("Fecha de inicio prevista", value=st.session_state.proyecto.get("fecha_inicio", ""), disabled=True)

    # Navegación
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Anterior", use_container_width=True):
            change_stage("inicio")
            st.rerun()

    with col3:
        if st.button("Siguiente →", use_container_width=True, type="primary"):
            change_stage("capex")
            st.rerun()


def render_stage_capex():
    """Etapa 2: Inversiones (CAPEX)"""

    st.markdown("## 💰 Etapa 2: Inversiones (CAPEX)")
    st.markdown("---")

    st.markdown("""
    <div class="info-card">
    <strong>🎯 Objetivo de esta etapa:</strong><br>
    Identificar todas las <strong>inversiones iniciales</strong> necesarias para poner en marcha tu negocio.
    El CAPEX (Capital Expenditure) incluye activos que permanecerán en la empresa durante varios años
    y se amortizarán gradualmente.
    </div>
    """, unsafe_allow_html=True)

    # Tabs para organizar la información
    tab_info, tab_chat, tab_datos = st.tabs(["📚 Información", "💬 Asistente", "📋 Datos"])

    with tab_info:
        st.markdown("""
        ### Categorías de Inversión (según PEF ToolBoard)

        El sistema clasifica las inversiones en dos grandes grupos:

        #### 🔷 Inmovilizado Intangible
        | Categoría | Años amortización | Ejemplos |
        |-----------|-------------------|----------|
        | Investigación y desarrollo | 5 años | Desarrollo de producto, I+D |
        | Patentes y marcas | 10 años | Registro de marca, patentes |
        | Aplicaciones informáticas | 5 años | Software, desarrollo web, apps |
        | Otros intangibles | 5 años | Licencias, derechos |

        #### 🔶 Inmovilizado Material
        | Categoría | Años amortización | Ejemplos |
        |-----------|-------------------|----------|
        | Terrenos y construcciones | 50 años | Local en propiedad, obras |
        | Instalaciones | 10 años | Climatización, electricidad |
        | Maquinaria | 10 años | Máquinas de producción |
        | Equipos informáticos (EPIs) | 5 años | Ordenadores, servidores |
        | Mobiliario | 10 años | Mesas, sillas, estanterías |
        | Vehículos | 10 años | Furgonetas, coches empresa |
        | Otros materiales | 5 años | Herramientas, utillaje |

        #### 📌 Fianzas y depósitos
        Importes entregados como garantía (alquiler local, etc.) - Son recuperables.

        ---

        ### 💡 Campos automáticos (calculados por el sistema)
        - **IVA soportado**: 21% sobre el importe de inversión
        - **Total con IVA**: Importe + IVA (desembolso real)
        - **Amortización anual**: Importe / Años de vida útil
        """)

    with tab_chat:
        st.markdown("### 💬 Asistente de Inversiones")

        if not any(m.get("stage") == "capex" for m in st.session_state.messages):
            capex_msg = """Vamos a identificar las **inversiones iniciales** de tu proyecto.

**Según el PEF ToolBoard, necesito conocer para cada inversión:**
1. 📦 **Categoría**: ¿Es intangible (software, patentes) o material (equipos, mobiliario)?
2. 💰 **Importe** (sin IVA)
3. 📅 **Años de amortización** (el sistema sugiere valores por defecto)
4. 🎁 **¿Tienes subvención?** (si hay ayuda pública para esta inversión)

**Cuéntame qué inversiones necesitas:**

Por ejemplo:
- *"Necesito ordenadores por 2.000€ y desarrollar una web por 5.000€"*
- *"Voy a comprar maquinaria por 15.000€ con una subvención del 30%"*
- *"Mobiliario de oficina por 3.000€ y una furgoneta de segunda mano por 8.000€"*"""

            st.session_state.messages.append({
                "role": "assistant",
                "content": capex_msg,
                "stage": "capex"
            })

        render_chat_interface()

    with tab_datos:
        st.markdown("### 📋 Inversiones Registradas")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 26-40)")

        # === INMOVILIZADO INTANGIBLE ===
        st.markdown("#### 🔷 Inmovilizado Intangible")

        intangible_data = {
            "Categoría": [
                "Investigación y desarrollo",
                "Patentes y marcas",
                "Aplicaciones informáticas",
                "Otros intangibles"
            ],
            "Importe (€)": [0, 0, 0, 0],
            "IVA (21%)": ["Auto", "Auto", "Auto", "Auto"],
            "Total con IVA": ["Auto", "Auto", "Auto", "Auto"],
            "Años amort.": [5, 10, 5, 5],
            "Subvención (€)": [0, 0, 0, 0],
            "Amort. anual": ["Auto", "Auto", "Auto", "Auto"]
        }
        st.dataframe(intangible_data, use_container_width=True, hide_index=True)

        # === INMOVILIZADO MATERIAL ===
        st.markdown("#### 🔶 Inmovilizado Material")

        material_data = {
            "Categoría": [
                "Terrenos y construcciones",
                "Instalaciones",
                "Maquinaria",
                "Equipos informáticos (EPIs)",
                "Mobiliario",
                "Vehículos",
                "Otros materiales"
            ],
            "Importe (€)": [0, 0, 0, 0, 0, 0, 0],
            "IVA (21%)": ["Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto"],
            "Total con IVA": ["Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto"],
            "Años amort.": [50, 10, 10, 5, 10, 10, 5],
            "Subvención (€)": [0, 0, 0, 0, 0, 0, 0],
            "Amort. anual": ["Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto"]
        }
        st.dataframe(material_data, use_container_width=True, hide_index=True)

        # === FIANZAS ===
        st.markdown("#### 📌 Fianzas y Depósitos")
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Fianzas (€)", value=0, help="Depósitos recuperables (ej: fianza alquiler)")
        with col2:
            st.selectbox("Recuperable en", ["Año 1", "Año 2", "Año 3", "Año 4", "Año 5"], index=4)

        # === RESUMEN ===
        st.markdown("---")
        st.markdown("### 📊 Resumen de Inversiones")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Intangible", "0 €")
        with col2:
            st.metric("Total Material", "0 €")
        with col3:
            st.metric("IVA Soportado", "0 €", help="Calculado automáticamente al 21%")
        with col4:
            st.metric("TOTAL con IVA", "0 €", help="Desembolso real necesario")

        st.info("💡 **Nota**: Los campos marcados como 'Auto' se calculan automáticamente. Solo necesitas introducir el importe y los años de amortización.")

    # Navegación
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Anterior", use_container_width=True):
            change_stage("proyecto")
            st.rerun()

    with col3:
        if st.button("Siguiente →", use_container_width=True, type="primary"):
            change_stage("financiacion")
            st.rerun()


def render_stage_financiacion():
    """Etapa 3: Financiación"""

    st.markdown("## 🏦 Etapa 3: Financiación")
    st.markdown("---")

    st.markdown("""
    <div class="info-card">
    <strong>🎯 Objetivo de esta etapa:</strong><br>
    Definir <strong>cómo vas a financiar</strong> las inversiones identificadas en la etapa anterior.
    La financiación puede provenir de capital propio (aportaciones de los socios) o de fuentes externas
    (préstamos bancarios, pólizas de crédito).
    </div>
    """, unsafe_allow_html=True)

    # Tabs para organizar la información
    tab_info, tab_chat, tab_datos = st.tabs(["📚 Información", "💬 Asistente", "📋 Datos"])

    with tab_info:
        st.markdown("""
        ### Estructura de Financiación (según PEF ToolBoard)

        #### 💰 Financiación Interna (Capital)
        Aportaciones de los socios fundadores. Puede hacerse en varios momentos:
        - **Capital inicial**: Al constituir la empresa (mes 1)
        - **Ampliaciones**: Aportaciones adicionales en años posteriores

        #### 🏦 Financiación Externa (Préstamos)
        El sistema permite configurar hasta **2 préstamos** con las siguientes condiciones:

        | Parámetro | Descripción | Ejemplo |
        |-----------|-------------|---------|
        | **Mes inicio** | Cuándo se recibe el préstamo (1-60) | Mes 1 |
        | **Importe** | Cantidad prestada | 20.000 € |
        | **Meses carencia** | Período sin pagar capital | 6 meses |
        | **Meses amortización** | Plazo para devolver el capital | 48 meses |
        | **Interés anual** | Tipo de interés (TAE) | 5% |

        #### 💳 Póliza de Crédito
        Línea de crédito automática para cubrir déficits puntuales de tesorería:
        - Se activa automáticamente si hay saldo negativo
        - Solo pagas intereses por el saldo dispuesto
        - Útil como "colchón de seguridad"

        ---

        ### 💡 Campos automáticos (calculados por el sistema)
        - **Mes final**: Mes inicio + Meses carencia + Meses amortización
        - **Cuota mensual**: Calculada con sistema francés (cuota constante)
        - **Intereses totales**: Suma de intereses durante la vida del préstamo
        """)

    with tab_chat:
        st.markdown("### 💬 Asistente de Financiación")

        if not any(m.get("stage") == "financiacion" for m in st.session_state.messages):
            fin_msg = """Vamos a definir **cómo vas a financiar** tu proyecto.

**El PEF ToolBoard estructura la financiación así:**

1. 💰 **Capital de los fundadores**
   - ¿Cuánto aportaréis al inicio?
   - ¿Habrá ampliaciones de capital más adelante?

2. 🏦 **Préstamos** (hasta 2)
   - ¿Vas a pedir préstamos bancarios o de entidades como ENISA?
   - Para cada préstamo necesito: importe, plazo, interés y si tiene carencia

3. 💳 **Póliza de crédito**
   - ¿Quieres configurar una línea de crédito para imprevistos?

**Ejemplo:**
*"Aportamos 10.000€ de capital inicial. Pediremos un préstamo ICO de 25.000€ a 5 años con 1 año de carencia al 4% de interés"*"""

            st.session_state.messages.append({
                "role": "assistant",
                "content": fin_msg,
                "stage": "financiacion"
            })

        render_chat_interface()

    with tab_datos:
        st.markdown("### 📋 Estructura de Financiación")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 63-70)")

        # === FINANCIACIÓN INTERNA ===
        st.markdown("#### 💰 Financiación Interna (Capital)")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.number_input("Capital inicial (€)", value=0, key="capital_inicial",
                           help="Aportación de los fundadores al inicio")
        with col2:
            st.number_input("Ampliación Año 2 (€)", value=0, key="ampliacion_2",
                           help="Aportación adicional en el año 2")
        with col3:
            st.number_input("Ampliación Año 3 (€)", value=0, key="ampliacion_3",
                           help="Aportación adicional en el año 3")

        # === PRÉSTAMOS ===
        st.markdown("#### 🏦 Financiación Externa (Préstamos)")

        st.markdown("**Préstamo 1**")
        cols = st.columns(6)
        with cols[0]:
            st.number_input("Mes inicio", value=1, min_value=1, max_value=60, key="p1_mes")
        with cols[1]:
            st.number_input("Importe (€)", value=0, key="p1_importe")
        with cols[2]:
            st.number_input("Meses carencia", value=0, min_value=0, key="p1_carencia")
        with cols[3]:
            st.number_input("Meses amortiz.", value=60, min_value=1, key="p1_amortiz")
        with cols[4]:
            st.text_input("Mes final", value="Auto", disabled=True, key="p1_final")
        with cols[5]:
            st.number_input("Interés anual %", value=5.0, min_value=0.0, key="p1_interes")

        st.markdown("**Préstamo 2**")
        cols2 = st.columns(6)
        with cols2[0]:
            st.number_input("Mes inicio", value=1, min_value=1, max_value=60, key="p2_mes")
        with cols2[1]:
            st.number_input("Importe (€)", value=0, key="p2_importe")
        with cols2[2]:
            st.number_input("Meses carencia", value=0, min_value=0, key="p2_carencia")
        with cols2[3]:
            st.number_input("Meses amortiz.", value=60, min_value=1, key="p2_amortiz")
        with cols2[4]:
            st.text_input("Mes final", value="Auto", disabled=True, key="p2_final")
        with cols2[5]:
            st.number_input("Interés anual %", value=0.0, min_value=0.0, key="p2_interes")

        # === PÓLIZA DE CRÉDITO ===
        st.markdown("#### 💳 Póliza de Crédito")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Límite", value="Ilimitado", disabled=True,
                         help="Se activa automáticamente si hay déficit de tesorería")
        with col2:
            st.number_input("Interés anual %", value=3.0, min_value=0.0, key="poliza_interes",
                           help="Interés que pagarás por el saldo dispuesto")

        # === RESUMEN ===
        st.markdown("---")
        st.markdown("### 📊 Resumen de Financiación")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Capital", "0 €", help="Aportaciones de los socios")
        with col2:
            st.metric("Total Préstamos", "0 €", help="Suma de préstamos solicitados")
        with col3:
            st.metric("TOTAL Disponible", "0 €")

        # Validación
        st.markdown("---")
        necesidades = 0  # Se calculará desde CAPEX
        disponible = 0

        if disponible >= necesidades:
            st.success(f"✅ **Financiación suficiente**: Dispones de {disponible:,.0f}€ para cubrir {necesidades:,.0f}€ de inversiones")
        elif necesidades > 0:
            st.warning(f"⚠️ **Revisa la financiación**: Las inversiones suman {necesidades:,.0f}€. Asegúrate de tener fondos suficientes.")
        else:
            st.info("💡 Completa primero la etapa de CAPEX para conocer las necesidades de inversión.")

    # Navegación
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Anterior", use_container_width=True):
            change_stage("capex")
            st.rerun()

    with col3:
        if st.button("Siguiente →", use_container_width=True, type="primary"):
            change_stage("opex")
            st.rerun()


def render_stage_opex():
    """Etapa 4: Gastos operativos (OPEX)"""

    st.markdown("## 📊 Etapa 4: Gastos Operativos (OPEX)")
    st.markdown("---")

    st.markdown("""
    <div class="info-card">
    <strong>🎯 Objetivo de esta etapa:</strong><br>
    Identificar todos los <strong>gastos fijos recurrentes</strong>: servicios exteriores y nóminas del personal.
    Los gastos variables (coste de las ventas) se definirán en la etapa de Ingresos.
    </div>
    """, unsafe_allow_html=True)

    # Tabs para organizar la información
    tab_info, tab_chat, tab_servicios, tab_nominas = st.tabs([
        "📚 Información", "💬 Asistente", "🏢 Servicios Exteriores", "👥 Nóminas"
    ])

    with tab_info:
        st.markdown("""
        ### Estructura de Gastos Fijos (según PEF ToolBoard)

        El sistema divide los gastos operativos fijos en dos categorías:

        #### 🏢 Gastos por Servicios Exteriores
        Gastos anuales que se distribuyen mensualmente:

        | Categoría | Descripción | Ejemplos |
        |-----------|-------------|----------|
        | Alquileres | Locales, oficinas, almacén | 800 €/mes = 9.600 €/año |
        | Suministros | Luz, agua, gas, internet, teléfono | 200 €/mes = 2.400 €/año |
        | Rentings | Leasing de equipos o vehículos | Cuotas de renting |
        | Reparaciones | Mantenimiento y reparaciones | Presupuesto anual |
        | Servicios profesionales | Gestoría, abogados, consultores | Honorarios anuales |
        | Transportes | Gastos de envío, mensajería | Presupuesto anual |
        | Gastos bancarios y seguros | Comisiones, seguros RC | Anual |
        | Marketing | Publicidad, ferias, promociones | Presupuesto anual |
        | Tributos municipales | IAE, tasas, licencias | Anual |

        #### 👥 Gastos de Nómina
        Personal contratado organizado en **3 etapas** de crecimiento:

        | Etapa | Descripción | Uso típico |
        |-------|-------------|------------|
        | Etapa 1 | Personal inicial | Desde el mes 1 |
        | Etapa 2 | Primera ampliación | Cuando crece el negocio |
        | Etapa 3 | Segunda ampliación | Consolidación |

        Cada etapa permite definir **5 perfiles** de empleados:
        - Socios fundadores trabajadores (régimen autónomos)
        - Personal tipo A, B, C, D (régimen general)

        ---

        ### 💡 Campos automáticos (calculados por el sistema)
        - **Seguridad Social empresa**: ~33% del salario bruto (régimen general)
        - **Seguridad Social trabajador**: ~6.47% del salario bruto
        - **IRPF**: Retención según tramos de renta
        - **Coste total empresa**: Salario bruto + SS empresa
        """)

    with tab_chat:
        st.markdown("### 💬 Asistente de Gastos Operativos")

        if not any(m.get("stage") == "opex" for m in st.session_state.messages):
            opex_msg = """Vamos a detallar los **gastos fijos** de tu negocio.

**El PEF ToolBoard necesita dos tipos de información:**

🏢 **1. Servicios Exteriores** (gasto ANUAL)
- Alquiler del local/oficina
- Suministros (luz, agua, internet...)
- Gestoría y servicios profesionales
- Marketing y publicidad
- Seguros

👥 **2. Personal** (para cada empleado)
- Número de trabajadores por perfil
- Mes de alta y baja (1-60)
- Salario bruto anual

**Ejemplo:**
*"El alquiler son 800€/mes, suministros unos 150€/mes. Contrataremos 1 empleado administrativo con 18.000€ brutos/año desde el mes 1, y un comercial con 22.000€ desde el mes 6"*

💡 La Seguridad Social e IRPF se calculan automáticamente."""

            st.session_state.messages.append({
                "role": "assistant",
                "content": opex_msg,
                "stage": "opex"
            })

        render_chat_interface()

    with tab_servicios:
        st.markdown("### 🏢 Gastos Fijos por Servicios Exteriores")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 77-85)")
        st.info("💡 Introduce el importe **ANUAL**. El sistema lo distribuirá mensualmente.")

        # Crear tabla de gastos
        gastos_ext = [
            ("Alquileres", "Local, oficina, almacén"),
            ("Suministros", "Luz, agua, gas, internet, teléfono"),
            ("Rentings", "Leasing de equipos o vehículos"),
            ("Reparaciones", "Mantenimiento y reparaciones"),
            ("Servicios profesionales", "Gestoría, abogados, consultores"),
            ("Transportes", "Envíos, mensajería, combustible"),
            ("Gastos bancarios y seguros", "Comisiones bancarias, seguros"),
            ("Marketing", "Publicidad, ferias, redes sociales"),
            ("Tributos municipales", "IAE, tasas, licencias municipales"),
        ]

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown("**Concepto**")
        with col2:
            st.markdown("**Año 1 (€)**")
        with col3:
            st.markdown("**Años 2-5 (€)**")

        for gasto, desc in gastos_ext:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.text(f"{gasto}")
                st.caption(desc)
            with col2:
                st.number_input(f"Año 1 - {gasto}", value=0, key=f"gasto_{gasto}_a1",
                               label_visibility="collapsed")
            with col3:
                st.number_input(f"Años 2-5 - {gasto}", value=0, key=f"gasto_{gasto}_a2",
                               label_visibility="collapsed")

        st.markdown("---")
        st.markdown("**TOTAL ANUAL**")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            st.metric("Año 1", "0 €", label_visibility="collapsed")
        with col3:
            st.metric("Años 2-5", "0 €", label_visibility="collapsed")

    with tab_nominas:
        st.markdown("### 👥 Gastos Fijos por Nómina")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 90-104)")

        # Configuración fiscal (por defecto)
        with st.expander("⚙️ Configuración Seguridad Social (valores por defecto)", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.number_input("SS Autónomos %", value=15.0, key="ss_autonomos",
                               help="Cuota fija mensual sobre base mínima/máxima")
            with col2:
                st.number_input("SS Empresa (Reg. General) %", value=33.0, key="ss_empresa")
            with col3:
                st.number_input("SS Trabajador %", value=6.47, key="ss_trabajador")

        # ETAPA 1
        st.markdown("#### 📌 Etapa 1 - Personal Inicial")

        nomina_headers = ["Perfil", "Nº Trab.", "Mes Alta", "Mes Baja", "Salario Bruto Anual (€)",
                         "SS Empresa", "SS Trabaj.", "IRPF"]

        st.markdown("| " + " | ".join(nomina_headers) + " |")
        st.markdown("|" + "|".join(["---"]*len(nomina_headers)) + "|")

        perfiles_e1 = [
            ("Socios fundadores", "Régimen autónomos"),
            ("Personal tipo A", "Ej: Directivos"),
            ("Personal tipo B", "Ej: Técnicos"),
            ("Personal tipo C", "Ej: Administrativos"),
            ("Personal tipo D", "Ej: Operarios"),
        ]

        for i, (perfil, desc) in enumerate(perfiles_e1):
            cols = st.columns([2, 1, 1, 1, 1.5, 1, 1, 1])
            with cols[0]:
                st.text(perfil)
                st.caption(desc)
            with cols[1]:
                st.number_input("Nº", value=0, key=f"e1_p{i}_num", label_visibility="collapsed")
            with cols[2]:
                st.number_input("Alta", value=1, min_value=1, max_value=60, key=f"e1_p{i}_alta",
                               label_visibility="collapsed")
            with cols[3]:
                st.number_input("Baja", value=60, min_value=1, max_value=60, key=f"e1_p{i}_baja",
                               label_visibility="collapsed")
            with cols[4]:
                st.number_input("Bruto", value=0, key=f"e1_p{i}_salario", label_visibility="collapsed")
            with cols[5]:
                st.text_input("SS Emp", value="Auto", disabled=True, key=f"e1_p{i}_sse",
                             label_visibility="collapsed")
            with cols[6]:
                st.text_input("SS Trab", value="Auto", disabled=True, key=f"e1_p{i}_sst",
                             label_visibility="collapsed")
            with cols[7]:
                st.text_input("IRPF", value="Auto", disabled=True, key=f"e1_p{i}_irpf",
                             label_visibility="collapsed")

        # ETAPA 2
        with st.expander("📌 Etapa 2 - Primera Ampliación de Personal"):
            st.caption("Personal que se incorpora cuando el negocio crece")
            for i, (perfil, desc) in enumerate(perfiles_e1):
                cols = st.columns([2, 1, 1, 1, 1.5, 1, 1, 1])
                with cols[0]:
                    st.text(f"Más {perfil.lower()}")
                with cols[1]:
                    st.number_input("Nº", value=0, key=f"e2_p{i}_num", label_visibility="collapsed")
                with cols[2]:
                    st.number_input("Alta", value=1, key=f"e2_p{i}_alta", label_visibility="collapsed")
                with cols[3]:
                    st.number_input("Baja", value=60, key=f"e2_p{i}_baja", label_visibility="collapsed")
                with cols[4]:
                    st.number_input("Bruto", value=0, key=f"e2_p{i}_salario", label_visibility="collapsed")
                with cols[5]:
                    st.text_input("SS Emp", value="Auto", disabled=True, key=f"e2_p{i}_sse",
                                 label_visibility="collapsed")
                with cols[6]:
                    st.text_input("SS Trab", value="Auto", disabled=True, key=f"e2_p{i}_sst",
                                 label_visibility="collapsed")
                with cols[7]:
                    st.text_input("IRPF", value="Auto", disabled=True, key=f"e2_p{i}_irpf",
                                 label_visibility="collapsed")

        # ETAPA 3
        with st.expander("📌 Etapa 3 - Segunda Ampliación de Personal"):
            st.caption("Personal adicional en fase de consolidación")
            for i, (perfil, desc) in enumerate(perfiles_e1):
                cols = st.columns([2, 1, 1, 1, 1.5, 1, 1, 1])
                with cols[0]:
                    st.text(f"Más {perfil.lower()}")
                with cols[1]:
                    st.number_input("Nº", value=0, key=f"e3_p{i}_num", label_visibility="collapsed")
                with cols[2]:
                    st.number_input("Alta", value=1, key=f"e3_p{i}_alta", label_visibility="collapsed")
                with cols[3]:
                    st.number_input("Baja", value=60, key=f"e3_p{i}_baja", label_visibility="collapsed")
                with cols[4]:
                    st.number_input("Bruto", value=0, key=f"e3_p{i}_salario", label_visibility="collapsed")
                with cols[5]:
                    st.text_input("SS Emp", value="Auto", disabled=True, key=f"e3_p{i}_sse",
                                 label_visibility="collapsed")
                with cols[6]:
                    st.text_input("SS Trab", value="Auto", disabled=True, key=f"e3_p{i}_sst",
                                 label_visibility="collapsed")
                with cols[7]:
                    st.text_input("IRPF", value="Auto", disabled=True, key=f"e3_p{i}_irpf",
                                 label_visibility="collapsed")

        # RESUMEN
        st.markdown("---")
        st.markdown("### 📊 Resumen de Costes de Personal")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Salarios Brutos", "0 €/año")
        with col2:
            st.metric("SS Empresa", "0 €/año", help="Calculado automáticamente")
        with col3:
            st.metric("Coste Total Empresa", "0 €/año", help="Salarios + SS Empresa")
        with col4:
            st.metric("Coste Mensual Medio", "0 €/mes")

    # Navegación
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Anterior", use_container_width=True):
            change_stage("financiacion")
            st.rerun()

    with col3:
        if st.button("Siguiente →", use_container_width=True, type="primary"):
            change_stage("ingresos")
            st.rerun()


def render_stage_ingresos():
    """Etapa 5: Proyección de ingresos"""

    st.markdown("## 📈 Etapa 5: Proyección de Ingresos")
    st.markdown("---")

    st.markdown("""
    <div class="info-card">
    <strong>🎯 Objetivo de esta etapa:</strong><br>
    Definir tus <strong>líneas de producto/servicio</strong> (hasta 3 tipos), estimar el mercado potencial,
    fijar precios y calcular los márgenes comerciales. Esta es la parte más crítica del PEF.
    </div>
    """, unsafe_allow_html=True)

    # Tabs para organizar la información
    tab_info, tab_chat, tab_mercado, tab_precios, tab_margenes = st.tabs([
        "📚 Información", "💬 Asistente", "🎯 Mercado (SAM/SOM)", "💵 Precios", "📊 Márgenes"
    ])

    with tab_info:
        st.markdown("""
        ### Estructura de Ingresos (según PEF ToolBoard)

        El sistema permite definir **hasta 3 líneas de producto/servicio** (Tipo A, B y C).
        Para cada una necesitas:

        #### 🎯 1. Mercado y Volumen de Ventas

        | Concepto | Descripción | Ejemplo |
        |----------|-------------|---------|
        | **SAM** | Serviceable Addressable Market - Mercado accesible | 10.000 clientes potenciales |
        | **SOM %** | Share of Market - Cuota de mercado objetivo | 1% año 1, 5% año 2... |
        | **Unidades** | SAM × SOM = Ventas anuales | 100 unidades año 1 |

        #### 💵 2. Precios de Venta

        | Concepto | Descripción | Ejemplo |
        |----------|-------------|---------|
        | **Precio inicial** | Precio unitario sin IVA (año 1) | 50 €/unidad |
        | **Incremento anual** | % de subida de precios cada año | 3% anual |

        #### 📊 3. Márgenes Comerciales (Costes Variables)

        | Concepto | Descripción | Ejemplo |
        |----------|-------------|---------|
        | **Cv Producción** | Coste variable de fabricar | 20% del precio |
        | **Cv Adquisición** | Coste de comprar mercancía | 40% del precio |
        | **Comisiones** | Comisiones de venta | 5% del precio |
        | **Total Cv/V** | Suma = Coste variable total | 65% del precio |
        | **Margen Bruto** | 100% - Total Cv/V | 35% |

        ---

        ### 💡 Campos automáticos (calculados por el sistema)
        - **Unidades vendidas**: SAM × SOM%
        - **Precios años 2-5**: Precio inicial × (1 + incremento)^año
        - **Total Cv/V**: Suma de costes variables
        - **Ingresos**: Unidades × Precio
        - **Coste de ventas**: Ingresos × Total Cv/V
        - **Margen comercial**: Ingresos - Coste de ventas

        ### 📅 Cobros y Pagos
        También puedes configurar los plazos de cobro a clientes y pago a proveedores,
        que afectan al flujo de tesorería.
        """)

    with tab_chat:
        st.markdown("### 💬 Asistente de Proyección de Ingresos")

        if not any(m.get("stage") == "ingresos" for m in st.session_state.messages):
            ing_msg = """¡Llegamos a la parte más importante! Vamos a proyectar tus **ingresos**.

**El PEF ToolBoard permite hasta 3 líneas de producto/servicio.** Para cada una necesito:

🎯 **Mercado (SAM y SOM)**
- ¿Cuántos clientes potenciales hay en tu mercado accesible? (SAM)
- ¿Qué cuota de mercado esperas captar cada año? (SOM)

💵 **Precios**
- ¿A qué precio venderás cada producto/servicio?
- ¿Subirás precios anualmente?

📊 **Costes Variables (Márgenes)**
- ¿Cuánto te cuesta producir o comprar lo que vendes?
- ¿Pagas comisiones de venta?

**Ejemplo:**
*"Vendemos servicio de consultoría (Tipo A). El mercado son unas 500 empresas en la zona. Esperamos captar un 2% el primer año, 5% el segundo. Precio: 200€/hora, con un coste de tiempo del 30%"*

*"También vendemos cursos online (Tipo B). Mercado de 10.000 personas, captaremos 0.5% el año 1. Precio: 99€, coste de plataforma 10%"*"""

            st.session_state.messages.append({
                "role": "assistant",
                "content": ing_msg,
                "stage": "ingresos"
            })

        render_chat_interface()

    with tab_mercado:
        st.markdown("### 🎯 Mercado y Volumen de Ventas")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 110-118)")

        st.info("💡 **SAM** = Mercado Accesible Servible. **SOM** = Cuota de mercado objetivo. **Unidades = SAM × SOM**")

        # Producto A
        st.markdown("#### 🔵 Producto/Servicio Tipo A")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.number_input("SAM (mercado total)", value=0, key="sam_a",
                           help="Número total de clientes/unidades potenciales")
        with col2:
            st.text_area("Descripción del mercado A", key="desc_sam_a", height=68,
                        placeholder="Explica en qué consiste este mercado y cómo has estimado el SAM...")

        st.markdown("**Cuota de mercado objetivo (SOM) por año:**")
        cols = st.columns(5)
        for i, col in enumerate(cols):
            with col:
                st.number_input(f"Año {i+1} %", value=0.0, key=f"som_a_{i+1}",
                               format="%.2f", help=f"% del SAM que captarás en año {i+1}")

        st.markdown("**Unidades vendidas (calculado automáticamente):**")
        cols = st.columns(5)
        for i, col in enumerate(cols):
            with col:
                st.text_input(f"Año {i+1}", value="0", disabled=True, key=f"uds_a_{i+1}")

        st.markdown("---")

        # Producto B
        st.markdown("#### 🟢 Producto/Servicio Tipo B")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.number_input("SAM (mercado total)", value=0, key="sam_b")
        with col2:
            st.text_area("Descripción del mercado B", key="desc_sam_b", height=68,
                        placeholder="Explica en qué consiste este mercado...")

        st.markdown("**Cuota de mercado objetivo (SOM) por año:**")
        cols = st.columns(5)
        for i, col in enumerate(cols):
            with col:
                st.number_input(f"Año {i+1} %", value=0.0, key=f"som_b_{i+1}", format="%.2f")

        st.markdown("**Unidades vendidas:**")
        cols = st.columns(5)
        for i, col in enumerate(cols):
            with col:
                st.text_input(f"Año {i+1}", value="0", disabled=True, key=f"uds_b_{i+1}")

        st.markdown("---")

        # Producto C
        with st.expander("🟠 Producto/Servicio Tipo C (opcional)"):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.number_input("SAM (mercado total)", value=0, key="sam_c")
            with col2:
                st.text_area("Descripción del mercado C", key="desc_sam_c", height=68)

            st.markdown("**Cuota de mercado objetivo (SOM) por año:**")
            cols = st.columns(5)
            for i, col in enumerate(cols):
                with col:
                    st.number_input(f"Año {i+1} %", value=0.0, key=f"som_c_{i+1}", format="%.2f")

    with tab_precios:
        st.markdown("### 💵 Precios de Venta")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 122-125)")

        st.info("💡 Introduce el precio inicial (Año 1). Los años siguientes se calculan automáticamente con el incremento anual.")

        # Tabla de precios
        st.markdown("#### Precio unitario por tipo de producto (sin IVA)")

        col_headers = st.columns([2, 1, 1, 1, 1, 1])
        with col_headers[0]:
            st.markdown("**Producto**")
        for i in range(5):
            with col_headers[i+1]:
                st.markdown(f"**Año {i+1}**")

        # Tipo A
        cols = st.columns([2, 1, 1, 1, 1, 1])
        with cols[0]:
            st.markdown("🔵 Tipo A")
        with cols[1]:
            st.number_input("Precio A", value=0.0, key="precio_a", label_visibility="collapsed")
        for i in range(2, 6):
            with cols[i]:
                st.text_input(f"P_A_{i}", value="Auto", disabled=True, key=f"precio_a_{i}",
                             label_visibility="collapsed")

        # Tipo B
        cols = st.columns([2, 1, 1, 1, 1, 1])
        with cols[0]:
            st.markdown("🟢 Tipo B")
        with cols[1]:
            st.number_input("Precio B", value=0.0, key="precio_b", label_visibility="collapsed")
        for i in range(2, 6):
            with cols[i]:
                st.text_input(f"P_B_{i}", value="Auto", disabled=True, key=f"precio_b_{i}",
                             label_visibility="collapsed")

        # Tipo C
        cols = st.columns([2, 1, 1, 1, 1, 1])
        with cols[0]:
            st.markdown("🟠 Tipo C")
        with cols[1]:
            st.number_input("Precio C", value=0.0, key="precio_c", label_visibility="collapsed")
        for i in range(2, 6):
            with cols[i]:
                st.text_input(f"P_C_{i}", value="Auto", disabled=True, key=f"precio_c_{i}",
                             label_visibility="collapsed")

        st.markdown("---")

        # Incremento anual
        st.markdown("#### Incremento anual de precios")
        cols = st.columns(5)
        with cols[0]:
            st.text("Año 1 → 2")
        with cols[1]:
            st.text("Año 2 → 3")
        with cols[2]:
            st.text("Año 3 → 4")
        with cols[3]:
            st.text("Año 4 → 5")

        cols = st.columns(5)
        for i in range(4):
            with cols[i]:
                st.number_input(f"Incr {i+1}", value=3.0, key=f"incr_precio_{i+1}",
                               format="%.1f", label_visibility="collapsed", help=f"% incremento año {i+1} a {i+2}")

        st.markdown("---")

        # Plazos de cobro/pago
        st.markdown("#### 📅 Plazos de Cobro y Pago")
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Plazo de cobro a clientes", ["Contado", "30 días", "60 días", "90 días"],
                        key="plazo_cobro", help="Días que tardan los clientes en pagar")
        with col2:
            st.selectbox("Plazo de pago a proveedores", ["Contado", "30 días", "60 días", "90 días"],
                        key="plazo_pago", help="Días que tardas en pagar a proveedores")

    with tab_margenes:
        st.markdown("### 📊 Márgenes Comerciales (Costes Variables)")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 128-139)")

        st.info("""💡 Los **costes variables** son aquellos que varían según el volumen de ventas:
        - **Cv Producción**: Coste de fabricar el producto (materias primas, mano de obra directa)
        - **Cv Adquisición**: Coste de comprar mercancía para revender
        - **Comisiones**: Comisiones de venta, plataformas, etc.
        """)

        st.markdown("#### Introduce los costes variables como % del precio de venta")

        # Headers
        col_h = st.columns([2, 1, 1, 1, 1])
        with col_h[0]:
            st.markdown("**Concepto**")
        with col_h[1]:
            st.markdown("**Tipo A**")
        with col_h[2]:
            st.markdown("**Tipo B**")
        with col_h[3]:
            st.markdown("**Tipo C**")
        with col_h[4]:
            st.markdown("**Descripción**")

        # Cv Producción
        cols = st.columns([2, 1, 1, 1, 1])
        with cols[0]:
            st.markdown("Cv Producción %")
        with cols[1]:
            st.number_input("Cv Prod A", value=0.0, key="cv_prod_a", label_visibility="collapsed")
        with cols[2]:
            st.number_input("Cv Prod B", value=0.0, key="cv_prod_b", label_visibility="collapsed")
        with cols[3]:
            st.number_input("Cv Prod C", value=0.0, key="cv_prod_c", label_visibility="collapsed")
        with cols[4]:
            st.caption("Coste de fabricar")

        # Cv Adquisición
        cols = st.columns([2, 1, 1, 1, 1])
        with cols[0]:
            st.markdown("Cv Adquisición %")
        with cols[1]:
            st.number_input("Cv Adq A", value=0.0, key="cv_adq_a", label_visibility="collapsed")
        with cols[2]:
            st.number_input("Cv Adq B", value=0.0, key="cv_adq_b", label_visibility="collapsed")
        with cols[3]:
            st.number_input("Cv Adq C", value=0.0, key="cv_adq_c", label_visibility="collapsed")
        with cols[4]:
            st.caption("Coste de comprar")

        # Comisiones
        cols = st.columns([2, 1, 1, 1, 1])
        with cols[0]:
            st.markdown("Comisiones %")
        with cols[1]:
            st.number_input("Com A", value=0.0, key="cv_com_a", label_visibility="collapsed")
        with cols[2]:
            st.number_input("Com B", value=0.0, key="cv_com_b", label_visibility="collapsed")
        with cols[3]:
            st.number_input("Com C", value=0.0, key="cv_com_c", label_visibility="collapsed")
        with cols[4]:
            st.caption("Comisiones venta")

        st.markdown("---")

        # TOTAL (calculado)
        cols = st.columns([2, 1, 1, 1, 1])
        with cols[0]:
            st.markdown("**TOTAL Cv/V %**")
        with cols[1]:
            st.text_input("Total A", value="0%", disabled=True, key="cv_total_a",
                         label_visibility="collapsed")
        with cols[2]:
            st.text_input("Total B", value="0%", disabled=True, key="cv_total_b",
                         label_visibility="collapsed")
        with cols[3]:
            st.text_input("Total C", value="0%", disabled=True, key="cv_total_c",
                         label_visibility="collapsed")
        with cols[4]:
            st.caption("**Automático**")

        # Margen bruto (calculado)
        cols = st.columns([2, 1, 1, 1, 1])
        with cols[0]:
            st.markdown("**MARGEN BRUTO %**")
        with cols[1]:
            st.text_input("Margen A", value="100%", disabled=True, key="margen_a",
                         label_visibility="collapsed")
        with cols[2]:
            st.text_input("Margen B", value="100%", disabled=True, key="margen_b",
                         label_visibility="collapsed")
        with cols[3]:
            st.text_input("Margen C", value="100%", disabled=True, key="margen_c",
                         label_visibility="collapsed")
        with cols[4]:
            st.caption("100% - Total Cv/V")

        st.markdown("---")

        # Existencias
        st.markdown("#### 📦 Política de Existencias")
        st.caption("Meses de existencias en almacén (si aplica)")

        cols = st.columns(3)
        with cols[0]:
            st.number_input("Existencias Tipo A (meses)", value=0, key="exist_a",
                           help="Meses de stock en almacén")
        with cols[1]:
            st.number_input("Existencias Tipo B (meses)", value=0, key="exist_b")
        with cols[2]:
            st.number_input("Existencias Tipo C (meses)", value=0, key="exist_c")

    # Resumen de proyección
    st.markdown("---")
    st.markdown("### 📊 Resumen de Proyección de Ingresos")

    col1, col2, col3, col4, col5 = st.columns(5)
    for i, col in enumerate([col1, col2, col3, col4, col5]):
        with col:
            st.metric(f"Año {i+1}", "0 €", help="Ingresos totales proyectados")

    # Navegación
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Anterior", use_container_width=True):
            change_stage("opex")
            st.rerun()

    with col3:
        if st.button("Siguiente →", use_container_width=True, type="primary"):
            change_stage("analisis")
            st.rerun()


def render_stage_analisis():
    """Etapa 6: Análisis y resultados"""

    st.markdown("## 📑 Etapa 6: Análisis y Resultados")
    st.markdown("---")

    st.markdown("""
    <div class="success-card">
    <strong>🎉 ¡Enhorabuena!</strong><br>
    Has completado la introducción de datos. El sistema calculará automáticamente todos los
    estados financieros siguiendo la metodología PEF ToolBoard v2.0.
    </div>
    """, unsafe_allow_html=True)

    # Tabs para mostrar los diferentes análisis (según estructura del Excel)
    tab_pyl, tab_cf, tab_balance, tab_analisis, tab_export = st.tabs([
        "📈 Cuenta de Resultados", "💵 Cash Flow", "⚖️ Balance", "📊 Análisis", "📥 Exportar"
    ])

    with tab_pyl:
        st.markdown("### Cuenta de Resultados (P&L)")
        st.caption("Estructura según hoja RESULTADOS del Excel (filas 5-25)")

        st.markdown("""
        **Todos los valores se calculan automáticamente** a partir de los datos introducidos:
        """)

        # Estructura P&L del Excel
        pyl_estructura = {
            "Concepto": [
                "INGRESOS",
                "   Ventas totales",
                "   Subvenciones de explotación",
                "COSTES DE LAS VENTAS",
                "   Costes variables de las ventas",
                "MARGEN COMERCIAL",
                "OTROS INGRESOS Y GASTOS",
                "   Trabajos para el propio activo",
                "   Gastos fijos servicios exteriores",
                "   Gastos fijos de nómina",
                "MARGEN EBITDA",
                "   Amortizaciones y depreciaciones",
                "   Imputación subvenciones de capital",
                "MARGEN EBIT",
                "   Resultado financiero",
                "MARGEN EBT (Beneficio antes impuestos)",
                "   Impuesto de Sociedades (25%)",
                "RESULTADO (Beneficio/Pérdida)"
            ],
            "Año 1": ["Auto", "Auto", "Auto", "", "Auto", "Auto", "", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto"],
            "Año 2": ["Auto", "Auto", "Auto", "", "Auto", "Auto", "", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto"],
            "Año 3": ["Auto", "Auto", "Auto", "", "Auto", "Auto", "", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto"],
            "Año 4": ["Auto", "Auto", "Auto", "", "Auto", "Auto", "", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto"],
            "Año 5": ["Auto", "Auto", "Auto", "", "Auto", "Auto", "", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto", "Auto"],
        }
        st.dataframe(pyl_estructura, use_container_width=True, hide_index=True)

        st.info("""
        📝 **Cálculos automáticos:**
        - Ventas = Unidades × Precio (para cada tipo A, B, C)
        - Costes variables = Ventas × Total Cv/V
        - Margen comercial = Ventas - Costes variables
        - EBITDA = Margen comercial - Gastos fijos
        - EBIT = EBITDA - Amortizaciones + Subvenciones capital
        - EBT = EBIT - Gastos financieros
        - Resultado = EBT - Impuesto Sociedades (si EBT > 0)
        """)

    with tab_cf:
        st.markdown("### Flujo de Tesorería (Cash Flow)")
        st.caption("Estructura según hoja RESULTADOS del Excel (filas 29-58)")

        st.markdown("El Cash Flow se divide en tres categorías:")

        # CF Operaciones
        st.markdown("#### 📊 CF Operaciones")
        cf_ops = [
            "Cobros de clientes",
            "Cobro de subvenciones de explotación",
            "(-) Pagos a proveedores (coste de ventas)",
            "(-) Pagos gastos fijos servicios exteriores",
            "(-) Pago de nómina al contado",
            "(-) Pago Seguridad Social a TGSS",
            "(-) Pago intereses préstamos + póliza",
            "(-) Pago retenciones IRPF a Hacienda",
            "(-) Pago IVA a Hacienda",
            "(-) Pago Impuesto Sociedades",
            "= CF Operaciones"
        ]
        for item in cf_ops:
            st.text(f"  {item}")

        # CF Inversiones
        st.markdown("#### 💰 CF Inversiones")
        cf_inv = [
            "(-) Pago de inversiones (CAPEX)",
            "(-) Pago variación de existencias",
            "(+) Cobro de desinversiones",
            "(+/-) Fianzas y depósitos",
            "= CF Inversiones"
        ]
        for item in cf_inv:
            st.text(f"  {item}")

        # CF Financiación
        st.markdown("#### 🏦 CF Financiación")
        cf_fin = [
            "(+) Abono capital social",
            "(+) Abono nuevos préstamos",
            "(+) Abono subvenciones de capital",
            "(-) Pago amortización préstamos",
            "(-) Pago dividendos",
            "= CF Financiación"
        ]
        for item in cf_fin:
            st.text(f"  {item}")

        st.markdown("---")
        st.markdown("#### 💵 Resumen")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("CF Neto", "CF Ops + CF Inv + CF Fin")
        with col2:
            st.metric("CF Acumulado", "Tesorería disponible")
        with col3:
            st.metric("Póliza crédito", "Si CF Acum < 0")

        st.warning("⚠️ Si el CF Acumulado es negativo, el sistema activa automáticamente la póliza de crédito configurada.")

    with tab_balance:
        st.markdown("### Balance de Situación")
        st.caption("Calculado automáticamente al cierre de cada año")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ACTIVO")

            st.markdown("**Activo No Corriente**")
            st.text("  Inmovilizado intangible (neto)")
            st.text("  Inmovilizado material (neto)")
            st.text("  Inversiones financieras LP")

            st.markdown("**Activo Corriente**")
            st.text("  Existencias")
            st.text("  Clientes (deudores)")
            st.text("  HP deudora (IVA a compensar)")
            st.text("  Tesorería")

            st.markdown("**TOTAL ACTIVO**")

        with col2:
            st.markdown("#### PATRIMONIO NETO + PASIVO")

            st.markdown("**Patrimonio Neto**")
            st.text("  Capital social")
            st.text("  Reservas")
            st.text("  Resultado del ejercicio")
            st.text("  Subvenciones de capital")

            st.markdown("**Pasivo No Corriente**")
            st.text("  Deudas LP (préstamos)")

            st.markdown("**Pasivo Corriente**")
            st.text("  Deudas CP (préstamos)")
            st.text("  Proveedores (acreedores)")
            st.text("  HP acreedora (IVA, IS, IRPF)")
            st.text("  SS acreedora")
            st.text("  Póliza de crédito dispuesta")

            st.markdown("**TOTAL PN + PASIVO**")

        st.success("✅ El balance siempre cuadra: ACTIVO = PATRIMONIO NETO + PASIVO")

    with tab_analisis:
        st.markdown("### Análisis Financiero")
        st.caption("Estructura según hoja ANALISIS del Excel")

        # Análisis de tesorería
        st.markdown("#### 💵 Análisis del Cash Flow")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Déficit máximo tesorería", "Auto", help="Mes con saldo más bajo")
        with col2:
            st.metric("Mes del pico de déficit", "Auto")
        with col3:
            st.metric("Burn Rate", "Auto", help="CF medio mensual en fase inicial")

        st.markdown("---")

        # Valoración
        st.markdown("#### 💎 Valoración del Proyecto")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Por Flujos de Caja (DCF)**")
            st.metric("TIR", "Auto", help="Tasa Interna de Retorno")
            st.metric("VAN", "Auto", help="Valor Actual Neto (descuento 10%)")
        with col2:
            st.markdown("**Por Múltiplos**")
            st.metric("Valoración x Resultado", "Auto", help="Múltiplo sobre beneficio año 5")

        st.markdown("---")

        # Márgenes
        st.markdown("#### 📊 Evolución de Márgenes")
        margenes_tabla = {
            "Margen": ["Margen Comercial", "Margen EBITDA", "Margen EBT", "Margen Beneficio"],
            "Año 1": ["Auto", "Auto", "Auto", "Auto"],
            "Año 2": ["Auto", "Auto", "Auto", "Auto"],
            "Año 3": ["Auto", "Auto", "Auto", "Auto"],
            "Año 4": ["Auto", "Auto", "Auto", "Auto"],
            "Año 5": ["Auto", "Auto", "Auto", "Auto"],
        }
        st.dataframe(margenes_tabla, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Punto muerto
        st.markdown("#### ⚖️ Punto Muerto (Break-Even)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Unidades para equilibrio", "Auto", help="# unidades anuales para EBT=0")
        with col2:
            st.metric("Mes del punto muerto", "Auto", help="Primer mes con EBT acumulado > 0")
        with col3:
            st.metric("Ventas para equilibrio", "Auto €", help="Ingresos necesarios para EBT=0")

        st.markdown("---")

        # Ratios patrimoniales
        st.markdown("#### 📐 Ratios Patrimoniales")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("**Fondo de Maniobra**")
            st.caption("AC - PC")
            st.metric("FM", "Auto")
        with col2:
            st.markdown("**Apalancamiento**")
            st.caption("Pasivo / (PN + Pasivo)")
            st.metric("Apalancamiento", "Auto")
        with col3:
            st.markdown("**Liquidez**")
            st.caption("AC / PC")
            st.metric("Liquidez", "Auto")
        with col4:
            st.markdown("**Solvencia**")
            st.caption("Activo / Pasivo")
            st.metric("Solvencia", "Auto")

        st.info("""
        📊 **Interpretación de ratios:**
        - **Fondo de Maniobra > 0**: La empresa puede atender sus deudas a corto plazo
        - **Liquidez > 1**: El activo corriente cubre el pasivo corriente
        - **Solvencia > 1.5**: Buena capacidad de pago a largo plazo
        - **Apalancamiento < 0.6**: Nivel de endeudamiento saludable
        """)

    with tab_export:
        st.markdown("### 📥 Exportar Plan Económico-Financiero")

        st.markdown("""
        El archivo Excel generado contendrá **todas las hojas del PEF ToolBoard v2.0**:

        | Hoja | Contenido |
        |------|-----------|
        | **IDEA** | Identificación del proyecto y modelo de negocio |
        | **HIPOTESIS** | Todos los parámetros introducidos (editables) |
        | **C** | Cálculos intermedios mensuales (60 meses) |
        | **RESULTADOS** | Cuenta de Resultados y Cash Flow |
        | **ANALISIS** | Ratios, valoración y punto muerto |

        **Características del archivo:**
        - Formato .xlsx compatible con Excel y LibreOffice
        - Fórmulas editables (puedes modificar hipótesis y ver resultados)
        - Compatible con requisitos de **ENISA** para solicitudes de financiación
        - Gráficos automáticos de evolución
        """)

        st.markdown("---")

        # Opciones de exportación
        st.markdown("#### ⚙️ Opciones de Exportación")

        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Incluir gráficos", value=True, key="export_graficos")
            st.checkbox("Incluir análisis del asistente IA", value=True, key="export_analisis_ia")
        with col2:
            st.checkbox("Proteger celdas de fórmulas", value=False, key="export_proteger")
            st.checkbox("Formato ENISA", value=True, key="export_enisa")

        st.markdown("---")

        # Botón de descarga
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 Generar y Descargar Excel", type="primary", use_container_width=True):
                st.toast("Generando archivo Excel...", icon="⏳")
                # Aquí iría la lógica de generación con ExcelGenerator
                st.success("✅ Archivo generado correctamente")
                st.info("💾 El archivo se descargará automáticamente")

                # Placeholder para el botón de descarga real
                # st.download_button(...)

        st.markdown("---")

        # Análisis del asistente
        st.markdown("### 🤖 Análisis del Asistente IA")

        st.markdown("""
        *El asistente analizará automáticamente los resultados y proporcionará:*

        ✅ **Puntos fuertes** del plan financiero

        ⚠️ **Puntos de atención** y riesgos identificados

        💡 **Recomendaciones** para mejorar la viabilidad

        📊 **Comparativa** con ratios típicos del sector

        *Este análisis se incluirá en el Excel si marcas la opción correspondiente.*
        """)

    # Navegación
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Anterior", use_container_width=True):
            change_stage("ingresos")
            st.rerun()


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================
def main():
    """Función principal de la aplicación"""

    # Inicializar estado de sesión
    init_session_state()

    # Renderizar sidebar
    render_sidebar()

    # Renderizar contenido según la etapa actual
    current_stage = st.session_state.current_stage

    if current_stage == "inicio":
        render_stage_inicio()
    elif current_stage == "proyecto":
        render_stage_proyecto()
    elif current_stage == "capex":
        render_stage_capex()
    elif current_stage == "financiacion":
        render_stage_financiacion()
    elif current_stage == "opex":
        render_stage_opex()
    elif current_stage == "ingresos":
        render_stage_ingresos()
    elif current_stage == "analisis":
        render_stage_analisis()
    else:
        render_stage_inicio()

    # Footer
    st.markdown("""
    <div class="footer">
        <p><strong>PEF AI Assistant</strong> - Asistente para Planes Económico-Financieros</p>
        <p>TFG 2025-26 | Raul Velasco Tello | Tutor: Jaume Teodoro i Sadurní</p>
        <p>Universitat Pompeu Fabra - TecnoCampus Mataró-Maresme</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
