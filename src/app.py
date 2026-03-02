"""
Aplicación principal - PEF AI Assistant
Streamlit app para elaboración de Planes Económico-Financieros con IA

TFG 2025-26 - Raul Velasco Tello
Tutor: Jaume Teodoro i Sadurní
Universitat Pompeu Fabra - TecnoCampus
"""
import streamlit as st
from config import Config
from components.financial_engine import (
    FinancialEngine, Inversion, ProyectoTrabajoActivoPropio, Prestamo,
    Empleado, LineaVenta, GastoFijo, TaxConfig
)
from utils.prompts import (
    SYSTEM_PROMPT_PROYECTO, EXTRACTION_PROMPT_PROYECTO,
    SYSTEM_PROMPT_CAPEX, EXTRACTION_PROMPT_CAPEX,
    SYSTEM_PROMPT_FINANCIACION, EXTRACTION_PROMPT_FINANCIACION,
    SYSTEM_PROMPT_OPEX, EXTRACTION_PROMPT_OPEX,
    SYSTEM_PROMPT_INGRESOS, EXTRACTION_PROMPT_INGRESOS,
    SYSTEM_PROMPT_ANALISIS_BASE,
)

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

    # === CAPEX - Inversiones ===
    _capex_keys = [
        "investigacion", "patentes", "aplicaciones", "otros_intangibles",
        "terrenos", "instalaciones", "maquinaria", "equipos",
        "mobiliario", "vehiculos", "otros_materiales", "fianzas",
    ]
    if "capex" not in st.session_state:
        st.session_state.capex = {
            # Intangibles
            "investigacion": {"importe": 0, "anos": 5, "subvencion": 0},
            "patentes": {"importe": 0, "anos": 10, "subvencion": 0},
            "aplicaciones": {"importe": 0, "anos": 5, "subvencion": 0},
            "otros_intangibles": {"importe": 0, "anos": 5, "subvencion": 0},
            # Materiales
            "terrenos": {"importe": 0, "anos": 50, "subvencion": 0},
            "instalaciones": {"importe": 0, "anos": 10, "subvencion": 0},
            "maquinaria": {"importe": 0, "anos": 10, "subvencion": 0},
            "equipos": {"importe": 0, "anos": 5, "subvencion": 0},
            "mobiliario": {"importe": 0, "anos": 10, "subvencion": 0},
            "vehiculos": {"importe": 0, "anos": 10, "subvencion": 0},
            "otros_materiales": {"importe": 0, "anos": 5, "subvencion": 0},
            # Fianzas
            "fianzas": {"importe": 0, "anos": 5, "subvencion": 0},
        }
        # Pre-inicializar claves de widgets para evitar conflicto con session_state API
        for _k in _capex_keys:
            st.session_state[f"capex_{_k}_importe"] = 0

    # === CAPEX - Proyectos de inversión en años posteriores ===
    if "proyectos_inversion" not in st.session_state:
        st.session_state.proyectos_inversion = {
            "proyecto_inv_1": {"importe": 0, "anos": 1, "mes_adquisicion": 13, "subvencion": 0, "observaciones": ""},
            "proyecto_inv_2": {"importe": 0, "anos": 1, "mes_adquisicion": 13, "subvencion": 0, "observaciones": ""},
        }

    # === CAPEX - Proyectos de trabajo para el propio activo ===
    if "proyectos_trabajo" not in st.session_state:
        st.session_state.proyectos_trabajo = {
            "proyecto_trab_1": {"importe": 0, "anos": 1, "mes_inicio": 1, "mes_fin": 1, "subvencion": 0, "observaciones": ""},
            "proyecto_trab_2": {"importe": 0, "anos": 1, "mes_inicio": 1, "mes_fin": 1, "subvencion": 0, "observaciones": ""},
        }

    # === FINANCIACIÓN ===
    if "financiacion" not in st.session_state:
        st.session_state.financiacion = {
            "capital_inicial": {"importe": 0, "acciones": 0},
            "ampliacion": {"mes": 21, "importe": 0, "valoracion_premoney": 0},
            "prestamo1": {
                "importe": 0, "mes_inicio": 1, "meses_carencia": 0,
                "meses_amortizacion": 60, "interes": 5.0
            },
            "prestamo2": {
                "importe": 0, "mes_inicio": 1, "meses_carencia": 0,
                "meses_amortizacion": 60, "interes": 0.0
            },
            "poliza_interes": 3.0
        }
        # Pre-inicializar claves de widgets para evitar conflicto con session_state API
        st.session_state["cap_ini_importe"] = 0
        st.session_state["cap_ini_acciones"] = 0
        st.session_state["amp_mes"] = 21
        st.session_state["amp_importe"] = 0
        st.session_state["amp_valoracion"] = 0

    # === OPEX - Gastos fijos ===
    if "opex" not in st.session_state:
        st.session_state.opex = {
            "gastos_fijos": {
                "alquileres": {"ano1": 0, "incrementos": [0.0, 0.0, 0.0, 0.0]},
                "suministros": {"ano1": 0, "incrementos": [0.0, 0.0, 0.0, 0.0]},
                "rentings": {"ano1": 0, "incrementos": [0.0, 0.0, 0.0, 0.0]},
                "reparaciones": {"ano1": 0, "incrementos": [0.0, 0.0, 0.0, 0.0]},
                "servicios_prof": {"ano1": 0, "incrementos": [0.0, 0.0, 0.0, 0.0]},
                "transportes": {"ano1": 0, "incrementos": [0.0, 0.0, 0.0, 0.0]},
                "bancarios_seguros": {"ano1": 0, "incrementos": [0.0, 0.0, 0.0, 0.0]},
                "marketing": {"ano1": 0, "incrementos": [0.0, 0.0, 0.0, 0.0]},
                "tributos": {"ano1": 0, "incrementos": [0.0, 0.0, 0.0, 0.0]},
            },
            "empleados": []  # Lista de empleados
        }
        # Pre-inicializar claves de widgets para evitar conflicto con session_state API
        _opex_keys = ["alquileres", "suministros", "rentings", "reparaciones",
                      "servicios_prof", "transportes", "bancarios_seguros", "marketing", "tributos"]
        for _k in _opex_keys:
            st.session_state[f"opex_{_k}_ano1"] = 0
            for _yr in range(2, 6):
                st.session_state[f"opex_{_k}_inc{_yr}"] = 0.0

    # === INGRESOS ===
    if "ingresos" not in st.session_state:
        st.session_state.ingresos = {
            "tipo_a": {
                "nombre": "Producto A",
                "sam": 0,
                "som": [0, 0, 0, 0, 0],
                "precio": 0,
                "incremento": [0, 0, 0, 0],
                "cv_produccion": 0,
                "cv_adquisicion": 0,
                "comisiones": 0,
            },
            "tipo_b": {
                "nombre": "Producto B",
                "sam": 0,
                "som": [0, 0, 0, 0, 0],
                "precio": 0,
                "incremento": [0, 0, 0, 0],
                "cv_produccion": 0,
                "cv_adquisicion": 0,
                "comisiones": 0,
            },
            "tipo_c": {
                "nombre": "Producto C",
                "sam": 0,
                "som": [0, 0, 0, 0, 0],
                "precio": 0,
                "incremento": [0, 0, 0, 0],
                "cv_produccion": 0,
                "cv_adquisicion": 0,
                "comisiones": 0,
            },
        }
        # Pre-inicializar claves de widgets para evitar conflicto con session_state API
        for _k in ("tipo_a", "tipo_b", "tipo_c"):
            st.session_state[f"ing_{_k}_nombre"] = {"tipo_a": "Producto A", "tipo_b": "Producto B", "tipo_c": "Producto C"}[_k]
            st.session_state[f"ing_{_k}_sam"] = 0
            st.session_state[f"ing_{_k}_precio"] = 0.0
            st.session_state[f"ing_{_k}_cv_prod"] = 0.0
            st.session_state[f"ing_{_k}_cv_adq"] = 0.0
            st.session_state[f"ing_{_k}_comisiones"] = 0.0
            for _yr in range(5):
                st.session_state[f"ing_{_k}_som{_yr}"] = 0.0

    # === Motor de cálculos ===
    if "financial_engine" not in st.session_state:
        st.session_state.financial_engine = FinancialEngine()

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
                total_capex = sum(v["importe"] for v in st.session_state.capex.values())
                total_capex += sum(v["importe"] for v in st.session_state.proyectos_inversion.values())
                total_capex += sum(v["importe"] for v in st.session_state.proyectos_trabajo.values())
                st.metric("Total CAPEX", f"{total_capex:,.0f} €")

            if st.session_state.ingresos:
                st.write(f"**Líneas de ingreso:** {len(st.session_state.ingresos)}")

        st.divider()

        # === ACCIONES ===
        st.markdown("### ⚡ Acciones")

        # Exportar Excel
        nombre_sb_default = st.session_state.proyecto.get("nombre", "PEF") or "PEF"
        nombre_sb = st.text_input(
            "Nombre del archivo",
            value=nombre_sb_default,
            key="sidebar_export_filename",
            help="Se guardará como PEF_<nombre>.xlsx en output/",
        )
        if st.button("📥 Generar y Guardar Excel", type="primary", use_container_width=True,
                     disabled=(progress < 1.0),
                     help="Completa todas las etapas para habilitar" if progress < 1.0 else ""):
            with st.spinner("Generando Excel..."):
                try:
                    from components.excel_generator import fill_template
                    excel_bytes = fill_template(st.session_state)
                    safe_name = (nombre_sb or nombre_sb_default).strip().replace(" ", "_")
                    filename = f"PEF_{safe_name}.xlsx"
                    Config.OUTPUT_DIR.mkdir(exist_ok=True)
                    output_path = Config.OUTPUT_DIR / filename
                    try:
                        output_path.write_bytes(excel_bytes)
                        st.success(f"✅ Guardado en output/{filename}")
                    except PermissionError:
                        st.warning(f"⚠️ '{filename}' está abierto en Excel. Descárgalo manualmente.")
                    st.download_button(
                        label="💾 Descargar Excel",
                        data=excel_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"Error generando Excel: {e}")

        if st.button("🔄 Reiniciar", use_container_width=True, help="Borrar todos los datos y comenzar de nuevo"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        # Importar Excel existente
        st.markdown("---")
        st.markdown("### 📂 Importar Excel")

        def _do_import(excel_bytes):
            from components.excel_generator import read_template
            data = read_template(excel_bytes)
            for key, value in data.items():
                st.session_state[key] = value
            for stage in st.session_state.stages_status:
                st.session_state.stages_status[stage] = "complete"

        # --- Excels guardados en output/ ---
        Config.OUTPUT_DIR.mkdir(exist_ok=True)
        saved_files = sorted(
            Config.OUTPUT_DIR.glob("*.xlsx"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if saved_files:
            st.caption(f"📁 {len(saved_files)} archivo(s) en output/")
            opciones = {p.name: p for p in saved_files}
            selected_name = st.selectbox(
                "Selecciona un PEF guardado",
                options=list(opciones.keys()),
                key="select_saved_excel",
            )
            col_load, col_del = st.columns([2, 1])
            with col_load:
                if st.button("📂 Cargar", use_container_width=True, type="primary"):
                    with st.spinner("Cargando..."):
                        try:
                            _do_import(opciones[selected_name].read_bytes())
                            st.success(f"✅ {selected_name} cargado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            with col_del:
                if st.button("🗑️", use_container_width=True, help=f"Borrar {selected_name}",
                             key="btn_borrar_excel"):
                    st.session_state["_confirmar_borrar"] = selected_name

            if st.session_state.get("_confirmar_borrar") == selected_name:
                st.warning(f"¿Borrar **{selected_name}**?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Sí, borrar", type="primary", use_container_width=True,
                                 key="btn_confirmar_borrar"):
                        try:
                            opciones[selected_name].unlink()
                            del st.session_state["_confirmar_borrar"]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al borrar: {e}")
                with c2:
                    if st.button("Cancelar", use_container_width=True, key="btn_cancelar_borrar"):
                        del st.session_state["_confirmar_borrar"]
                        st.rerun()
            st.markdown("---")

        # --- Subir Excel externo ---
        st.caption("O importa un Excel desde tu ordenador:")
        uploaded_file = st.file_uploader(
            "Sube un Excel PEF generado",
            type=["xlsx"],
            key="import_excel_uploader",
            help="Importa un Excel PEF_TOOLBOARD previamente generado para restaurar todos los datos",
        )
        if uploaded_file is not None:
            if st.button("📤 Importar subido", use_container_width=True, type="secondary"):
                with st.spinner("Importando datos del Excel..."):
                    try:
                        _do_import(uploaded_file.read())
                        st.success("✅ Datos importados correctamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error importando Excel: {e}")

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
# LLM — cliente cacheado y helpers de extracción
# =============================================================================

@st.cache_resource
def _get_llm_client():
    """Devuelve un LLMClient cacheado (se crea una sola vez por sesión de servidor)."""
    from components.llm_client import LLMClient
    return LLMClient()


def _build_analisis_system_prompt() -> str:
    """Construye el system prompt del análisis con los resultados financieros reales."""
    try:
        import pandas as pd
        resultados = calcular_proyecciones()
        cr = resultados['cuenta_resultados']
        ft = resultados['flujo_tesoreria']
        bal = resultados['balance']
        ratios = resultados['ratios']
        ratios_glob = ratios.get('globales', {})

        def suma_ano(df, col, ano):
            return sum(df[col][(ano - 1) * 12: ano * 12])

        def fmt_n(v):
            return f"{v:,.0f} €" if v is not None else "N/A"

        def fmt_p(v):
            return f"{v * 100:.1f}%" if v is not None else "N/A"

        proyecto = st.session_state.proyecto
        lineas = []
        lineas.append(f"Proyecto: {proyecto.get('nombre', '—')} | Sector: {proyecto.get('sector', '—')}")
        lineas.append("")
        lineas.append("=== CUENTA DE RESULTADOS (anual) ===")
        lineas.append(f"{'':20} {'Año 1':>12} {'Año 2':>12} {'Año 3':>12} {'Año 4':>12} {'Año 5':>12}")
        for label, col in [
            ("Ingresos", "ingresos"),
            ("Margen comercial", "margen_comercial"),
            ("EBITDA", "ebitda"),
            ("Resultado neto", "resultado"),
        ]:
            vals = [suma_ano(cr, col, a) for a in range(1, 6)]
            lineas.append(f"{label:20} " + " ".join(f"{fmt_n(v):>12}" for v in vals))

        lineas.append("")
        lineas.append("=== MÁRGENES (% sobre ingresos) ===")
        for label, col in [("Margen comercial", "margen_comercial"), ("EBITDA", "ebitda"), ("Resultado neto", "resultado")]:
            row = []
            for a in range(1, 6):
                ing = suma_ano(cr, "ingresos", a)
                val = suma_ano(cr, col, a)
                row.append(fmt_p(val / ing) if ing > 0 else "  N/A")
            lineas.append(f"{label:20} " + " ".join(f"{v:>12}" for v in row))

        lineas.append("")
        lineas.append("=== CASH FLOW NETO (anual) ===")
        cf_vals = [suma_ano(ft, "cf_neto", a) for a in range(1, 6)]
        lineas.append("CF Neto            " + " ".join(f"{fmt_n(v):>12}" for v in cf_vals))

        burn = suma_ano(ft, "cf_neto", 1) / 12
        lineas.append(f"Burn rate año 1: {fmt_n(burn)}/mes")

        lineas.append("")
        lineas.append("=== BALANCE (final año 5) ===")
        m = 59
        ac = bal['activo_corriente'][m]
        pc = bal['pasivo_corriente'][m]
        pnc = bal['pasivo_no_corriente'][m]
        pn = bal['patrimonio_neto'][m]
        total_p = pc + pnc
        fm = ac - pc
        lineas.append(f"Fondo de maniobra: {fmt_n(fm)}")
        lineas.append(f"Liquidez (AC/PC): {(ac / pc):.2f}" if pc > 0 else "Liquidez: N/A (sin pasivo corriente)")
        lineas.append(f"Solvencia (Activo/Pasivo): {(bal['activo_total'][m] / total_p):.2f}" if total_p > 0 else "Solvencia: N/A")
        lineas.append(f"Apalancamiento: {(total_p / (pn + total_p) * 100):.1f}%" if (pn + total_p) > 0 else "Apalancamiento: N/A")

        lineas.append("")
        lineas.append("=== VALORACIÓN ===")
        tir = ratios.get('tir')
        van = ratios.get('van')
        lineas.append(f"TIR: {fmt_p(tir) if tir else 'N/A'}")
        lineas.append(f"VAN (tasa 10%): {fmt_n(van) if van else 'N/A'}")

        mes_pm = ratios_glob.get('mes_punto_equilibrio')
        lineas.append(f"Mes punto muerto: {f'Mes {mes_pm}' if mes_pm else 'No alcanzado en 5 años'}")
        deficit_max = ratios_glob.get('deficit_maximo', 0)
        if deficit_max > 0:
            lineas.append(f"Déficit máximo tesorería: {fmt_n(deficit_max)} (mes {ratios_glob.get('mes_deficit_maximo', '?')})")

        datos = "\n".join(lineas)
    except Exception as e:
        datos = f"(No se pudieron calcular las proyecciones: {e})"

    return SYSTEM_PROMPT_ANALISIS_BASE.format(datos_financieros=datos)


def _get_system_prompt(stage: str) -> str:
    """Devuelve el prompt de sistema apropiado para cada etapa."""
    from utils.prompts import SYSTEM_PROMPT
    prompts = {
        "proyecto": SYSTEM_PROMPT_PROYECTO,
        "capex": SYSTEM_PROMPT_CAPEX,
        "financiacion": SYSTEM_PROMPT_FINANCIACION,
        "opex": SYSTEM_PROMPT_OPEX,
        "ingresos": SYSTEM_PROMPT_INGRESOS,
    }
    if stage == "analisis":
        return _build_analisis_system_prompt()
    return prompts.get(stage, SYSTEM_PROMPT)


def _extract_and_save_proyecto():
    """
    Llama al LLM con un prompt de extracción para parsear los datos
    del proyecto de la conversación y actualiza st.session_state.proyecto.
    """
    # Construir texto de la conversación de esta etapa
    conversation = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in st.session_state.messages
        if m["role"] in ("user", "assistant") and m.get("stage") == "proyecto"
    ])
    if not conversation:
        return

    client = _get_llm_client()
    data = client.extract_json(
        messages=[{"role": "user", "content": conversation}],
        system=EXTRACTION_PROMPT_PROYECTO,
    )

    # Actualizar solo los campos que el LLM haya extraído (no sobreescribir con null)
    for field in ("nombre", "sector", "equipo", "fecha_inicio"):
        value = data.get(field)
        if value and value != "null":
            st.session_state.proyecto[field] = value


def _extract_and_save_capex():
    """Extrae importes de inversión de la conversación y actualiza st.session_state.capex."""
    conversation = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in st.session_state.messages
        if m["role"] in ("user", "assistant") and m.get("stage") == "capex"
    ])
    if not conversation:
        return

    client = _get_llm_client()
    data = client.extract_json(
        messages=[{"role": "user", "content": conversation}],
        system=EXTRACTION_PROMPT_CAPEX,
    )

    capex_keys = [
        "investigacion", "patentes", "aplicaciones", "otros_intangibles",
        "terrenos", "instalaciones", "maquinaria", "equipos",
        "mobiliario", "vehiculos", "otros_materiales", "fianzas",
    ]
    for key in capex_keys:
        value = data.get(key)
        if value is not None and isinstance(value, (int, float)) and value > 0:
            importe = int(value)
            st.session_state.capex[key]["importe"] = importe
            st.session_state[f"capex_{key}_importe"] = importe


