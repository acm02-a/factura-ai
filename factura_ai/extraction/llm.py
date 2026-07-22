"""
Extractor con IA usando Groq (LLM rápido y gratuito).

El LLM recibe el texto crudo del comprobante y devuelve JSON estructurado. Esto
es lo que le da robustez frente a layouts que las regex no anticiparon: facturas
con campos en otro orden, etiquetas distintas o texto ruidoso de un OCR.

Nota de diseño: si no hay GROQ_API_KEY, este extractor no se instancia — el
`factory` cae al RuleBasedExtractor. Y si la llamada al LLM falla o devuelve un
JSON inservible, se levanta LLMExtractionError para que el pipeline pueda
degradar con gracia. Un sistema de producción nunca depende de que un servicio
externo esté siempre disponible.
"""

from __future__ import annotations

import json
import os

from ..domain.models import Factura

MODELO_POR_DEFECTO = "llama-3.3-70b-versatile"

_SYSTEM = (
    "Eres un extractor de datos de facturas y boletas electrónicas peruanas. "
    "Devuelves EXCLUSIVAMENTE un objeto JSON válido, sin texto adicional, con "
    "las claves: ruc_emisor (11 dígitos), razon_social, numero (serie-correlativo), "
    "fecha_emision (AAAA-MM-DD), moneda (código ISO), items (lista de objetos con "
    "descripcion, cantidad, precio_unitario, importe), base_imponible, igv, total. "
    "Usa null para lo que no encuentres. Los montos son números, no strings."
)


class LLMExtractionError(RuntimeError):
    """La extracción con IA no pudo completarse."""


class LLMExtractor:
    nombre = "llm"

    def __init__(self, api_key: str | None = None, modelo: str | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.modelo = modelo or os.getenv("GROQ_MODEL", MODELO_POR_DEFECTO)
        if not self.api_key:
            raise LLMExtractionError("No hay GROQ_API_KEY configurada")

    def extract(self, texto: str) -> Factura:
        try:
            from groq import Groq
        except ImportError as e:  # pragma: no cover - depende del entorno
            raise LLMExtractionError("El paquete 'groq' no está instalado") from e

        try:
            client = Groq(api_key=self.api_key)
            resp = client.chat.completions.create(
                model=self.modelo,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": texto},
                ],
            )
            data = json.loads(resp.choices[0].message.content)
        except Exception as e:  # noqa: BLE001 - cualquier fallo externo degrada
            raise LLMExtractionError(f"Fallo en la extracción con IA: {e}") from e

        return Factura.model_validate(data)
