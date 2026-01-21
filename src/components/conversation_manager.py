"""
Gestor de conversación con LLM
Maneja la interacción conversacional con el usuario a través del LLM
"""

from typing import Optional, Dict, Any
import openai
from anthropic import Anthropic
from ..config import Config
from ..utils.prompts import SYSTEM_PROMPT, INITIAL_GREETING


class ConversationManager:
    """
    Gestiona la conversación con el usuario mediante un LLM
    """

    def __init__(self):
        """Inicializa el gestor de conversación"""
        self.provider = Config.MODEL_PROVIDER
        self.model_name = Config.MODEL_NAME
        self.conversation_history = []

        # Inicializar cliente según proveedor
        if self.provider == "openai":
            openai.api_key = Config.OPENAI_API_KEY
            self.client = openai
        elif self.provider == "anthropic":
            self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Proveedor no soportado: {self.provider}")

    def start_conversation(self) -> str:
        """
        Inicia una nueva conversación

        Returns:
            str: Mensaje de bienvenida del asistente
        """
        # Añadir mensaje del sistema
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        return INITIAL_GREETING

    def send_message(self, user_message: str) -> str:
        """
        Envía un mensaje del usuario y obtiene la respuesta del LLM

        Args:
            user_message: Mensaje del usuario

        Returns:
            str: Respuesta del asistente
        """
        # TODO: Implementar lógica de llamada a la API
        # TODO: Gestionar contexto de conversación
        # TODO: Manejar errores de API

        return "Función en desarrollo - se implementará en la siguiente fase"

    def extract_data(self, user_input: str, context: str) -> Dict[str, Any]:
        """
        Extrae datos estructurados de la respuesta del usuario

        Args:
            user_input: Respuesta del usuario
            context: Contexto de qué datos se esperan

        Returns:
            dict: Datos extraídos en formato estructurado
        """
        # TODO: Implementar extracción de datos con LLM
        # TODO: Validar formato JSON de respuesta

        return {}

    def reset(self):
        """Reinicia la conversación"""
        self.conversation_history = []


# TODO: Implementar completamente en la fase de integración LLM