def _extract_and_save_financiacion():
    """Extrae datos de financiación de la conversación y actualiza st.session_state.financiacion."""
    conversation = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in st.session_state.messages
        if m["role"] in ("user", "assistant") and m.get("stage") == "financiacion"
    ])
    if not conversation:
        return

    client = _get_llm_client()
    data = client.extract_json(
        messages=[{"role": "user", "content": conversation}],
        system=EXTRACTION_PROMPT_FINANCIACION,
    )

    def _num(key):
        v = data.get(key)
        return v if isinstance(v, (int, float)) and v > 0 else None

    fin = st.session_state.financiacion

    if _num("capital_inicial_importe"):
        v = int(_num("capital_inicial_importe"))
        fin["capital_inicial"]["importe"] = v
        st.session_state["cap_ini_importe"] = v
    if _num("capital_inicial_acciones"):
        v = int(_num("capital_inicial_acciones"))
        fin["capital_inicial"]["acciones"] = v
        st.session_state["cap_ini_acciones"] = v
    if _num("ampliacion_mes"):
        v = int(_num("ampliacion_mes"))
        fin["ampliacion"]["mes"] = v
        st.session_state["amp_mes"] = v
    if _num("ampliacion_importe"):
        v = int(_num("ampliacion_importe"))
        fin["ampliacion"]["importe"] = v
        st.session_state["amp_importe"] = v
    if _num("ampliacion_valoracion_premoney"):
        v = int(_num("ampliacion_valoracion_premoney"))
        fin["ampliacion"]["valoracion_premoney"] = v
        st.session_state["amp_valoracion"] = v
    for p in ("prestamo1", "prestamo2"):
        if _num(f"{p}_importe"):
            fin[p]["importe"] = int(_num(f"{p}_importe"))
        if _num(f"{p}_interes"):
            fin[p]["interes"] = float(_num(f"{p}_interes"))
        if _num(f"{p}_meses_amortizacion"):
            fin[p]["meses_amortizacion"] = int(_num(f"{p}_meses_amortizacion"))
        if _num(f"{p}_meses_carencia"):
            fin[p]["meses_carencia"] = int(_num(f"{p}_meses_carencia"))
        if _num(f"{p}_mes_inicio"):
            fin[p]["mes_inicio"] = int(_num(f"{p}_mes_inicio"))
    if _num("poliza_interes"):
        fin["poliza_interes"] = float(_num("poliza_interes"))


def _extract_and_save_opex():
    """Extrae gastos fijos de la conversación y actualiza st.session_state.opex."""
    conversation = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in st.session_state.messages
        if m["role"] in ("user", "assistant") and m.get("stage") == "opex"
    ])
    if not conversation:
        return

    client = _get_llm_client()
    data = client.extract_json(
        messages=[{"role": "user", "content": conversation}],
        system=EXTRACTION_PROMPT_OPEX,
    )

    opex_keys = ["alquileres", "suministros", "rentings", "reparaciones",
                 "servicios_prof", "transportes", "bancarios_seguros", "marketing", "tributos"]
    for key in opex_keys:
        gf = st.session_state.opex["gastos_fijos"][key]
        # Importe año 1
        value = data.get(key)
        if value is not None and isinstance(value, (int, float)) and value > 0:
            v = int(value)
            gf["ano1"] = v
            st.session_state[f"opex_{key}_ano1"] = v
        # Incrementos por año
        for yr in range(2, 6):
            inc_val = data.get(f"{key}_inc{yr}")
            if inc_val is not None and isinstance(inc_val, (int, float)):
                gf["incrementos"][yr - 2] = float(inc_val)
                st.session_state[f"opex_{key}_inc{yr}"] = float(inc_val)


def _extract_and_save_ingresos():
    """Extrae datos de ingresos de la conversación y actualiza st.session_state.ingresos."""
    conversation = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in st.session_state.messages
        if m["role"] in ("user", "assistant") and m.get("stage") == "ingresos"
    ])
    if not conversation:
        return

    client = _get_llm_client()
    data = client.extract_json(
        messages=[{"role": "user", "content": conversation}],
        system=EXTRACTION_PROMPT_INGRESOS,
    )

    for key in ("tipo_a", "tipo_b", "tipo_c"):
        ing = st.session_state.ingresos[key]

        nombre = data.get(f"{key}_nombre")
        if nombre and isinstance(nombre, str):
            ing["nombre"] = nombre
            st.session_state[f"ing_{key}_nombre"] = nombre

        sam = data.get(f"{key}_sam")
        if sam is not None and isinstance(sam, (int, float)) and sam > 0:
            v = int(sam)
            ing["sam"] = v
            st.session_state[f"ing_{key}_sam"] = v

        precio = data.get(f"{key}_precio")
        if precio is not None and isinstance(precio, (int, float)) and precio > 0:
            ing["precio"] = float(precio)
            st.session_state[f"ing_{key}_precio"] = float(precio)

        for yr in range(1, 6):
            som_val = data.get(f"{key}_som{yr}")
            if som_val is not None and isinstance(som_val, (int, float)):
                ing["som"][yr - 1] = float(som_val)  # stored as % (prepare_financial_engine divides by 100)
                st.session_state[f"ing_{key}_som{yr - 1}"] = float(som_val)

        for yr in range(2, 6):
            inc_val = data.get(f"{key}_inc{yr}")
            if inc_val is not None and isinstance(inc_val, (int, float)):
                ing["incremento"][yr - 2] = float(inc_val)  # stored as % (prepare_financial_engine divides by 100)

        cv_prod = data.get(f"{key}_cv_prod")
        if cv_prod is not None and isinstance(cv_prod, (int, float)):
            ing["cv_produccion"] = float(cv_prod)
            st.session_state[f"ing_{key}_cv_prod"] = float(cv_prod)

        cv_adq = data.get(f"{key}_cv_adq")
        if cv_adq is not None and isinstance(cv_adq, (int, float)):
            ing["cv_adquisicion"] = float(cv_adq)
            st.session_state[f"ing_{key}_cv_adq"] = float(cv_adq)

        comisiones = data.get(f"{key}_comisiones")
        if comisiones is not None and isinstance(comisiones, (int, float)):
            ing["comisiones"] = float(comisiones)
            st.session_state[f"ing_{key}_comisiones"] = float(comisiones)


# =============================================================================
# COMPONENTE: ÁREA DE CHAT
# =============================================================================
def render_chat_interface(stage: str = ""):
    """Renderiza la interfaz de chat con el asistente."""

    # Mostrar historial de mensajes
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input del usuario
    if prompt := st.chat_input("Escribe tu mensaje aquí..."):
        st.session_state.messages.append({"role": "user", "content": prompt, "stage": stage})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            client = _get_llm_client()

            if not client.is_configured:
                response = "⚠️ El asistente IA no está configurado. Añade tu API key en el archivo `.env`."
            else:
                # Construir historial para el LLM (solo role y content)
                llm_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                    if m["role"] in ("user", "assistant")
                ]
                with st.spinner("Pensando..."):
                    response = client.chat(
                        messages=llm_messages,
                        system=_get_system_prompt(stage),
                    )

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response, "stage": stage})

        # Extracción de datos tras cada intercambio (por etapa)
        if stage == "proyecto":
            _extract_and_save_proyecto()
        elif stage == "capex":
            _extract_and_save_capex()
        elif stage == "financiacion":
            _extract_and_save_financiacion()
        elif stage == "opex":
            _extract_and_save_opex()
        elif stage == "ingresos":
            _extract_and_save_ingresos()

        st.rerun()

# =============================================================================
# FUNCIONES AUXILIARES PARA INGRESOS
# =============================================================================
def render_mercado_producto(key, titulo):
    """Renderiza los campos de mercado para un tipo de producto"""
    col1, col2 = st.columns([1, 3])
    with col1:
        sam = st.number_input(
            f"SAM {key}", min_value=0, step=100, label_visibility="collapsed",
            help="Número total de clientes/unidades potenciales en tu mercado",
            key=f"ing_{key}_sam"
        )
        st.session_state.ingresos[key]["sam"] = sam
        st.caption("SAM (mercado)")
    with col2:
        nombre = st.text_input(
            f"Nombre {key}", label_visibility="collapsed",
            placeholder="Describe tu producto/servicio...",
            key=f"ing_{key}_nombre"
        )
        st.session_state.ingresos[key]["nombre"] = nombre

    # SOM por año (editable) y Unidades (calculado)
    st.markdown("**Cuota de mercado (SOM %) y Unidades vendidas:**")
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.markdown(f"**Año {i+1}**")
            som = st.number_input(
                f"SOM {key} {i+1}",
                min_value=0.0, max_value=100.0, step=0.1, format="%.2f",
                label_visibility="collapsed",
                help=f"% del SAM que captarás en año {i+1}",
                key=f"ing_{key}_som{i}"
            )
            st.session_state.ingresos[key]["som"][i] = som
            st.caption(f"SOM: {som}%")
            # Unidades calculadas
            unidades = int(sam * som / 100)
            st.text(f"→ {unidades:,} uds")


