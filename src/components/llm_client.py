"""
Cliente LLM — Abstracción unificada para OpenAI y Anthropic.

Responsabilidades:
- Hacer llamadas a la API del proveedor configurado
- Abstraer las diferencias entre OpenAI y Anthropic
- Manejar errores de API (rate limit, auth, conexión)
- Extraer JSON de respuestas del modelo
"""

import json
import time
from typing import Optional

from config import Config


class LLMClient:
    """
    Cliente unificado para OpenAI y Anthropic.
    El resto del código no depende del proveedor concreto —
    solo usa chat() y extract_json().
    """

    def __init__(self):
        import os
        self.provider = os.getenv("MODEL_PROVIDER", Config.MODEL_PROVIDER)
        self.model = os.getenv("MODEL_NAME", Config.MODEL_NAME)
        self.max_tokens = Config.MAX_TOKENS
        self.temperature = Config.TEMPERATURE
        self._client = self._init_client()

    # ------------------------------------------------------------------
    # Inicialización
    # ------------------------------------------------------------------

    def _init_client(self):
        """Inicializa el cliente del proveedor configurado."""
        import os
        if self.provider == "anthropic":
            from anthropic import Anthropic
            return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        elif self.provider == "openai":
            from openai import OpenAI
            return OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        else:
            raise ValueError(
                f"Proveedor '{self.provider}' no soportado. "
                "Usa 'openai' o 'anthropic' en el archivo .env."
            )

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def chat(self, messages: list[dict], system: Optional[str] = None) -> str:
        """
        Envía una conversación y devuelve la respuesta como texto.

        Args:
            messages: Lista de {"role": "user"/"assistant", "content": "..."}
            system:   Prompt de sistema. Si es None usa el prompt por defecto.

        Returns:
            Respuesta del modelo como string. En caso de error devuelve
            un mensaje descriptivo para mostrar al usuario.
        """
        try:
            if self.provider == "anthropic":
                return self._chat_anthropic(messages, system)
            else:
                return self._chat_openai(messages, system)
        except Exception as e:
            return self._handle_error(e)

    def extract_json(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        retries: int = 2,
    ) -> dict:
        """
        Llama al LLM esperando una respuesta en JSON.
        Reintenta automáticamente si el JSON no es válido.

        Args:
            messages: Igual que en chat()
            system:   Igual que en chat()
            retries:  Número de reintentos si el JSON falla (default 2)

        Returns:
            dict con el JSON parseado, o {} si falla tras todos los intentos.
        """
        for attempt in range(retries + 1):
            raw = self.chat(messages, system)
            parsed = self._parse_json(raw)
            if parsed is not None:
                return parsed
            if attempt < retries:
                time.sleep(1)

        return {}

    @property
    def is_configured(self) -> bool:
        """True si la API key del proveedor activo parece válida (no es el valor placeholder)."""
        import os
        if self.provider == "anthropic":
            key = os.getenv("ANTHROPIC_API_KEY", "")
            return key.startswith("sk-ant-") and len(key) > 20
        else:
            key = os.getenv("OPENAI_API_KEY", "")
            return key.startswith("sk-") and not key.startswith("sk-tu") and len(key) > 20

    # ------------------------------------------------------------------
    # Implementaciones por proveedor
    # ------------------------------------------------------------------

    def _chat_anthropic(self, messages: list[dict], system: Optional[str]) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system or "",
            messages=messages,
        )
        return response.content[0].text

    def _chat_openai(self, messages: list[dict], system: Optional[str]) -> str:
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=all_messages,
        )
        return response.choices[0].message.content

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _parse_json(self, text: str) -> Optional[dict]:
        """
        Extrae y parsea JSON de la respuesta del modelo.
        Soporta respuestas envueltas en bloques ```json ... ```.
        Devuelve None si el texto no contiene JSON válido.
        """
        text = text.strip()

        # Extraer bloque de código si lo hay
        if "```" in text:
            parts = text.split("```")
            # parts[1] es el contenido del bloque
            if len(parts) >= 2:
                block = parts[1]
                if block.startswith("json"):
                    block = block[4:]
                text = block.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _handle_error(self, error: Exception) -> str:
        """Convierte excepciones de API en mensajes legibles para el usuario."""
        msg = str(error).lower()

        if "rate limit" in msg:
            return "⚠️ Demasiadas peticiones. Espera unos segundos e inténtalo de nuevo."
        elif "api key" in msg or "authentication" in msg or "401" in msg:
            return "⚠️ API Key no válida. Revisa la configuración en el archivo .env."
        elif "connection" in msg or "timeout" in msg:
            return "⚠️ Error de conexión. Comprueba tu conexión a internet."
        elif "model" in msg and "not found" in msg:
            return f"⚠️ Modelo '{self.model}' no encontrado. Revisa MODEL_NAME en .env."
        else:
            return f"⚠️ Error inesperado: {error}"
