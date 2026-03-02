"""
Gestor de conversación con LLM.
Maneja el historial de mensajes y delega las llamadas al LLMClient.
"""

from typing import Optional
from components.llm_client import LLMClient
from config import Config
from utils.prompts import SYSTEM_PROMPT, INITIAL_GREETING


class ConversationManager:
    """
    Gestiona la conversación con el usuario.

    Responsabilidades:
    - Mantener el historial de mensajes de la sesión
    - Añadir/quitar mensajes del contexto
    - Delegar las llamadas al LLMClient
    """

    def __init__(self):
        self.client = LLMClient()
        self.history: list[dict] = []

    # ------------------------------------------------------------------
    # Control de conversación
    # ------------------------------------------------------------------

    def start_conversation(self) -> str:
        """Reinicia el historial y devuelve el saludo inicial."""
        self.history = []
        return INITIAL_GREETING

    def reset(self):
        """Limpia el historial."""
        self.history = []

    # ------------------------------------------------------------------
    # Envío de mensajes
    # ------------------------------------------------------------------

    def send_message(self, user_message: str, system: Optional[str] = None) -> str:
        """
        Añade el mensaje del usuario al historial, llama al LLM y
        añade la respuesta al historial.

        Args:
            user_message: Texto del usuario
            system: Prompt de sistema para esta llamada (usa SYSTEM_PROMPT si None)

        Returns:
            Respuesta del asistente como string
        """
        self.history.append({"role": "user", "content": user_message})

        response = self.client.chat(
            messages=self.history,
            system=system or SYSTEM_PROMPT,
        )

        self.history.append({"role": "assistant", "content": response})
        return response

    def extract_data(
        self,
        user_message: str,
        system: str,
    ) -> dict:
        """
        Envía un mensaje esperando una respuesta JSON estructurada.
        NO añade al historial principal (es una llamada de extracción puntual).

        Args:
            user_message: Descripción/respuesta del usuario a parsear
            system: Prompt de sistema con el schema JSON esperado

        Returns:
            dict con los datos extraídos, o {} si falla
        """
        messages = [{"role": "user", "content": user_message}]
        return self.client.extract_json(messages=messages, system=system)

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------

    @property
    def is_configured(self) -> bool:
        return self.client.is_configured