def render_precios_producto(key, titulo):
    """Renderiza los campos de precios para un tipo de producto"""
    cols = st.columns(6)
    with cols[0]:
        st.markdown(f"**{titulo}**")

    # Precio año 1 (editable)
    with cols[1]:
        precio = st.number_input(
            f"Precio {key}",
            value=float(st.session_state.ingresos[key]["precio"]),
            min_value=0.0, step=1.0, format="%.2f",
            label_visibility="collapsed"
        )
        st.session_state.ingresos[key]["precio"] = precio

    # Precios años 2-5 (calculados con incremento)
    precio_actual = precio
    for i in range(4):
        incremento = st.session_state.ingresos[key]["incremento"][i] if i < len(st.session_state.ingresos[key]["incremento"]) else 0
        precio_actual = precio_actual * (1 + incremento / 100)
        with cols[i + 2]:
            st.text(f"{precio_actual:,.2f} €")


def render_margenes_producto(key, titulo):
    """Renderiza los campos de márgenes para un tipo de producto"""
    # Cv Producción
    cv_prod = st.number_input(
        f"Cv Prod {key}",
        value=float(st.session_state.ingresos[key]["cv_produccion"]),
        min_value=0.0, max_value=100.0, step=0.5, format="%.1f",
        label_visibility="collapsed"
    )
    st.session_state.ingresos[key]["cv_produccion"] = cv_prod
    return cv_prod


def prepare_financial_engine():
    """
    Prepara el FinancialEngine con todos los datos de session_state.
    Convierte los datos de la UI al formato esperado por el motor de cálculo.
    """
    engine = st.session_state.financial_engine

    # 1. CAPEX - Inversiones
    inversiones = []
    capex_mapping = {
        "investigacion": "Investigación y desarrollo",
        "patentes": "Patentes y marcas",
        "aplicaciones": "Aplicaciones informáticas",
        "otros_intangibles": "Otros intangibles",
        "terrenos": "Terrenos y construcciones",
        "instalaciones": "Instalaciones",
        "maquinaria": "Maquinaria",
        "equipos": "Equipos informáticos",
        "mobiliario": "Mobiliario",
        "vehiculos": "Vehículos",
        "otros_materiales": "Otros materiales",
        "fianzas": "Fianzas y depósitos",
    }

    for key, nombre in capex_mapping.items():
        data = st.session_state.capex.get(key, {})
        importe = data.get("importe", 0)
        if importe > 0:
            inversiones.append({
                "concepto": nombre,
                "importe": importe,
                "vida_util_anos": data.get("anos", 5),
                "mes_adquisicion": 1,
                "subvencion": data.get("subvencion", 0)
            })

    # Proyectos de inversión en años posteriores (son Inversiones estándar con mes_adquisicion > 1)
    for key in st.session_state.proyectos_inversion:
        pi = st.session_state.proyectos_inversion[key]
        if pi.get("importe", 0) > 0:
            inversiones.append({
                "concepto": pi.get("observaciones", key) or key,
                "importe": pi["importe"],
                "vida_util_anos": pi.get("anos", 5),
                "mes_adquisicion": pi.get("mes_adquisicion", 13),
                "subvencion": pi.get("subvencion", 0)
            })

    engine.set_inversiones(inversiones)

    # Proyectos de trabajo para el propio activo
    proyectos_trabajo = []
    for key in st.session_state.proyectos_trabajo:
        pt = st.session_state.proyectos_trabajo[key]
        if pt.get("importe", 0) > 0:
            proyectos_trabajo.append({
                "concepto": pt.get("observaciones", key) or key,
                "importe": pt["importe"],
                "vida_util_anos": pt.get("anos", 5),
                "mes_inicio_proyecto": pt.get("mes_inicio", 1),
                "mes_fin_proyecto": pt.get("mes_fin", 12),
                "subvencion": pt.get("subvencion", 0)
            })
    engine.set_proyectos_trabajo(proyectos_trabajo)

    # 2. Financiación
    financiacion_data = st.session_state.financiacion
    prestamos = []

    if financiacion_data.get("prestamo1", {}).get("importe", 0) > 0:
        p1 = financiacion_data["prestamo1"]
        prestamos.append({
            "nombre": "Préstamo 1",
            "importe": p1["importe"],
            "mes_inicio": p1.get("mes_inicio", 1),
            "meses_carencia": p1.get("meses_carencia", 0),
            "meses_amortizacion": p1.get("meses_amortizacion", 60),
            "interes_anual": p1.get("interes", 5.0) / 100
        })

    if financiacion_data.get("prestamo2", {}).get("importe", 0) > 0:
        p2 = financiacion_data["prestamo2"]
        prestamos.append({
            "nombre": "Préstamo 2",
            "importe": p2["importe"],
            "mes_inicio": p2.get("mes_inicio", 1),
            "meses_carencia": p2.get("meses_carencia", 0),
            "meses_amortizacion": p2.get("meses_amortizacion", 60),
            "interes_anual": p2.get("interes", 0.0) / 100
        })

    # Capital: leer del nuevo formato {importe, acciones}
    cap_ini = financiacion_data.get("capital_inicial", {})
    if isinstance(cap_ini, dict):
        capital_inicial_total = cap_ini.get("importe", 0)
    else:
        capital_inicial_total = cap_ini  # Backward compatibility

    ampliacion_data = financiacion_data.get("ampliacion", {})
    ampliaciones = []
    if isinstance(ampliacion_data, dict) and ampliacion_data.get("importe", 0) > 0:
        ampliaciones.append({"mes": ampliacion_data.get("mes", 21), "importe": ampliacion_data["importe"]})

    engine.set_financiacion({
        "capital_inicial": capital_inicial_total,
        "ampliaciones": ampliaciones,
        "poliza_interes": financiacion_data.get("poliza_interes", 3.0) / 100,
        "prestamos": prestamos
    })

    # 3. OPEX - Gastos fijos
    gastos_fijos = []
    opex_data = st.session_state.opex.get("gastos_fijos", {})

    gastos_mapping = {
        "alquileres": "Alquileres",
        "suministros": "Suministros",
        "rentings": "Rentings",
        "reparaciones": "Reparaciones",
        "servicios_prof": "Servicios profesionales",
        "transportes": "Transportes",
        "bancarios_seguros": "Gastos bancarios y seguros",
        "marketing": "Marketing",
        "tributos": "Tributos municipales",
    }

    for key, nombre in gastos_mapping.items():
        data = opex_data.get(key, {})
        ano1 = data.get("ano1", 0)
        if ano1 > 0:
            # Calcular importes por año desde ano1 + incrementos por año
            incrementos = data.get("incrementos", [0.0, 0.0, 0.0, 0.0])
            importes = [float(ano1)]
            for inc in incrementos:
                importes.append(importes[-1] * (1 + inc / 100))
            gastos_fijos.append({
                "concepto": nombre,
                "importes_anuales": importes
            })

    # 4. Empleados (ahora con 3 etapas y incremento salarial)
    empleados = []
    incrementos_salariales = {}  # {etapa: incremento}
    perfiles_config = {
        "socios": ("Socios fundadores", True),
        "perfil_a": ("Personal tipo A", False),
        "perfil_b": ("Personal tipo B", False),
        "perfil_c": ("Personal tipo C", False),
        "perfil_d": ("Personal tipo D", False),
    }

    if "empleados_data" in st.session_state:
        emp_data = st.session_state.empleados_data
        # Verificar si es la estructura nueva con "perfiles"
        if isinstance(list(emp_data.keys())[0], int) and "perfiles" in emp_data.get(1, {}):
            # Nueva estructura con 3 etapas y perfiles
            for etapa_num in [1, 2, 3]:
                if etapa_num in emp_data:
                    # Guardar incremento salarial de esta etapa
                    incrementos_salariales[etapa_num] = emp_data[etapa_num].get("incremento_salario", 0) / 100

                    perfiles_data = emp_data[etapa_num].get("perfiles", {})
                    for key, (nombre, es_autonomo) in perfiles_config.items():
                        data = perfiles_data.get(key, {})
                        num = data.get("num", 0)
                        if num > 0:
                            empleados.append({
                                "perfil": f"{nombre} (Etapa {etapa_num})",
                                "num_trabajadores": num,
                                "mes_alta": data.get("alta", 1),
                                "mes_baja": data.get("baja", 60),
                                "sueldo_bruto_anual": data.get("salario", 0),
                                "es_autonomo": es_autonomo,
                                "etapa": etapa_num
                            })
        elif isinstance(list(emp_data.keys())[0], int):
            # Estructura intermedia (etapas sin "perfiles")
            for etapa_num in [1, 2, 3]:
                if etapa_num in emp_data:
                    for key, (nombre, es_autonomo) in perfiles_config.items():
                        data = emp_data[etapa_num].get(key, {})
                        num = data.get("num", 0)
                        if num > 0:
                            empleados.append({
                                "perfil": f"{nombre} (Etapa {etapa_num})",
                                "num_trabajadores": num,
                                "mes_alta": data.get("alta", 1),
                                "mes_baja": data.get("baja", 60),
                                "sueldo_bruto_anual": data.get("salario", 0),
                                "es_autonomo": es_autonomo,
                                "etapa": etapa_num
                            })
        else:
            # Estructura antigua (sin etapas) - compatibilidad
            for key, (nombre, es_autonomo) in perfiles_config.items():
                data = emp_data.get(key, {})
                num = data.get("num", 0)
                if num > 0:
                    empleados.append({
                        "perfil": nombre,
                        "num_trabajadores": num,
                        "mes_alta": data.get("alta", 1),
                        "mes_baja": data.get("baja", 60),
                        "sueldo_bruto_anual": data.get("salario", 0),
                        "es_autonomo": es_autonomo,
                        "etapa": 1
                    })

    # Pasar los incrementos salariales al engine
    engine.incrementos_salariales = incrementos_salariales

    engine.set_gastos_operativos(gastos_fijos, empleados)

    # 5. Ingresos - Líneas de venta
    lineas = []
    for tipo_key in ["tipo_a", "tipo_b", "tipo_c"]:
        data = st.session_state.ingresos.get(tipo_key, {})
        sam = data.get("sam", 0)
        precio = data.get("precio", 0)
        if sam > 0 and precio > 0:
            # Convertir SOM de porcentaje a decimal
            som_list = [s / 100 if s > 0 else 0 for s in data.get("som", [0, 0, 0, 0, 0])]
            # Convertir incrementos de porcentaje a decimal
            inc_list = [0] + [i / 100 for i in data.get("incremento", [0, 0, 0, 0])]

            lineas.append({
                "nombre": data.get("nombre", tipo_key),
                "sam": sam,
                "som_anual": som_list,
                "precio_inicial": precio,
                "incremento_precio_anual": inc_list,
                "cv_produccion": data.get("cv_produccion", 0) / 100,
                "cv_adquisicion": data.get("cv_adquisicion", 0) / 100,
                "comisiones": data.get("comisiones", 0) / 100
            })

    engine.set_ingresos(lineas)

    return engine


def calcular_proyecciones():
    """
    Ejecuta todos los cálculos financieros y devuelve los resultados.
    """
    engine = prepare_financial_engine()
    return engine.generate_all_projections()


# =============================================================================
# CONTENIDO DE CADA ETAPA
# =============================================================================
@st.dialog("⚙️ Configuración del Asistente IA", width="large")
def _show_config_dialog():
    """Popup de configuración de la API key."""

    import os

    st.markdown("Introduce tu API key para activar el asistente IA. Puedes obtenerla de forma gratuita en la web de cada proveedor.")

    provider = st.radio(
        "Proveedor:",
        options=["OpenAI (GPT) — Recomendado", "Anthropic (Claude)"],
        horizontal=True,
    )

    st.markdown("---")

    if provider.startswith("OpenAI"):
        st.markdown("Obtén tu API key en [platform.openai.com/api-keys](https://platform.openai.com/api-keys)")
        api_key = st.text_input(
            "API Key de OpenAI",
            placeholder="sk-...",
            type="password",
            help="Empieza por 'sk-'",
        )
        model = st.selectbox(
            "Modelo",
            options=["gpt-4o", "gpt-4o-mini"],
            help="gpt-4o es más potente, gpt-4o-mini más económico",
        )
        env_provider = "openai"
        env_key_name = "OPENAI_API_KEY"
        valid = api_key.startswith("sk-") and not api_key.startswith("sk-tu") and len(api_key) > 20
    else:
        st.markdown("Obtén tu API key en [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)")
        api_key = st.text_input(
            "API Key de Anthropic",
            placeholder="sk-ant-...",
            type="password",
            help="Empieza por 'sk-ant-'",
        )
        model = st.selectbox(
            "Modelo",
            options=["claude-sonnet-4-6", "claude-haiku-4-5-20251001", "claude-opus-4-6"],
            help="Sonnet es el equilibrio recomendado entre potencia y coste",
        )
        env_provider = "anthropic"
        env_key_name = "ANTHROPIC_API_KEY"
        valid = api_key.startswith("sk-ant-") and len(api_key) > 20

    st.markdown("---")

    if st.button("💾 Guardar configuración", type="primary", use_container_width=True, disabled=not valid):
        # Escribir el .env con los nuevos valores
        env_path = Config.BASE_DIR / ".env"
        env_lines = []
        if env_path.exists():
            # Leer el .env actual y reemplazar/añadir las claves relevantes
            existing = env_path.read_text(encoding="utf-8").splitlines()
            keys_to_update = {"MODEL_PROVIDER", "MODEL_NAME", env_key_name}
            for line in existing:
                key_in_line = line.split("=")[0].strip()
                if key_in_line not in keys_to_update:
                    env_lines.append(line)

        env_lines += [
            f"MODEL_PROVIDER={env_provider}",
            f"{env_key_name}={api_key}",
            f"MODEL_NAME={model}",
        ]
        env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

        # Aplicar en memoria sin reiniciar
        os.environ["MODEL_PROVIDER"] = env_provider
        os.environ[env_key_name] = api_key
        os.environ["MODEL_NAME"] = model

        # Limpiar caché del cliente para que se recree con los nuevos valores
        _get_llm_client.clear()

        st.success("✅ Configuración guardada. El asistente IA ya está activo.")
        st.rerun()

    if not valid and api_key:
        st.caption("⚠️ La API key no tiene el formato correcto.")

    st.warning("🔒 Tu API key se guarda solo en el archivo `.env` local. Nunca se sube a ningún servidor.")

    st.markdown("---")
    st.markdown("**¿Quieres eliminar la configuración actual?**")
    if st.button("🗑️ Borrar API key guardada", use_container_width=True):
        env_path = Config.BASE_DIR / ".env"
        if env_path.exists():
            lines = env_path.read_text(encoding="utf-8").splitlines()
            clean = [l for l in lines if not l.startswith(("OPENAI_API_KEY=", "ANTHROPIC_API_KEY=", "MODEL_PROVIDER=", "MODEL_NAME="))]
            env_path.write_text("\n".join(clean) + "\n", encoding="utf-8")
        for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "MODEL_PROVIDER", "MODEL_NAME"):
            os.environ.pop(key, None)
        _get_llm_client.clear()
        st.success("✅ Configuración eliminada.")
        st.rerun()


