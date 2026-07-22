"""
Orquestador del pipeline: extraer → validar → puntuar → decidir.

Es el corazón del sistema y, a propósito, es corto y lineal: cada paso vive en
su propio módulo y acá solo se encadenan. Si la extracción con IA falla, se
degrada automáticamente al extractor por reglas antes de rendirse.
"""

from __future__ import annotations

from pathlib import Path

from .domain.models import ProcessedInvoice
from .extraction import Extractor, RuleBasedExtractor, get_extractor
from .extraction.llm import LLMExtractionError
from .scoring import evaluar
from .validation.rules import validar


def procesar_texto(
    texto: str,
    extractor: Extractor | None = None,
    fuente: str | None = None,
) -> ProcessedInvoice:
    """Procesa el texto de un comprobante y devuelve el resultado con su decisión."""
    extractor = extractor or get_extractor()
    try:
        factura = extractor.extract(texto)
        usado = extractor.nombre
    except LLMExtractionError:
        # Degradación con gracia: si la IA falla, usamos el extractor por reglas.
        fallback = RuleBasedExtractor()
        factura = fallback.extract(texto)
        usado = fallback.nombre
    issues = validar(factura)
    return evaluar(factura, issues, extractor=usado, fuente=fuente)


def procesar_archivos(
    rutas: list[Path],
    extractor: Extractor | None = None,
) -> list[ProcessedInvoice]:
    """Procesa un lote de archivos de texto (automatización batch)."""
    extractor = extractor or get_extractor()
    resultados: list[ProcessedInvoice] = []
    for ruta in rutas:
        texto = Path(ruta).read_text(encoding="utf-8")
        resultados.append(procesar_texto(texto, extractor, fuente=Path(ruta).name))
    return resultados
