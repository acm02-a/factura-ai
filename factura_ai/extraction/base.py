"""
Contrato de extracción. Cualquier estrategia (IA o basada en reglas) implementa
la misma interfaz, así el pipeline no sabe ni le importa cuál se usa: se puede
cambiar el motor de extracción sin tocar validación, scoring ni la API.
"""

from __future__ import annotations

from typing import Protocol

from ..domain.models import Factura


class Extractor(Protocol):
    """Convierte el texto crudo de un comprobante en una Factura estructurada."""

    nombre: str

    def extract(self, texto: str) -> Factura:
        ...