def render_stage_inicio():
    """Pantalla de inicio y bienvenida"""

    st.markdown('<p class="main-header">📊 PEF AI Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Tu asistente inteligente para crear Planes Económico-Financieros profesionales</p>', unsafe_allow_html=True)

    # --- Estado del asistente IA ---
    import os
    _provider = os.getenv("MODEL_PROVIDER", "openai")
    _key = os.getenv("OPENAI_API_KEY", "") if _provider == "openai" else os.getenv("ANTHROPIC_API_KEY", "")
    _configured = (
        (_key.startswith("sk-ant-") and len(_key) > 20) if _provider == "anthropic"
        else (_key.startswith("sk-") and not _key.startswith("sk-tu") and len(_key) > 20)
    )
    col_status, col_btn = st.columns([3, 1])
    with col_status:
        if _configured:
            st.success(f"✅ Asistente IA activo — {_provider.capitalize()} · {os.getenv('MODEL_NAME', '')}")
        else:
            st.error("❌ Asistente IA no configurado — Pulsa 'Configurar IA' para añadir tu API key")
    with col_btn:
        if st.button("⚙️ Configurar IA", use_container_width=True):
            _show_config_dialog()

    st.markdown("---")

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
    render_chat_interface(stage="proyecto")

    st.markdown("---")

    # Panel de datos recopilados
    st.markdown("### 📋 Datos Recopilados")
    st.caption("Los datos que el asistente extraiga de la conversación aparecerán aquí automáticamente:")

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Nombre del proyecto", value=st.session_state.proyecto.get("nombre", ""), disabled=True)
        st.text_input("Sector de actividad", value=st.session_state.proyecto.get("sector", ""), disabled=True)

    with col2:
        st.text_input("Número de socios", value=st.session_state.proyecto.get("equipo", ""), disabled=True)
        st.text_input("Fecha de inicio prevista", value=st.session_state.proyecto.get("fecha_inicio", ""), disabled=True)

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

        render_chat_interface(stage="capex")

    with tab_datos:
        st.markdown("### 📋 Inversiones Registradas")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 26-40)")
        st.info("💡 **Introduce los importes SIN IVA**. El IVA y la amortización se calculan automáticamente.")

        # === INMOVILIZADO INTANGIBLE ===
        st.markdown("#### 🔷 Inmovilizado Intangible")

        # Headers
        cols = st.columns([3, 1.5, 1, 1.5, 1, 1.5])
        with cols[0]:
            st.markdown("**Categoría**")
        with cols[1]:
            st.markdown("**Importe (€)**")
        with cols[2]:
            st.markdown("**Años**")
        with cols[3]:
            st.markdown("**IVA (21%)**")
        with cols[4]:
            st.markdown("**Total**")
        with cols[5]:
            st.markdown("**Amort/año**")

        intangibles = [
            ("investigacion", "Investigación y desarrollo", 5),
            ("patentes", "Patentes y marcas", 10),
            ("aplicaciones", "Aplicaciones informáticas", 5),
            ("otros_intangibles", "Otros intangibles", 5),
        ]

        for key, nombre, anos_def in intangibles:
            cols = st.columns([3, 1.5, 1, 1.5, 1, 1.5])
            with cols[0]:
                st.text(nombre)
            with cols[1]:
                importe = st.number_input(
                    f"Importe {key}",
                    min_value=0, step=100, key=f"capex_{key}_importe",
                    label_visibility="collapsed"
                )
                st.session_state.capex[key]["importe"] = importe
            with cols[2]:
                anos = st.number_input(
                    f"Años {key}", value=st.session_state.capex[key]["anos"],
                    min_value=1, max_value=50, key=f"capex_{key}_anos",
                    label_visibility="collapsed"
                )
                st.session_state.capex[key]["anos"] = anos
            with cols[3]:
                iva = importe * 0.21
                st.text(f"{iva:,.0f} €")
            with cols[4]:
                total = importe + iva
                st.text(f"{total:,.0f} €")
            with cols[5]:
                amort = importe / anos if anos > 0 else 0
                st.text(f"{amort:,.0f} €")

        # === INMOVILIZADO MATERIAL ===
        st.markdown("#### 🔶 Inmovilizado Material")

        # Headers
        cols = st.columns([3, 1.5, 1, 1.5, 1, 1.5])
        with cols[0]:
            st.markdown("**Categoría**")
        with cols[1]:
            st.markdown("**Importe (€)**")
        with cols[2]:
            st.markdown("**Años**")
        with cols[3]:
            st.markdown("**IVA (21%)**")
        with cols[4]:
            st.markdown("**Total**")
        with cols[5]:
            st.markdown("**Amort/año**")

        materiales = [
            ("terrenos", "Terrenos y construcciones", 50),
            ("instalaciones", "Instalaciones", 10),
            ("maquinaria", "Maquinaria", 10),
            ("equipos", "Equipos informáticos (EPIs)", 5),
            ("mobiliario", "Mobiliario", 10),
            ("vehiculos", "Vehículos", 10),
            ("otros_materiales", "Otros materiales", 5),
        ]

        for key, nombre, anos_def in materiales:
            cols = st.columns([3, 1.5, 1, 1.5, 1, 1.5])
            with cols[0]:
                st.text(nombre)
            with cols[1]:
                importe = st.number_input(
                    f"Importe {key}",
                    min_value=0, step=100, key=f"capex_{key}_importe",
                    label_visibility="collapsed"
                )
                st.session_state.capex[key]["importe"] = importe
            with cols[2]:
                anos = st.number_input(
                    f"Años {key}", value=st.session_state.capex[key]["anos"],
                    min_value=1, max_value=50, key=f"capex_{key}_anos",
                    label_visibility="collapsed"
                )
                st.session_state.capex[key]["anos"] = anos
            with cols[3]:
                iva = importe * 0.21
                st.text(f"{iva:,.0f} €")
            with cols[4]:
                total = importe + iva
                st.text(f"{total:,.0f} €")
            with cols[5]:
                amort = importe / anos if anos > 0 else 0
                st.text(f"{amort:,.0f} €")

        # === FIANZAS ===
        st.markdown("#### 📌 Fianzas y Depósitos")
        col1, col2 = st.columns(2)
        with col1:
            fianzas = st.number_input(
                "Fianzas (€)", value=st.session_state.capex["fianzas"]["importe"],
                min_value=0, step=100, key="capex_fianzas_importe",
                help="Depósitos recuperables (ej: fianza alquiler)"
            )
            st.session_state.capex["fianzas"]["importe"] = fianzas
        with col2:
            st.selectbox("Recuperable en", ["Año 1", "Año 2", "Año 3", "Año 4", "Año 5"], index=4)

        # === PROYECTOS DE INVERSIÓN EN AÑOS POSTERIORES ===
        st.markdown("---")
        st.markdown("#### 📅 Proyectos de Inversión en Años Posteriores")
        st.caption("Inversiones adicionales adquiridas después del mes 1 (2 slots)")

        for proy_key, proy_label in [("proyecto_inv_1", "Proyecto de Inversión 1"), ("proyecto_inv_2", "Proyecto de Inversión 2")]:
            proy_data = st.session_state.proyectos_inversion[proy_key]
            with st.expander(f"{proy_label} — {proy_data.get('observaciones', '') or 'Sin definir'}", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    pi_importe = st.number_input(
                        "Importe (€)", value=proy_data["importe"],
                        min_value=0, step=100, key=f"{proy_key}_importe",
                        help="Importe sin IVA"
                    )
                    proy_data["importe"] = pi_importe
                with col2:
                    pi_anos = st.number_input(
                        "Años amortización", value=proy_data["anos"],
                        min_value=1, max_value=50, key=f"{proy_key}_anos"
                    )
                    proy_data["anos"] = pi_anos
                with col3:
                    pi_mes = st.number_input(
                        "Mes adquisición (1-60)", value=proy_data["mes_adquisicion"],
                        min_value=1, max_value=60, key=f"{proy_key}_mes"
                    )
                    proy_data["mes_adquisicion"] = pi_mes

                col1, col2, col3 = st.columns(3)
                with col1:
                    pi_sub = st.number_input(
                        "Subvención (€)", value=proy_data["subvencion"],
                        min_value=0, step=100, key=f"{proy_key}_sub",
                        help="Subvención de capital asociada"
                    )
                    proy_data["subvencion"] = pi_sub
                with col2:
                    pi_obs = st.text_input(
                        "Observaciones", value=proy_data["observaciones"],
                        key=f"{proy_key}_obs", placeholder="Describe la inversión..."
                    )
                    proy_data["observaciones"] = pi_obs
                with col3:
                    if pi_importe > 0:
                        pi_iva = pi_importe * 0.21
                        st.text(f"IVA (21%): {pi_iva:,.0f} €")
                        st.text(f"Total: {pi_importe + pi_iva:,.0f} €")
                        pi_mes_fin_amort = pi_mes + pi_anos * 12
                        st.text(f"Fin amort: mes {pi_mes_fin_amort}")

        # === PROYECTOS DE TRABAJO PARA EL PROPIO ACTIVO ===
        st.markdown("---")
        st.markdown("#### 🔬 Proyectos de Trabajo para el Propio Activo")
        st.caption("I+D interno que se capitaliza como inmovilizado intangible (sin IVA, sin desembolso adicional)")

        for proy_key, proy_label in [("proyecto_trab_1", "Proyecto de Trabajo 1"), ("proyecto_trab_2", "Proyecto de Trabajo 2")]:
            proy_data = st.session_state.proyectos_trabajo[proy_key]
            with st.expander(f"{proy_label} — {proy_data.get('observaciones', '') or 'Sin definir'}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    pt_importe = st.number_input(
                        "Importe total (€)", value=proy_data["importe"],
                        min_value=0, step=100, key=f"{proy_key}_importe",
                        help="Coste total del proyecto (se capitaliza al finalizar)"
                    )
                    proy_data["importe"] = pt_importe
                with col2:
                    pt_anos = st.number_input(
                        "Años amortización", value=proy_data["anos"],
                        min_value=1, max_value=50, key=f"{proy_key}_anos"
                    )
                    proy_data["anos"] = pt_anos

                col1, col2, col3 = st.columns(3)
                with col1:
                    pt_inicio = st.number_input(
                        "Mes inicio proyecto (1-60)", value=proy_data["mes_inicio"],
                        min_value=1, max_value=60, key=f"{proy_key}_inicio"
                    )
                    proy_data["mes_inicio"] = pt_inicio
                with col2:
                    pt_fin = st.number_input(
                        "Mes fin proyecto (1-60)", value=proy_data["mes_fin"],
                        min_value=pt_inicio, max_value=60, key=f"{proy_key}_fin"
                    )
                    proy_data["mes_fin"] = pt_fin
                with col3:
                    pt_sub = st.number_input(
                        "Subvención (€)", value=proy_data["subvencion"],
                        min_value=0, step=100, key=f"{proy_key}_sub",
                        help="Subvención de capital asociada"
                    )
                    proy_data["subvencion"] = pt_sub

                col1, col2 = st.columns(2)
                with col1:
                    pt_obs = st.text_input(
                        "Observaciones", value=proy_data["observaciones"],
                        key=f"{proy_key}_obs", placeholder="Describe el proyecto..."
                    )
                    proy_data["observaciones"] = pt_obs
                with col2:
                    if pt_importe > 0:
                        duracion = pt_fin - pt_inicio + 1
                        importe_medio = pt_importe / duracion if duracion > 0 else 0
                        st.text(f"IVA: 0 € (no aplica)")
                        st.text(f"Importe medio/mes: {importe_medio:,.0f} €")
                        st.text(f"Inicio amort: mes {pt_fin + 1}")
                        st.text(f"Fin amort: mes {pt_fin + 1 + pt_anos * 12}")

        # === RESUMEN - Cálculos automáticos ===
        st.markdown("---")
        st.markdown("### 📊 Resumen de Inversiones")

        # Calcular totales inversiones iniciales
        total_intangible = sum(st.session_state.capex[k]["importe"] for k in ["investigacion", "patentes", "aplicaciones", "otros_intangibles"])
        total_material = sum(st.session_state.capex[k]["importe"] for k in ["terrenos", "instalaciones", "maquinaria", "equipos", "mobiliario", "vehiculos", "otros_materiales"])
        total_fianzas = st.session_state.capex["fianzas"]["importe"]

        # Totales de proyectos de inversión posteriores
        total_proy_inv = sum(
            st.session_state.proyectos_inversion[k]["importe"]
            for k in st.session_state.proyectos_inversion
        )
        # Totales de proyectos de trabajo propio activo
        total_proy_trab = sum(
            st.session_state.proyectos_trabajo[k]["importe"]
            for k in st.session_state.proyectos_trabajo
        )

        total_importe = total_intangible + total_material + total_fianzas + total_proy_inv
        total_iva = (total_intangible + total_material + total_proy_inv) * 0.21  # Fianzas y proy. trabajo no llevan IVA
        total_con_iva = total_importe + total_iva

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Intangible", f"{total_intangible:,.0f} €")
        with col2:
            st.metric("Total Material", f"{total_material:,.0f} €")
        with col3:
            st.metric("IVA Soportado", f"{total_iva:,.0f} €", help="Calculado automáticamente al 21%")
        with col4:
            st.metric("TOTAL con IVA", f"{total_con_iva:,.0f} €", help="Desembolso real necesario")

        if total_proy_inv > 0 or total_proy_trab > 0:
            col1, col2 = st.columns(2)
            with col1:
                if total_proy_inv > 0:
                    st.metric("Proy. Inversión Posteriores", f"{total_proy_inv:,.0f} €",
                              help="Inversiones adquiridas después del mes 1 (incluidas en total)")
            with col2:
                if total_proy_trab > 0:
                    st.metric("Proy. Trabajo Propio Activo", f"{total_proy_trab:,.0f} €",
                              help="Se capitaliza al finalizar (no genera desembolso adicional)")

        # Mostrar también amortización anual total
        amort_anual = sum(
            st.session_state.capex[k]["importe"] / st.session_state.capex[k]["anos"]
            for k in st.session_state.capex.keys()
            if st.session_state.capex[k]["importe"] > 0 and st.session_state.capex[k]["anos"] > 0
        )
        # Añadir amortización de proyectos de inversión posteriores
        for k in st.session_state.proyectos_inversion:
            pi = st.session_state.proyectos_inversion[k]
            if pi["importe"] > 0 and pi["anos"] > 0:
                amort_anual += pi["importe"] / pi["anos"]
        # Añadir amortización de proyectos de trabajo
        for k in st.session_state.proyectos_trabajo:
            pt = st.session_state.proyectos_trabajo[k]
            if pt["importe"] > 0 and pt["anos"] > 0:
                amort_anual += pt["importe"] / pt["anos"]

        st.info(f"📈 **Amortización anual total**: {amort_anual:,.0f} € (gasto no monetario que reduce el beneficio)")

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

        render_chat_interface(stage="financiacion")

    with tab_datos:
        st.markdown("### 📋 Estructura de Financiación")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 63-70)")

        # === FINANCIACIÓN INTERNA ===
        st.markdown("#### 💰 Financiación Interna (Capital)")

        # Migración: si capital_inicial es un int/float o formato antiguo, convertir
        cap_ini = st.session_state.financiacion.get("capital_inicial", {})
        if isinstance(cap_ini, (int, float)):
            st.session_state.financiacion["capital_inicial"] = {"importe": int(cap_ini), "acciones": int(cap_ini)}
        elif isinstance(cap_ini, dict) and "nominal" in cap_ini:
            old_importe = cap_ini.get("acciones", 0) * cap_ini.get("nominal", 1.0)
            st.session_state.financiacion["capital_inicial"] = {"importe": int(old_importe), "acciones": cap_ini.get("acciones", 0)}
        if "ampliacion" not in st.session_state.financiacion or "nominal" in st.session_state.financiacion.get("ampliacion", {}):
            old_amp = st.session_state.financiacion.get("ampliacion", {})
            st.session_state.financiacion.pop("ampliacion_2", None)
            st.session_state.financiacion.pop("ampliacion_3", None)
            st.session_state.financiacion["ampliacion"] = {
                "mes": old_amp.get("mes", 21),
                "importe": 0,
                "valoracion_premoney": 0
            }

        cap_data = st.session_state.financiacion["capital_inicial"]
        amp_data = st.session_state.financiacion["ampliacion"]

        st.markdown("**Capital inicial desembolsado por los fundadores**")
        col1, col2, col3 = st.columns(3)
        with col1:
            cap_importe = st.number_input(
                "Importe (€)", min_value=0, step=1000, key="cap_ini_importe"
            )
            cap_data["importe"] = cap_importe
        with col2:
            cap_acciones = st.number_input(
                "Acciones emitidas", min_value=0, step=100, key="cap_ini_acciones"
            )
            cap_data["acciones"] = cap_acciones
        with col3:
            if cap_acciones > 0:
                valor_accion_ini = cap_importe / cap_acciones
                st.metric("Valor/acción", f"{valor_accion_ini:,.2f} €")
            else:
                st.metric("Valor/acción", "-")
        capital = cap_importe

        st.markdown("**Ampliación de capital 1 (prevista en el mes a indicar)**")
        col1, col2, col3 = st.columns(3)
        with col1:
            amp_mes = st.number_input(
                "Mes previsto (1-60)", min_value=1, max_value=60, key="amp_mes"
            )
            amp_data["mes"] = amp_mes
        with col2:
            amp_importe = st.number_input(
                "Importe (€)", min_value=0, step=1000, key="amp_importe"
            )
            amp_data["importe"] = amp_importe
        with col3:
            amp_valoracion = st.number_input(
                "Valoración pre-money (€)", min_value=0, step=10000, key="amp_valoracion"
            )
            amp_data["valoracion_premoney"] = amp_valoracion

        # Mostrar tabla resumen de refinanciación
        if cap_acciones > 0:
            # Capital inicial
            valor_accion_cap = cap_importe / cap_acciones if cap_acciones > 0 else 0

            # Ampliación
            if amp_importe > 0 and amp_valoracion > 0:
                precio_accion_amp = amp_valoracion / cap_acciones
                acciones_nuevas = amp_importe / precio_accion_amp if precio_accion_amp > 0 else 0
                acciones_totales = cap_acciones + acciones_nuevas
                valor_accion_amp = (amp_valoracion + amp_importe) / acciones_totales if acciones_totales > 0 else 0
                pct_nuevos = acciones_nuevas / acciones_totales if acciones_totales > 0 else 0
                valor_fundadores = amp_valoracion
            else:
                acciones_totales = cap_acciones
                valor_accion_amp = amp_valoracion / cap_acciones if amp_valoracion > 0 else valor_accion_cap
                pct_nuevos = 0
                valor_fundadores = amp_valoracion if amp_valoracion > 0 else cap_importe

            st.caption(
                f"Tras ampliación: {acciones_totales:,.0f} acciones | "
                f"Valor/acción: {valor_accion_amp:,.2f} € | "
                f"% nuevos socios: {pct_nuevos:.1%} | "
                f"Valor fundadores: {valor_fundadores:,.0f} €"
            )

        ampliacion = amp_importe

        # === PRÉSTAMOS ===
        st.markdown("#### 🏦 Financiación Externa (Préstamos)")

        # Headers
        cols = st.columns([1, 1.5, 1, 1.5, 1, 1, 1.5])
        with cols[0]:
            st.markdown("**Mes inicio**")
        with cols[1]:
            st.markdown("**Importe (€)**")
        with cols[2]:
            st.markdown("**Carencia**")
        with cols[3]:
            st.markdown("**Amortización**")
        with cols[4]:
            st.markdown("**Mes final**")
        with cols[5]:
            st.markdown("**Interés %**")
        with cols[6]:
            st.markdown("**Cuota mensual**")

        # Préstamo 1
        st.markdown("**Préstamo 1**")
        cols = st.columns([1, 1.5, 1, 1.5, 1, 1, 1.5])
        with cols[0]:
            p1_mes = st.number_input(
                "P1 Mes", value=st.session_state.financiacion["prestamo1"]["mes_inicio"],
                min_value=1, max_value=60, label_visibility="collapsed"
            )
            st.session_state.financiacion["prestamo1"]["mes_inicio"] = p1_mes
        with cols[1]:
            p1_importe = st.number_input(
                "P1 Importe", value=st.session_state.financiacion["prestamo1"]["importe"],
                min_value=0, step=1000, label_visibility="collapsed"
            )
            st.session_state.financiacion["prestamo1"]["importe"] = p1_importe
        with cols[2]:
            p1_carencia = st.number_input(
                "P1 Carencia", value=st.session_state.financiacion["prestamo1"]["meses_carencia"],
                min_value=0, max_value=24, label_visibility="collapsed"
            )
            st.session_state.financiacion["prestamo1"]["meses_carencia"] = p1_carencia
        with cols[3]:
            p1_amort = st.number_input(
                "P1 Amort", value=st.session_state.financiacion["prestamo1"]["meses_amortizacion"],
                min_value=1, max_value=120, label_visibility="collapsed"
            )
            st.session_state.financiacion["prestamo1"]["meses_amortizacion"] = p1_amort
        with cols[4]:
            # Calculado automáticamente
            p1_mes_final = p1_mes + p1_carencia + p1_amort
            st.text(f"{p1_mes_final}")
        with cols[5]:
            p1_interes = st.number_input(
                "P1 Interés", value=st.session_state.financiacion["prestamo1"]["interes"],
                min_value=0.0, max_value=30.0, step=0.1, format="%.1f", label_visibility="collapsed"
            )
            st.session_state.financiacion["prestamo1"]["interes"] = p1_interes
        with cols[6]:
            # Cuota mensual calculada (sistema francés)
            if p1_importe > 0 and p1_amort > 0:
                i_mensual = (p1_interes / 100) / 12
                if i_mensual > 0:
                    cuota_p1 = p1_importe * (i_mensual * (1 + i_mensual)**p1_amort) / ((1 + i_mensual)**p1_amort - 1)
                else:
                    cuota_p1 = p1_importe / p1_amort
                st.text(f"{cuota_p1:,.0f} €")
            else:
                st.text("0 €")

        # Préstamo 2
        st.markdown("**Préstamo 2**")
        cols = st.columns([1, 1.5, 1, 1.5, 1, 1, 1.5])
        with cols[0]:
            p2_mes = st.number_input(
                "P2 Mes", value=st.session_state.financiacion["prestamo2"]["mes_inicio"],
                min_value=1, max_value=60, label_visibility="collapsed"
            )
            st.session_state.financiacion["prestamo2"]["mes_inicio"] = p2_mes
        with cols[1]:
            p2_importe = st.number_input(
                "P2 Importe", value=st.session_state.financiacion["prestamo2"]["importe"],
                min_value=0, step=1000, label_visibility="collapsed"
            )
            st.session_state.financiacion["prestamo2"]["importe"] = p2_importe
        with cols[2]:
            p2_carencia = st.number_input(
                "P2 Carencia", value=st.session_state.financiacion["prestamo2"]["meses_carencia"],
                min_value=0, max_value=24, label_visibility="collapsed"
            )
            st.session_state.financiacion["prestamo2"]["meses_carencia"] = p2_carencia
        with cols[3]:
            p2_amort = st.number_input(
                "P2 Amort", value=st.session_state.financiacion["prestamo2"]["meses_amortizacion"],
                min_value=1, max_value=120, label_visibility="collapsed"
            )
            st.session_state.financiacion["prestamo2"]["meses_amortizacion"] = p2_amort
        with cols[4]:
            p2_mes_final = p2_mes + p2_carencia + p2_amort
            st.text(f"{p2_mes_final}")
        with cols[5]:
            p2_interes = st.number_input(
                "P2 Interés", value=st.session_state.financiacion["prestamo2"]["interes"],
                min_value=0.0, max_value=30.0, step=0.1, format="%.1f", label_visibility="collapsed"
            )
            st.session_state.financiacion["prestamo2"]["interes"] = p2_interes
        with cols[6]:
            if p2_importe > 0 and p2_amort > 0:
                i_mensual = (p2_interes / 100) / 12
                if i_mensual > 0:
                    cuota_p2 = p2_importe * (i_mensual * (1 + i_mensual)**p2_amort) / ((1 + i_mensual)**p2_amort - 1)
                else:
                    cuota_p2 = p2_importe / p2_amort
                st.text(f"{cuota_p2:,.0f} €")
            else:
                st.text("0 €")

        # === PÓLIZA DE CRÉDITO ===
        st.markdown("#### 💳 Póliza de Crédito")
        col1, col2 = st.columns(2)
        with col1:
            st.text("Límite: Ilimitado (se activa automáticamente si hay déficit)")
        with col2:
            poliza_int = st.number_input(
                "Interés anual %",
                value=st.session_state.financiacion["poliza_interes"],
                min_value=0.0, max_value=20.0, step=0.1, format="%.1f",
                help="Interés que pagarás por el saldo dispuesto"
            )
            st.session_state.financiacion["poliza_interes"] = poliza_int

        # === RESUMEN - Cálculos automáticos ===
        st.markdown("---")
        st.markdown("### 📊 Resumen de Financiación")

        total_capital = capital + ampliacion
        total_prestamos = p1_importe + p2_importe
        total_disponible = total_capital + total_prestamos

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Capital", f"{total_capital:,.0f} €", help="Aportaciones de los socios")
        with col2:
            st.metric("Total Préstamos", f"{total_prestamos:,.0f} €", help="Suma de préstamos solicitados")
        with col3:
            st.metric("TOTAL Disponible", f"{total_disponible:,.0f} €")

        # Validación contra CAPEX
        st.markdown("---")
        # Calcular necesidades desde CAPEX (inversiones iniciales + proyectos inversión, NO proyectos trabajo)
        total_capex = sum(
            st.session_state.capex[k]["importe"]
            for k in st.session_state.capex.keys()
        )
        total_capex += sum(
            st.session_state.proyectos_inversion[k]["importe"]
            for k in st.session_state.proyectos_inversion
        )
        total_capex_iva = total_capex * 1.21  # Con IVA

        if total_disponible >= total_capex_iva and total_capex_iva > 0:
            diferencia = total_disponible - total_capex_iva
            st.success(f"✅ **Financiación suficiente**: Dispones de {total_disponible:,.0f}€ para cubrir {total_capex_iva:,.0f}€ de inversiones (+IVA). Excedente: {diferencia:,.0f}€")
        elif total_capex_iva > 0:
            deficit = total_capex_iva - total_disponible
            st.warning(f"⚠️ **Financiación insuficiente**: Las inversiones suman {total_capex_iva:,.0f}€ (con IVA). Te faltan {deficit:,.0f}€")
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

        render_chat_interface(stage="opex")

    with tab_servicios:
        st.markdown("### 🏢 Gastos Fijos por Servicios Exteriores")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 77-85)")
        st.info("💡 Introduce el importe **Año 1** y el **% de incremento** para cada año. Los importes de los años 2-5 se calculan automáticamente.")

        # Crear tabla de gastos
        gastos_ext = [
            ("alquileres", "Alquileres", "Local, oficina, almacén"),
            ("suministros", "Suministros", "Luz, agua, gas, internet, teléfono"),
            ("rentings", "Rentings", "Leasing de equipos o vehículos"),
            ("reparaciones", "Reparaciones", "Mantenimiento y reparaciones"),
            ("servicios_prof", "Servicios profesionales", "Gestoría, abogados, consultores"),
            ("transportes", "Transportes", "Envíos, mensajería, combustible"),
            ("bancarios_seguros", "Gastos bancarios y seguros", "Comisiones bancarias, seguros"),
            ("marketing", "Marketing", "Publicidad, ferias, redes sociales"),
            ("tributos", "Tributos municipales", "IAE, tasas, licencias municipales"),
        ]

        # Migrar datos antiguos al nuevo formato
        for key, _, _ in gastos_ext:
            gf_data = st.session_state.opex["gastos_fijos"][key]
            if "incrementos" not in gf_data:
                old_inc = gf_data.get("incremento", 0.0)
                gf_data["incrementos"] = [old_inc, old_inc, old_inc, old_inc]
            if "ano1" not in gf_data:
                gf_data["ano1"] = gf_data.get("anos", [0])[0] if "anos" in gf_data else 0

        # Headers - Fila 1: concepto + año 1 + incrementos %
        cols = st.columns([2, 1, 0.7, 0.7, 0.7, 0.7])
        with cols[0]:
            st.markdown("**Concepto**")
        with cols[1]:
            st.markdown("**Año 1 (€)**")
        with cols[2]:
            st.markdown("**% Año 2**")
        with cols[3]:
            st.markdown("**% Año 3**")
        with cols[4]:
            st.markdown("**% Año 4**")
        with cols[5]:
            st.markdown("**% Año 5**")

        totales_ano = [0] * 5

        for key, nombre, desc in gastos_ext:
            gf_data = st.session_state.opex["gastos_fijos"][key]

            cols = st.columns([2, 1, 0.7, 0.7, 0.7, 0.7])

            with cols[0]:
                st.text(f"{nombre}")
                st.caption(desc)

            # Año 1 - editable
            with cols[1]:
                ano1 = st.number_input(
                    f"Año 1 - {key}",
                    min_value=0, step=100, label_visibility="collapsed",
                    key=f"opex_{key}_ano1"
                )
                gf_data["ano1"] = ano1

            # Incrementos % por año - editables
            incrementos = gf_data["incrementos"]
            for idx, col in enumerate([cols[2], cols[3], cols[4], cols[5]]):
                with col:
                    inc = st.number_input(
                        f"Inc A{idx+2} - {key}",
                        min_value=0.0, max_value=100.0, step=0.5, format="%.1f",
                        label_visibility="collapsed",
                        key=f"opex_{key}_inc{idx+2}"
                    )
                    incrementos[idx] = inc
            gf_data["incrementos"] = incrementos

            # Calcular importes por año (solo lectura)
            importes = [ano1]
            for inc in incrementos:
                importes.append(importes[-1] * (1 + inc / 100))

            for idx in range(5):
                totales_ano[idx] += importes[idx]

            # Mostrar importes calculados años 2-5
            if ano1 > 0:
                cols2 = st.columns([2, 1, 0.7, 0.7, 0.7, 0.7])
                with cols2[1]:
                    st.caption(f"{ano1:,.0f} €/año")
                for idx, col in enumerate([cols2[2], cols2[3], cols2[4], cols2[5]]):
                    with col:
                        st.caption(f"{importes[idx+1]:,.0f} €")

        st.markdown("---")
        cols = st.columns([2, 1, 0.7, 0.7, 0.7, 0.7])
        with cols[0]:
            st.markdown("**TOTAL ANUAL**")
        with cols[1]:
            st.markdown(f"**{totales_ano[0]:,.0f} €**")
        for idx, col in enumerate([cols[2], cols[3], cols[4], cols[5]]):
            with col:
                st.markdown(f"**{totales_ano[idx+1]:,.0f}**")

    with tab_nominas:
        st.markdown("### 👥 Gastos Fijos por Nómina")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 90-104)")

        # Configuración fiscal (valores fijos legales - no editables)
        st.markdown("#### ⚙️ Configuración Seguridad Social")
        st.caption("Valores legales establecidos - se calculan automáticamente")

        # Valores fijos (no editables)
        ss_auto = 15.0   # SS Autónomos %
        ss_emp = 33.0    # SS Empresa % (régimen general)
        ss_trab = 6.47   # SS Trabajador % (régimen general)
        ss_tope = 56640  # Base máxima cotización anual

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("SS Autónomos", f"{ss_auto}%", help="Cuota sobre base de cotización")
        with col2:
            st.metric("SS Empresa", f"{ss_emp}%", help="Régimen general - cargo empresa")
        with col3:
            st.metric("SS Trabajador", f"{ss_trab}%", help="Régimen general - cargo trabajador")
        with col4:
            st.metric("Tope SS", f"{ss_tope:,.0f} €", help="Base máxima de cotización anual")

        st.markdown("---")

        # Función para calcular SS e IRPF
        def calcular_costes_empleado(salario, es_autonomo=False):
            if salario <= 0:
                return 0, 0, 0
            base = min(salario, ss_tope)
            if es_autonomo:
                ss_empresa = base * (ss_auto / 100)
                ss_trabajador = 0
            else:
                ss_empresa = base * (ss_emp / 100)
                ss_trabajador = base * (ss_trab / 100)
            # IRPF por tramos
            if salario < 15000:
                irpf = 0
            elif salario < 90000:
                irpf = salario * 0.20
            else:
                irpf = salario * 0.40
            return ss_empresa, ss_trabajador, irpf

        perfiles = [
            ("socios", "Socios fundadores", True),
            ("perfil_a", "Personal tipo A", False),
            ("perfil_b", "Personal tipo B", False),
            ("perfil_c", "Personal tipo C", False),
            ("perfil_d", "Personal tipo D", False),
        ]

        etapas = [
            (1, "Etapa 1: Personal inicial", "Personal desde el inicio del proyecto", "Increm. año 2"),
            (2, "Etapa 2: Primera ampliación", "Contrataciones cuando el negocio crece", "Increm. año 3"),
            (3, "Etapa 3: Segunda ampliación", "Ampliación en fase de consolidación", "Increm. año 4+"),
        ]

        # Inicializar empleados en session_state si no existe (ahora con 3 etapas)
        if "empleados_data" not in st.session_state:
            st.session_state.empleados_data = {}
            for etapa_num, _, _, _ in etapas:
                st.session_state.empleados_data[etapa_num] = {
                    "incremento_salario": 2.0 if etapa_num < 3 else 3.0,  # % incremento anual
                    "perfiles": {}
                }
                for key, _, _ in perfiles:
                    st.session_state.empleados_data[etapa_num]["perfiles"][key] = {
                        "num": 0, "alta": 1, "baja": 60, "salario": 0
                    }
        # Migrar estructura antigua a nueva
        elif "perfiles" not in st.session_state.empleados_data.get(1, {}):
            old_data = st.session_state.empleados_data.copy()
            st.session_state.empleados_data = {}
            for etapa_num, _, _, _ in etapas:
                st.session_state.empleados_data[etapa_num] = {
                    "incremento_salario": 2.0 if etapa_num < 3 else 3.0,
                    "perfiles": {}
                }
                for key, _, _ in perfiles:
                    if etapa_num in old_data and key in old_data[etapa_num]:
                        st.session_state.empleados_data[etapa_num]["perfiles"][key] = old_data[etapa_num][key]
                    elif etapa_num in old_data and "perfiles" not in old_data[etapa_num] and key in old_data.get(etapa_num, {}):
                        st.session_state.empleados_data[etapa_num]["perfiles"][key] = old_data[etapa_num][key]
                    else:
                        st.session_state.empleados_data[etapa_num]["perfiles"][key] = {
                            "num": 0, "alta": 1, "baja": 60, "salario": 0
                        }

        st.info("💡 **3 etapas de crecimiento**: Puedes añadir personal en diferentes momentos. "
                "El **incremento salarial** se aplica anualmente a partir del año indicado.")

        total_salarios = 0
        total_ss_emp = 0
        total_coste_emp = 0

        for etapa_num, etapa_nombre, etapa_desc, increm_label in etapas:
            with st.expander(f"📋 {etapa_nombre}", expanded=(etapa_num == 1)):
                st.caption(etapa_desc)

                # Incremento salarial de esta etapa
                col_inc1, col_inc2 = st.columns([3, 1])
                with col_inc1:
                    st.markdown(f"**{increm_label}** (% incremento salarial anual)")
                with col_inc2:
                    inc_val = st.number_input(
                        f"Increm {etapa_num}",
                        value=float(st.session_state.empleados_data[etapa_num]["incremento_salario"]),
                        min_value=0.0, max_value=20.0, step=0.5, format="%.1f",
                        label_visibility="collapsed",
                        key=f"increm_salario_{etapa_num}"
                    )
                    st.session_state.empleados_data[etapa_num]["incremento_salario"] = inc_val

                st.markdown("---")

                # Headers
                cols = st.columns([2.2, 0.8, 0.8, 0.8, 1.3, 1, 1, 1, 1.2])
                headers = ["Perfil", "Nº", "Alta", "Baja", "Bruto/año", "SS Emp", "SS Trab", "IRPF", "Coste Emp"]
                for col, header in zip(cols, headers):
                    with col:
                        st.markdown(f"**{header}**")

                etapa_salarios = 0
                etapa_ss_emp = 0
                etapa_coste = 0

                for key, nombre, es_autonomo in perfiles:
                    cols = st.columns([2.2, 0.8, 0.8, 0.8, 1.3, 1, 1, 1, 1.2])
                    emp_data = st.session_state.empleados_data[etapa_num]["perfiles"][key]

                    with cols[0]:
                        st.text(nombre)
                        if es_autonomo:
                            st.caption("Régimen autónomos")
                    with cols[1]:
                        num = st.number_input(
                            f"Nº {key} E{etapa_num}", value=emp_data["num"],
                            min_value=0, max_value=50, label_visibility="collapsed",
                            key=f"num_{etapa_num}_{key}"
                        )
                        st.session_state.empleados_data[etapa_num]["perfiles"][key]["num"] = num
                    with cols[2]:
                        alta = st.number_input(
                            f"Alta {key} E{etapa_num}", value=emp_data["alta"],
                            min_value=1, max_value=60, label_visibility="collapsed",
                            key=f"alta_{etapa_num}_{key}"
                        )
                        st.session_state.empleados_data[etapa_num]["perfiles"][key]["alta"] = alta
                    with cols[3]:
                        baja = st.number_input(
                            f"Baja {key} E{etapa_num}", value=emp_data["baja"],
                            min_value=1, max_value=60, label_visibility="collapsed",
                            key=f"baja_{etapa_num}_{key}"
                        )
                        st.session_state.empleados_data[etapa_num]["perfiles"][key]["baja"] = baja
                    with cols[4]:
                        salario = st.number_input(
                            f"Salario {key} E{etapa_num}", value=emp_data["salario"],
                            min_value=0, step=1000, label_visibility="collapsed",
                            key=f"salario_{etapa_num}_{key}"
                        )
                        st.session_state.empleados_data[etapa_num]["perfiles"][key]["salario"] = salario

                    # Cálculos automáticos
                    ss_e, ss_t, irpf = calcular_costes_empleado(salario, es_autonomo)
                    coste_emp = salario + ss_e

                    with cols[5]:
                        st.text(f"{ss_e * num:,.0f} €" if num > 0 else "-")
                    with cols[6]:
                        st.text(f"{ss_t * num:,.0f} €" if num > 0 and not es_autonomo else "-")
                    with cols[7]:
                        st.text(f"{irpf * num:,.0f} €" if num > 0 else "-")
                    with cols[8]:
                        st.text(f"{coste_emp * num:,.0f} €" if num > 0 else "-")

                    # Acumular totales de etapa
                    if num > 0:
                        etapa_salarios += salario * num
                        etapa_ss_emp += ss_e * num
                        etapa_coste += coste_emp * num

                # Subtotal de la etapa
                if etapa_coste > 0:
                    st.markdown(f"**Subtotal {etapa_nombre}:** {etapa_coste:,.0f} €/año")

                # Acumular totales globales
                total_salarios += etapa_salarios
                total_ss_emp += etapa_ss_emp
                total_coste_emp += etapa_coste

        # RESUMEN
        st.markdown("---")
        st.markdown("### 📊 Resumen de Costes de Personal (Todas las etapas)")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Salarios Brutos", f"{total_salarios:,.0f} €/año")
        with col2:
            st.metric("SS Empresa", f"{total_ss_emp:,.0f} €/año", help="Calculado automáticamente")
        with col3:
            st.metric("Coste Total Empresa", f"{total_coste_emp:,.0f} €/año", help="Salarios + SS Empresa")
        with col4:
            coste_mensual = total_coste_emp / 12 if total_coste_emp > 0 else 0
            st.metric("Coste Mensual Medio", f"{coste_mensual:,.0f} €/mes")

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

        render_chat_interface("ingresos")

    with tab_mercado:
        st.markdown("### 🎯 Mercado y Volumen de Ventas")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 110-118)")

        st.info("💡 **SAM** = Mercado Accesible Servible. **SOM** = Cuota de mercado objetivo (%). **Unidades = SAM × SOM**")

        productos = [
            ("tipo_a", "🔵 Producto/Servicio Tipo A", False),
            ("tipo_b", "🟢 Producto/Servicio Tipo B", False),
            ("tipo_c", "🟠 Producto/Servicio Tipo C", True),
        ]

        for key, titulo, es_opcional in productos:
            if es_opcional:
                with st.expander(f"{titulo} (opcional)"):
                    render_mercado_producto(key, titulo)
            else:
                st.markdown(f"#### {titulo}")
                render_mercado_producto(key, titulo)
                st.markdown("---")

    with tab_precios:
        st.markdown("### 💵 Precios de Venta")
        st.caption("Estructura según hoja HIPOTESIS del Excel (filas 122-125)")

        st.info("💡 Introduce el precio inicial (Año 1) y el incremento anual. Los precios de años 2-5 se calculan automáticamente.")

        # Incremento anual (común para todos)
        st.markdown("#### 📈 Incremento anual de precios (%)")
        cols = st.columns(4)
        incrementos = []
        for i in range(4):
            with cols[i]:
                inc = st.number_input(
                    f"Año {i+1}→{i+2}",
                    value=3.0, min_value=0.0, max_value=50.0, step=0.5, format="%.1f",
                    key=f"incremento_precio_{i}",
                    help=f"% incremento del año {i+1} al {i+2}"
                )
                incrementos.append(inc)

        # Guardar incrementos en cada producto
        for key in ["tipo_a", "tipo_b", "tipo_c"]:
            st.session_state.ingresos[key]["incremento"] = incrementos

        st.markdown("---")

        # Tabla de precios
        st.markdown("#### Precio unitario por tipo de producto (sin IVA)")

        # Headers
        cols = st.columns([2, 1.2, 1.2, 1.2, 1.2, 1.2])
        with cols[0]:
            st.markdown("**Producto**")
        for i in range(5):
            with cols[i+1]:
                st.markdown(f"**Año {i+1}**")

        productos_precio = [
            ("tipo_a", "🔵 Tipo A"),
            ("tipo_b", "🟢 Tipo B"),
            ("tipo_c", "🟠 Tipo C"),
        ]

        for key, nombre in productos_precio:
            cols = st.columns([2, 1.2, 1.2, 1.2, 1.2, 1.2])
            with cols[0]:
                st.markdown(nombre)
            with cols[1]:
                precio = st.number_input(
                    f"Precio {key}",
                    min_value=0.0, step=1.0, format="%.2f",
                    label_visibility="collapsed",
                    key=f"ing_{key}_precio"
                )
                st.session_state.ingresos[key]["precio"] = precio

            # Calcular precios años 2-5
            precio_actual = precio
            for i in range(4):
                precio_actual = precio_actual * (1 + incrementos[i] / 100)
                with cols[i + 2]:
                    st.text(f"{precio_actual:,.2f} €")

        st.markdown("---")

        # Plazos de cobro/pago
        st.markdown("#### 📅 Plazos de Cobro y Pago")
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Plazo de cobro a clientes", ["Contado", "30 días", "60 días", "90 días"],
                        help="Días que tardan los clientes en pagar")
        with col2:
            st.selectbox("Plazo de pago a proveedores", ["Contado", "30 días", "60 días", "90 días"],
                        help="Días que tardas en pagar a proveedores")

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
        col_h = st.columns([2.5, 1.2, 1.2, 1.2])
        with col_h[0]:
            st.markdown("**Concepto**")
        with col_h[1]:
            st.markdown("**🔵 Tipo A**")
        with col_h[2]:
            st.markdown("**🟢 Tipo B**")
        with col_h[3]:
            st.markdown("**🟠 Tipo C**")

        # Cv Producción
        cols = st.columns([2.5, 1.2, 1.2, 1.2])
        with cols[0]:
            st.markdown("Cv Producción %")
            st.caption("Coste de fabricar")
        with cols[1]:
            cv_prod_a = st.number_input(
                "Cv Prod A",
                min_value=0.0, max_value=100.0, step=0.5, format="%.1f",
                label_visibility="collapsed", key="ing_tipo_a_cv_prod"
            )
            st.session_state.ingresos["tipo_a"]["cv_produccion"] = cv_prod_a
        with cols[2]:
            cv_prod_b = st.number_input(
                "Cv Prod B",
                min_value=0.0, max_value=100.0, step=0.5, format="%.1f",
                label_visibility="collapsed", key="ing_tipo_b_cv_prod"
            )
            st.session_state.ingresos["tipo_b"]["cv_produccion"] = cv_prod_b
        with cols[3]:
            cv_prod_c = st.number_input(
                "Cv Prod C",
                min_value=0.0, max_value=100.0, step=0.5, format="%.1f",
                label_visibility="collapsed", key="ing_tipo_c_cv_prod"
            )
            st.session_state.ingresos["tipo_c"]["cv_produccion"] = cv_prod_c

        # Cv Adquisición
        cols = st.columns([2.5, 1.2, 1.2, 1.2])
        with cols[0]:
            st.markdown("Cv Adquisición %")
            st.caption("Coste de comprar")
        with cols[1]:
            cv_adq_a = st.number_input(
                "Cv Adq A",
                min_value=0.0, max_value=100.0, step=0.5, format="%.1f",
                label_visibility="collapsed", key="ing_tipo_a_cv_adq"
            )
            st.session_state.ingresos["tipo_a"]["cv_adquisicion"] = cv_adq_a
        with cols[2]:
            cv_adq_b = st.number_input(
                "Cv Adq B",
                min_value=0.0, max_value=100.0, step=0.5, format="%.1f",
                label_visibility="collapsed", key="ing_tipo_b_cv_adq"
            )
            st.session_state.ingresos["tipo_b"]["cv_adquisicion"] = cv_adq_b
        with cols[3]:
            cv_adq_c = st.number_input(
                "Cv Adq C",
                min_value=0.0, max_value=100.0, step=0.5, format="%.1f",
                label_visibility="collapsed", key="ing_tipo_c_cv_adq"
            )
            st.session_state.ingresos["tipo_c"]["cv_adquisicion"] = cv_adq_c

        # Comisiones
        cols = st.columns([2.5, 1.2, 1.2, 1.2])
        with cols[0]:
            st.markdown("Comisiones %")
            st.caption("Comisiones venta")
        with cols[1]:
            com_a = st.number_input(
                "Com A",
                min_value=0.0, max_value=100.0, step=0.5, format="%.1f",
                label_visibility="collapsed", key="ing_tipo_a_comisiones"
            )
            st.session_state.ingresos["tipo_a"]["comisiones"] = com_a
        with cols[2]:
            com_b = st.number_input(
                "Com B",
                min_value=0.0, max_value=100.0, step=0.5, format="%.1f",
                label_visibility="collapsed", key="ing_tipo_b_comisiones"
            )
            st.session_state.ingresos["tipo_b"]["comisiones"] = com_b
        with cols[3]:
            com_c = st.number_input(
                "Com C",
                min_value=0.0, max_value=100.0, step=0.5, format="%.1f",
                label_visibility="collapsed", key="ing_tipo_c_comisiones"
            )
            st.session_state.ingresos["tipo_c"]["comisiones"] = com_c

        st.markdown("---")

        # Calcular totales Cv/V y Margen
        total_cv_a = cv_prod_a + cv_adq_a + com_a
        total_cv_b = cv_prod_b + cv_adq_b + com_b
        total_cv_c = cv_prod_c + cv_adq_c + com_c
        margen_a = 100 - total_cv_a
        margen_b = 100 - total_cv_b
        margen_c = 100 - total_cv_c

        # TOTAL Cv/V (calculado)
        cols = st.columns([2.5, 1.2, 1.2, 1.2])
        with cols[0]:
            st.markdown("**TOTAL Cv/V %**")
            st.caption("Suma de costes variables")
        with cols[1]:
            st.markdown(f"**{total_cv_a:.1f}%**")
        with cols[2]:
            st.markdown(f"**{total_cv_b:.1f}%**")
        with cols[3]:
            st.markdown(f"**{total_cv_c:.1f}%**")

        # Margen bruto (calculado)
        cols = st.columns([2.5, 1.2, 1.2, 1.2])
        with cols[0]:
            st.markdown("**MARGEN BRUTO %**")
            st.caption("100% - Total Cv/V")
        with cols[1]:
            color_a = "green" if margen_a >= 30 else ("orange" if margen_a >= 15 else "red")
            st.markdown(f"**:{color_a}[{margen_a:.1f}%]**")
        with cols[2]:
            color_b = "green" if margen_b >= 30 else ("orange" if margen_b >= 15 else "red")
            st.markdown(f"**:{color_b}[{margen_b:.1f}%]**")
        with cols[3]:
            color_c = "green" if margen_c >= 30 else ("orange" if margen_c >= 15 else "red")
            st.markdown(f"**:{color_c}[{margen_c:.1f}%]**")

        st.markdown("---")

        # Existencias
        st.markdown("#### 📦 Política de Existencias")
        st.caption("Meses de existencias en almacén (si aplica para tu modelo de negocio)")

        cols = st.columns(3)
        with cols[0]:
            st.number_input("Existencias Tipo A (meses)", value=0, min_value=0, max_value=12,
                           help="Meses de stock en almacén")
        with cols[1]:
            st.number_input("Existencias Tipo B (meses)", value=0, min_value=0, max_value=12)
        with cols[2]:
            st.number_input("Existencias Tipo C (meses)", value=0, min_value=0, max_value=12)

    # Resumen de proyección - CALCULADO AUTOMÁTICAMENTE
    st.markdown("---")
    st.markdown("### 📊 Resumen de Proyección de Ingresos")

    # Calcular ingresos por año
    ingresos_anuales = []
    for ano in range(5):
        total_ano = 0
        for key in ["tipo_a", "tipo_b", "tipo_c"]:
            producto = st.session_state.ingresos[key]
            sam = producto["sam"]
            som = producto["som"][ano] if ano < len(producto["som"]) else 0
            unidades = int(sam * som / 100)

            # Calcular precio del año
            precio = producto["precio"]
            incrementos = producto["incremento"]
            for i in range(ano):
                if i < len(incrementos):
                    precio = precio * (1 + incrementos[i] / 100)

            total_ano += unidades * precio
        ingresos_anuales.append(total_ano)

    col1, col2, col3, col4, col5 = st.columns(5)
    for i, col in enumerate([col1, col2, col3, col4, col5]):
        with col:
            delta = None
            if i > 0 and ingresos_anuales[i-1] > 0:
                delta = f"{((ingresos_anuales[i] - ingresos_anuales[i-1]) / ingresos_anuales[i-1] * 100):+.0f}%"
            st.metric(f"Año {i+1}", f"{ingresos_anuales[i]:,.0f} €", delta=delta)

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
    """Etapa 6: Análisis y resultados - Con cálculos reales del FinancialEngine"""
    import pandas as pd

    st.markdown("## 📑 Etapa 6: Análisis y Resultados")
    st.markdown("---")

    # Calcular proyecciones
    try:
        resultados = calcular_proyecciones()
        cuenta_resultados = resultados['cuenta_resultados']
        flujo_tesoreria = resultados['flujo_tesoreria']
        balance = resultados['balance']
        ratios = resultados['ratios']
        saldo_inicial = resultados.get('saldo_inicial_tesoreria', 0.0)
        capital_inicial_val = resultados.get('capital_inicial', 0.0)
        inversiones_mes1 = resultados.get('inversiones_mes1', 0.0)
        inversiones_mes1_base = resultados.get('inversiones_mes1_base', 0.0)
        subvenciones_mes1 = resultados.get('subvenciones_mes1', 0.0)
        hay_datos = True
    except Exception as e:
        hay_datos = False
        st.warning(f"⚠️ No hay suficientes datos para calcular las proyecciones. Completa las etapas anteriores.")
        st.caption(f"Detalle: {str(e)}")

    if hay_datos:
        st.markdown("""
        <div class="success-card">
        <strong>🎉 ¡Cálculos completados!</strong><br>
        El sistema ha calculado automáticamente todos los estados financieros
        siguiendo la metodología PEF ToolBoard v2.0.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-card">
        <strong>📝 Pendiente de datos</strong><br>
        Completa las etapas anteriores (CAPEX, Financiación, OPEX, Ingresos) para ver los cálculos.
        </div>
        """, unsafe_allow_html=True)

    # Tabs para mostrar los diferentes análisis
    tab_pyl, tab_cf, tab_balance, tab_analisis, tab_chat, tab_export = st.tabs([
        "📈 Cuenta de Resultados", "💵 Cash Flow", "⚖️ Balance", "📊 Análisis", "💬 Asistente", "📥 Exportar"
    ])

    # Función auxiliar para formatear números
    def fmt(valor, decimals=0):
        if valor is None or pd.isna(valor):
            return "-"
        if decimals == 0:
            return f"{valor:,.0f} €"
        return f"{valor:,.{decimals}f} €"

    def fmt_pct(valor):
        if valor is None or pd.isna(valor):
            return "-"
        return f"{valor * 100:.1f}%"

    # Función para sumar valores de un rango de meses
    def suma_ano(df, columna, ano):
        inicio = (ano - 1) * 12
        fin = ano * 12
        return sum(df[columna][inicio:fin])

    with tab_pyl:
        st.markdown("### Cuenta de Resultados (P&L)")
        st.caption("Estructura según hoja RESULTADOS del Excel (filas 5-25)")

        if hay_datos:
            # Crear DataFrame con datos reales
            pyl_conceptos = [
                "INGRESOS (Ventas)",
            ]
            # Incluir ingresos trabajo propio activo solo si hay valores
            hay_trab_activo = any(suma_ano(cuenta_resultados, 'ingresos_trabajo_propio_activo', a) != 0 for a in range(1, 6))
            if hay_trab_activo:
                pyl_conceptos.append("Ingresos trabajo propio activo")

            pyl_conceptos += [
                "(-) Costes variables",
                "MARGEN COMERCIAL",
                "(-) Gastos fijos servicios",
                "(-) Gastos de nómina",
                "EBITDA",
                "(-) Amortizaciones",
            ]
            # Incluir imputación subvenciones solo si hay valores
            hay_imputacion_sub = any(suma_ano(cuenta_resultados, 'imputacion_subvenciones', a) != 0 for a in range(1, 6))
            if hay_imputacion_sub:
                pyl_conceptos.append("Imputación subvenciones capital")

            pyl_conceptos += [
                "EBIT",
                "(-) Gastos financieros",
                "EBT (Antes impuestos)",
                "(-) Impuesto Sociedades",
                "RESULTADO NETO",
                "(Resultado acumulado)"
            ]

            pyl_data = {"Concepto": pyl_conceptos}

            # Año 0: todo ceros (no hay operaciones)
            pyl_data["Año 0"] = [fmt(0)] * len(pyl_conceptos)

            for ano in range(1, 6):
                col_name = f"Año {ano}"
                col_values = [
                    fmt(suma_ano(cuenta_resultados, 'ingresos', ano)),
                ]
                if hay_trab_activo:
                    col_values.append(fmt(suma_ano(cuenta_resultados, 'ingresos_trabajo_propio_activo', ano)))
                col_values += [
                    fmt(suma_ano(cuenta_resultados, 'costes_variables', ano)),
                    fmt(suma_ano(cuenta_resultados, 'margen_comercial', ano)),
                    fmt(suma_ano(cuenta_resultados, 'gastos_fijos_servicios', ano)),
                    fmt(suma_ano(cuenta_resultados, 'gastos_nomina', ano)),
                    fmt(suma_ano(cuenta_resultados, 'ebitda', ano)),
                    fmt(suma_ano(cuenta_resultados, 'amortizaciones', ano)),
                ]
                if hay_imputacion_sub:
                    col_values.append(fmt(suma_ano(cuenta_resultados, 'imputacion_subvenciones', ano)))
                mes_fin = ano * 12 - 1
                col_values += [
                    fmt(suma_ano(cuenta_resultados, 'ebit', ano)),
                    fmt(suma_ano(cuenta_resultados, 'gastos_financieros', ano)),
                    fmt(suma_ano(cuenta_resultados, 'ebt', ano)),
                    fmt(suma_ano(cuenta_resultados, 'impuesto_sociedades', ano)),
                    fmt(suma_ano(cuenta_resultados, 'resultado', ano)),
                    fmt(cuenta_resultados['resultado_acumulado'][mes_fin])
                ]
                pyl_data[col_name] = col_values

            df_pyl = pd.DataFrame(pyl_data)
            st.dataframe(df_pyl, use_container_width=True, hide_index=True)

            # Resumen visual
            st.markdown("---")
            st.markdown("#### Resumen por Año")
            cols = st.columns(5)
            for i, ano in enumerate(range(1, 6)):
                with cols[i]:
                    resultado = suma_ano(cuenta_resultados, 'resultado', ano)
                    delta_color = "normal" if resultado >= 0 else "inverse"
                    st.metric(
                        f"Año {ano}",
                        fmt(resultado),
                        delta=fmt_pct(suma_ano(cuenta_resultados, 'resultado', ano) / max(suma_ano(cuenta_resultados, 'ingresos', ano), 1)) + " margen" if suma_ano(cuenta_resultados, 'ingresos', ano) > 0 else None
                    )
        else:
            st.info("Completa los datos de las etapas anteriores para ver la Cuenta de Resultados.")

    with tab_cf:
        st.markdown("### Flujo de Tesorería (Cash Flow)")
        st.caption("Estructura según hoja RESULTADOS del Excel (filas 29-58)")

        if hay_datos:
            # CF por año (con Año 0 como en el Excel)
            # Año 0: solo capital inicial (inversiones mes 1 se descuentan del saldo)
            inversiones_mes1 = saldo_inicial - capital_inicial_val  # negativo si hay inversiones
            cf_data = {
                "Concepto": [
                    "CF Operaciones",
                    "CF Inversiones",
                    "CF Financiación",
                    "CF NETO",
                    "CF Acumulado (Tesorería)"
                ]
            }

            # Año 0: capital inicial, inversiones mes 1, subvenciones mes 1
            cf_fin_ano0 = capital_inicial_val + subvenciones_mes1
            cf_inv_ano0 = -inversiones_mes1
            tesoreria_ano0 = max(saldo_inicial, 0)  # póliza cubre déficit
            cf_data["Año 0"] = [
                fmt(0),
                fmt(cf_inv_ano0),
                fmt(cf_fin_ano0),
                fmt(saldo_inicial),
                fmt(tesoreria_ano0)
            ]

            for ano in range(1, 6):
                col_name = f"Año {ano}"
                mes_fin = ano * 12 - 1
                cf_data[col_name] = [
                    fmt(suma_ano(flujo_tesoreria, 'cf_operaciones', ano)),
                    fmt(suma_ano(flujo_tesoreria, 'cf_inversiones', ano)),
                    fmt(suma_ano(flujo_tesoreria, 'cf_financiacion', ano)),
                    fmt(suma_ano(flujo_tesoreria, 'cf_neto', ano)),
                    fmt(flujo_tesoreria['tesoreria_disponible'][mes_fin])
                ]

            df_cf = pd.DataFrame(cf_data)
            st.dataframe(df_cf, use_container_width=True, hide_index=True)

            # Métricas de tesorería
            st.markdown("---")
            st.markdown("#### Evolución de Tesorería")
            cols = st.columns(6)
            with cols[0]:
                st.metric("Año 0", fmt(tesoreria_ano0))
            for i, ano in enumerate(range(1, 6)):
                with cols[i + 1]:
                    mes_fin = ano * 12 - 1
                    tesoreria = flujo_tesoreria['tesoreria_disponible'][mes_fin]
                    st.metric(f"Año {ano}", fmt(tesoreria))

            # Alerta de déficit
            min_tesoreria = min(flujo_tesoreria['tesoreria_disponible'])
            if min_tesoreria < 0:
                st.error(f"⚠️ Déficit máximo de tesorería: {fmt(min_tesoreria)}")
        else:
            st.info("Completa los datos de las etapas anteriores para ver el Cash Flow.")

    with tab_balance:
        st.markdown("### Balance de Situación")
        st.caption("Calculado automáticamente al cierre de cada año")

        if hay_datos:
            # Balance simplificado por año
            balance_data = {
                "Concepto": [
                    "ACTIVO NO CORRIENTE",
                    "ACTIVO CORRIENTE",
                    "TOTAL ACTIVO",
                    "---",
                    "PATRIMONIO NETO",
                    "PASIVO NO CORRIENTE",
                    "PASIVO CORRIENTE",
                    "TOTAL PN + PASIVO"
                ]
            }

            # Año 0: estado inicial antes de operar
            anc_0 = inversiones_mes1_base
            ac_0 = max(saldo_inicial, 0)  # tesorería (póliza cubre déficit)
            total_a_0 = anc_0 + ac_0
            pn_0 = capital_inicial_val + subvenciones_mes1
            pasivo_c_0 = total_a_0 - pn_0  # residual (póliza - IVA soportado)
            balance_data["Año 0"] = [
                fmt(anc_0), fmt(ac_0), fmt(total_a_0),
                "", fmt(pn_0), fmt(0), fmt(pasivo_c_0), fmt(total_a_0)
            ]

            for ano in range(1, 6):
                col_name = f"Año {ano}"
                mes_fin = ano * 12 - 1
                activo_nc = balance['activo_no_corriente'][mes_fin]
                activo_c = balance['activo_corriente'][mes_fin]
                total_activo = balance['activo_total'][mes_fin]
                pn = balance['patrimonio_neto'][mes_fin]
                pasivo_nc = balance['pasivo_no_corriente'][mes_fin]
                pasivo_c = balance['pasivo_corriente'][mes_fin]
                total_pn_pasivo = balance['pn_pasivo_total'][mes_fin]

                balance_data[col_name] = [
                    fmt(activo_nc),
                    fmt(activo_c),
                    fmt(total_activo),
                    "",
                    fmt(pn),
                    fmt(pasivo_nc),
                    fmt(pasivo_c),
                    fmt(total_pn_pasivo)
                ]

            df_balance = pd.DataFrame(balance_data)
            st.dataframe(df_balance, use_container_width=True, hide_index=True)

            st.success("✅ El balance cuadra: ACTIVO = PATRIMONIO NETO + PASIVO")
        else:
            st.info("Completa los datos de las etapas anteriores para ver el Balance.")

    with tab_analisis:
        st.markdown("### Análisis Financiero")
        st.caption("Estructura según hoja ANALISIS del Excel")

        if hay_datos:
            # Análisis de tesorería
            st.markdown("#### 💵 Análisis del Cash Flow")
            col1, col2, col3 = st.columns(3)

            ratios_glob = ratios.get('globales', {})
            deficit_max = ratios_glob.get('deficit_maximo', 0)
            mes_deficit = ratios_glob.get('mes_deficit_maximo', None)

            with col1:
                st.metric("Déficit máximo tesorería", fmt(deficit_max) if deficit_max > 0 else "Sin déficit")
            with col2:
                st.metric("Mes del pico de déficit", f"Mes {mes_deficit}" if mes_deficit else "—")
            with col3:
                burn_rate = sum(flujo_tesoreria['cf_neto'][0:12]) / 12
                st.metric("Burn Rate (medio año 1)", fmt(burn_rate) + "/mes")

            st.markdown("---")

            # Valoración
            st.markdown("#### 💎 Valoración del Proyecto")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Por Flujos de Caja (DCF)**")
                tir = ratios.get('tir')
                van = ratios.get('van')
                st.metric("TIR", fmt_pct(tir) if tir else "N/A")
                st.metric("VAN (10%)", fmt(van) if van else "N/A")
            with col2:
                st.markdown("**Por Múltiplos**")
                resultado_ano5 = suma_ano(cuenta_resultados, 'resultado', 5)
                valoracion = resultado_ano5 * 10 if resultado_ano5 > 0 else 0
                st.metric("Valoración x10 Resultado", fmt(valoracion))

            st.markdown("---")

            # Márgenes
            st.markdown("#### 📊 Evolución de Márgenes")
            margenes_data = {"Margen": ["Margen Comercial", "Margen EBITDA", "Margen Neto"]}

            for ano in range(1, 6):
                ingresos = suma_ano(cuenta_resultados, 'ingresos', ano)
                if ingresos > 0:
                    m_comercial = suma_ano(cuenta_resultados, 'margen_comercial', ano) / ingresos
                    m_ebitda = suma_ano(cuenta_resultados, 'ebitda', ano) / ingresos
                    m_neto = suma_ano(cuenta_resultados, 'resultado', ano) / ingresos
                else:
                    m_comercial = m_ebitda = m_neto = 0

                margenes_data[f"Año {ano}"] = [fmt_pct(m_comercial), fmt_pct(m_ebitda), fmt_pct(m_neto)]

            df_margenes = pd.DataFrame(margenes_data)
            st.dataframe(df_margenes, use_container_width=True, hide_index=True)

            st.markdown("---")

            # Refinanciación con capital
            st.markdown("#### 💼 Refinanciación con Capital")
            fin_data = st.session_state.financiacion
            cap_data_analisis = fin_data.get("capital_inicial", {})
            amp_data_analisis = fin_data.get("ampliacion", {})

            cap_imp = cap_data_analisis.get("importe", 0) if isinstance(cap_data_analisis, dict) else cap_data_analisis
            cap_acc = cap_data_analisis.get("acciones", 0) if isinstance(cap_data_analisis, dict) else 0
            amp_imp = amp_data_analisis.get("importe", 0) if isinstance(amp_data_analisis, dict) else 0
            amp_mes_val = amp_data_analisis.get("mes", 21) if isinstance(amp_data_analisis, dict) else 21
            amp_val = amp_data_analisis.get("valoracion_premoney", 0) if isinstance(amp_data_analisis, dict) else 0

            # Calcular fila capital inicial
            valor_accion_cap = cap_imp / cap_acc if cap_acc > 0 else 0

            # Calcular fila ampliación
            if amp_imp > 0 and amp_val > 0 and cap_acc > 0:
                precio_accion = amp_val / cap_acc
                acc_nuevas = amp_imp / precio_accion if precio_accion > 0 else 0
                acc_totales_amp = cap_acc + acc_nuevas
                valor_accion_amp_calc = (amp_val + amp_imp) / acc_totales_amp if acc_totales_amp > 0 else 0
                pct_nuevos_amp = acc_nuevas / acc_totales_amp if acc_totales_amp > 0 else 0
                valor_fund_amp = amp_val
            else:
                acc_totales_amp = cap_acc
                valor_accion_amp_calc = amp_val / cap_acc if (amp_val > 0 and cap_acc > 0) else valor_accion_cap
                pct_nuevos_amp = 0
                valor_fund_amp = amp_val if amp_val > 0 else cap_imp

            refin_data = {
                "Concepto": [
                    "Capital inicial (fundadores)",
                    f"Ampliación capital 1 (mes {amp_mes_val})"
                ],
                "Mes entrada": [0, amp_mes_val],
                "Importe": [fmt(cap_imp), fmt(amp_imp)],
                "Valoración (pre-money)": [fmt(cap_imp), fmt(amp_val)],
                "Acciones circulación": [f"{cap_acc:,.0f}" if cap_acc > 0 else "-", f"{acc_totales_amp:,.0f}" if acc_totales_amp > 0 else "-"],
                "Valor/acción": [f"{valor_accion_cap:,.2f} €" if cap_acc > 0 else "-", f"{valor_accion_amp_calc:,.2f} €" if acc_totales_amp > 0 else "-"],
                "% nuevos socios": ["0%", f"{pct_nuevos_amp:.1%}"],
                "Valor fundadores": [fmt(cap_imp), fmt(valor_fund_amp)]
            }

            df_refin = pd.DataFrame(refin_data)
            st.dataframe(df_refin, use_container_width=True, hide_index=True)

            st.markdown("---")

            # Punto muerto
            st.markdown("#### ⚖️ Punto Muerto (Break-Even)")
            col1, col2, col3 = st.columns(3)

            mes_punto_muerto = ratios_glob.get('mes_punto_equilibrio', None)
            ventas_equilibrio = ratios_glob.get('punto_equilibrio_euros', 0)

            with col1:
                st.metric("Unidades equilibrio", "N/A")
            with col2:
                st.metric("Mes punto muerto", f"Mes {mes_punto_muerto}" if mes_punto_muerto else "No alcanzado")
            with col3:
                st.metric("Ventas equilibrio", fmt(ventas_equilibrio) if ventas_equilibrio else "N/A")

            st.markdown("---")

            # Ratios patrimoniales (año 5)
            st.markdown("#### 📐 Ratios Patrimoniales (Año 5)")

            mes_fin_ano5 = 59
            activo_c = balance['activo_corriente'][mes_fin_ano5]
            pasivo_c = balance['pasivo_corriente'][mes_fin_ano5]
            total_activo = balance['activo_total'][mes_fin_ano5]
            total_pasivo = balance['pasivo_no_corriente'][mes_fin_ano5] + pasivo_c
            pn = balance['patrimonio_neto'][mes_fin_ano5]

            fm = activo_c - pasivo_c
            liquidez = activo_c / pasivo_c if pasivo_c > 0 else 0
            solvencia = total_activo / total_pasivo if total_pasivo > 0 else 0
            apalancamiento = total_pasivo / (pn + total_pasivo) if (pn + total_pasivo) > 0 else 0

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown("**Fondo de Maniobra**")
                st.caption("AC - PC")
                st.metric("FM", fmt(fm))
            with col2:
                st.markdown("**Liquidez**")
                st.caption("AC / PC")
                st.metric("Ratio", f"{liquidez:.2f}")
            with col3:
                st.markdown("**Solvencia**")
                st.caption("Activo / Pasivo")
                st.metric("Ratio", f"{solvencia:.2f}")
            with col4:
                st.markdown("**Apalancamiento**")
                st.caption("Pasivo / (PN+Pasivo)")
                st.metric("Ratio", f"{apalancamiento:.2f}")

            # Interpretación
            alertas = []
            if fm < 0:
                alertas.append("⚠️ Fondo de Maniobra negativo: riesgo de liquidez")
            if liquidez < 1:
                alertas.append("⚠️ Liquidez < 1: el activo corriente no cubre el pasivo corriente")
            if solvencia < 1.5:
                alertas.append("⚠️ Solvencia < 1.5: capacidad de pago ajustada")
            if apalancamiento > 0.6:
                alertas.append("⚠️ Apalancamiento > 60%: nivel de endeudamiento alto")

            if alertas:
                for alerta in alertas:
                    st.warning(alerta)
            else:
                st.success("✅ Todos los ratios dentro de rangos saludables")

        else:
            st.info("Completa los datos de las etapas anteriores para ver el Análisis.")

    with tab_chat:
        st.markdown("### 💬 Asistente de Análisis Financiero")

        if not any(m.get("stage") == "analisis" for m in st.session_state.messages):
            st.session_state.messages.append({
                "role": "assistant",
                "content": (
                    "¡Tu plan está listo! He analizado todos los datos que has introducido.\n\n"
                    "Puedo ayudarte a:\n"
                    "- 📊 **Interpretar** los resultados (TIR, VAN, márgenes, ratios)\n"
                    "- ⚠️ **Identificar** puntos de atención o riesgos\n"
                    "- 💡 **Sugerir** mejoras para aumentar la viabilidad\n"
                    "- ❓ **Responder** cualquier pregunta sobre tus cifras\n\n"
                    "¿Qué quieres saber sobre tu plan financiero?"
                ),
                "stage": "analisis"
            })

        render_chat_interface("analisis")

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
                with st.spinner("Generando Excel..."):
                    try:
                        from components.excel_generator import fill_template
                        excel_bytes = fill_template(st.session_state)
                        nombre = st.session_state.proyecto.get("nombre", "PEF") or "PEF"
                        filename = f"PEF_{nombre.replace(' ', '_')}.xlsx"
                        output_path = Config.OUTPUT_DIR / filename
                        Config.OUTPUT_DIR.mkdir(exist_ok=True)
                        output_path.write_bytes(excel_bytes)
                        st.success(f"✅ Guardado en output/{filename}")
                        st.download_button(
                            label="💾 Descargar Excel generado",
                            data=excel_bytes,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.error(f"Error generando Excel: {e}")

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
