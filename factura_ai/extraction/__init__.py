"""
Fábrica de extractores. El resto del sistema pide un extractor y no decide cuál:
se usa IA si hay clave configurada, y el extractor por reglas en caso contrario.
"""

from __future__ import annotations

import os

from .base import Extractor
from .llm import LLMExtractionError, LLMExtractor
from .rule_based import RuleBasedExtractor

__all__ = ["Extractor", "RuleBasedExtractor", "LLMExtractor", "get_extractor"]


def get_extractor(preferir_ia: bool = True) -> Extractor:
    """Devuelve el mejor extractor disponible según la configuración del entorno."""
    if preferir_ia and os.getenv("GROQ_API_KEY"):
        try:
            return LLMExtractor()
        except LLMExtractionError:
            pass  # sin clave válida, caemos al determinístico
    return RuleBasedExtractor()
