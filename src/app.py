"""
Aplicación principal - PEF AI Assistant
Streamlit app para elaboración de Planes Económico-Financieros con IA
"""
import streamlit as st
from config import Config

# Configuración de la página
st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Función principal de la aplicación"""

    # Título y subtítulo
    st.title(f"💰 {Config.APP_TITLE}")
    st.markdown(f"*{Config.APP_SUBTITLE}*")

    st.divider()

    # Barra lateral
    with st.sidebar:
        st.header("📋 Menú")
        st.markdown("""
        ### Bienvenido

        Esta herramienta te ayudará a crear un **Plan Económico-Financiero**
        riguroso para tu proyecto emprendedor.

        #### ¿Qué necesitas?
        - Información básica de tu proyecto
        - Inversiones previstas
        - Gastos operativos estimados
        - Proyecciones de ingresos

        #### ¿Qué obtendrás?
        - ✅ Cuenta de resultados (5 años)
        - ✅ Flujo de tesorería
        - ✅ Balance de situación
        - ✅ Ratios financieros
        - ✅ Análisis de viabilidad
        - ✅ Archivo Excel profesional
        """)

        st.divider()

        if Config.DEBUG:
            st.warning("🔧 Modo DEBUG activado")
            st.info(f"Modelo: {Config.MODEL_NAME}")

    # Contenido principal
    st.header("🚀 Comenzar")

    # Estado temporal - será reemplazado por la lógica conversacional
    st.info("🚧 **Proyecto en desarrollo** - TFG 2025-26")

    st.markdown("""
    ### Próximos pasos:

    1. **Fase actual**: Configuración y estructura del proyecto ✅
    2. **Siguiente fase**: Implementación del motor de cálculo financiero
    3. **Después**: Integración con LLM para asistencia conversacional

    ### Arquitectura del sistema:

    ```
    Usuario → Interfaz Streamlit → Gestor Conversacional (LLM)
                                           ↓
                                  Motor de Cálculo PEF
                                           ↓
                                  Generador de Excel
    ```
    """)

    # Sección de prueba de configuración
    with st.expander("🔍 Verificar Configuración"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Configuración del Modelo:**")
            st.json({
                "provider": Config.MODEL_PROVIDER,
                "model": Config.MODEL_NAME,
                "max_tokens": Config.MAX_TOKENS,
                "temperature": Config.TEMPERATURE
            })

        with col2:
            st.write("**Configuración Financiera:**")
            st.json({
                "años_proyección": Config.PROJECTION_YEARS,
                "meses_proyección": Config.PROJECTION_MONTHS,
                "iva_defecto": f"{Config.DEFAULT_IVA*100}%",
                "impuesto_sociedades": f"{Config.DEFAULT_CORPORATE_TAX*100}%"
            })

        # Verificar API Key (sin mostrarla)
        if Config.MODEL_PROVIDER == "openai":
            api_configured = bool(Config.OPENAI_API_KEY)
        else:
            api_configured = bool(Config.ANTHROPIC_API_KEY)

        if api_configured:
            st.success("✅ API Key configurada correctamente")
        else:
            st.error("❌ API Key no configurada. Revisa tu archivo .env")

    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
        <p>TFG 2025-26 - Raul Velasco Tello</p>
        <p>Tutor: Jaume Teodoro i Sadurní | Universitat Pompeu Fabra - TecnoCampus</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
