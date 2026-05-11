"""
Configuración central de la aplicación PEF AI Assistant
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cuando se ejecuta desde un bundle de PyInstaller, cargamos el .env únicamente
# desde la carpeta del ejecutable (nunca subiendo por el árbol de directorios).
# Así el .env del desarrollador no se filtra al usuario final.
if hasattr(sys, "_MEIPASS"):
    _exe_dir = Path(os.path.dirname(sys.executable))
    load_dotenv(dotenv_path=_exe_dir / ".env")
    _BUNDLE_MODE = True
else:
    load_dotenv()
    _BUNDLE_MODE = False


class Config:
    """Configuración de la aplicación"""

    # Rutas del proyecto
    BASE_DIR = Path(__file__).parent.parent
    SRC_DIR  = BASE_DIR / "src"

    # En modo bundle los recursos están en _internal/; las salidas van junto al exe
    if _BUNDLE_MODE:
        TEMPLATES_DIR = Path(sys._MEIPASS) / "templates"
        OUTPUT_DIR    = Path(os.path.dirname(sys.executable)) / "output"
    else:
        TEMPLATES_DIR = BASE_DIR / "templates"
        OUTPUT_DIR    = BASE_DIR / "output"

    # Configuración de la API LLM
    MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "openai")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

    # Configuración de la aplicación
    APP_TITLE = os.getenv("APP_TITLE", "PEF AI Assistant")
    APP_SUBTITLE = os.getenv("APP_SUBTITLE", "Asistente inteligente para planes económico-financieros")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LANGUAGE = os.getenv("LANGUAGE", "es")

    # Configuración financiera (PEF ToolBoard)
    PROJECTION_YEARS = 5
    PROJECTION_MONTHS = 60
    DEFAULT_IVA = 0.21
    DEFAULT_CORPORATE_TAX = 0.25

    # Rutas de archivos Excel
    TEMPLATE_FILE = TEMPLATES_DIR / "PEF_TOOLBOARD_v20.xlsx"

    @classmethod
    def validate(cls):
        """Valida que la configuración sea correcta"""
        errors = []

        # Validar API Key según el proveedor
        if cls.MODEL_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY no está configurada")
        elif cls.MODEL_PROVIDER == "anthropic" and not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY no está configurada")

        # Crear directorio de salida si no existe
        cls.OUTPUT_DIR.mkdir(exist_ok=True)

        if errors:
            raise ValueError(f"Errores de configuración: {', '.join(errors)}")

        return True

# Validar configuración al importar
if __name__ != "__main__":
    try:
        Config.validate()
    except ValueError as e:
        print(f"⚠️  Advertencia: {e}")
