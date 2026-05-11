"""
Launcher para la version empaquetada con PyInstaller.
Arranca Streamlit internamente y abre el navegador automaticamente.
"""
import os
import sys
import threading
import webbrowser
import time


def resource_path(*parts):
    """Devuelve ruta absoluta, tanto en desarrollo como dentro del .exe."""
    base = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.join(os.path.dirname(__file__), "..")
    return os.path.join(base, *parts)


def _open_browser():
    time.sleep(4)
    webbrowser.open("http://localhost:8501")


def main():
    # Añadir src al path para que los imports de app.py funcionen
    sys.path.insert(0, resource_path("src"))

    # Cambiar el directorio de trabajo a la raiz del bundle
    os.chdir(resource_path("."))

    # --- Configuracion de Streamlit via env vars ---
    # Deben estar fijadas ANTES de cualquier import de streamlit,
    # que es cuando el modulo config.py lee y cachea los valores.

    # Modo produccion (evita que Streamlit conecte al Node dev server)
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

    # Tema: nombres exactos confirmados via _config_options_template
    os.environ["STREAMLIT_THEME_BASE"]                       = "light"
    os.environ["STREAMLIT_THEME_PRIMARY_COLOR"]              = "#2E7D32"
    os.environ["STREAMLIT_THEME_BACKGROUND_COLOR"]           = "#FFFFFF"
    os.environ["STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR"] = "#E8F5E9"
    os.environ["STREAMLIT_THEME_TEXT_COLOR"]                 = "#1B5E20"

    # Forzar modo produccion via API (el env var de developmentMode no existe
    # en Streamlit, hay que hacerlo via set_option despues del import)
    from streamlit import config as _st_config
    _st_config.set_option("global.developmentMode", False)
    _st_config.set_option("server.headless", True)

    # Abrir navegador en segundo plano
    threading.Thread(target=_open_browser, daemon=True).start()

    # Lanzar Streamlit
    from streamlit.web import bootstrap
    bootstrap.run(resource_path("src", "app.py"), "", [], {})


if __name__ == "__main__":
    main()
