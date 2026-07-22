"""
Modelos de dominio del pipeline. Son la única fuente de verdad sobre la forma
de una factura y su resultado de procesamiento; toda capa (extracción,
validación, API) habla en términos de estos objetos.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    """Un ítem/línea de la factura."""

    descripcion: str
    cantidad: float
    precio_unitario: float
    importe: float


class Factura(BaseModel):
    """Datos estructurados extraídos de una factura o boleta."""

    ruc_emisor: str | None = None
    razon_social: str | None = None
    numero: str | None = None            # serie-correlativo, ej. F001-00001234
    fecha_emision: str | None = None     # ISO 8601 (AAAA-MM-DD)
    moneda: str = "PEN"
    items: list[LineItem] = Field(default_factory=list)
    base_imponible: float | None = None
    igv: float | None = None
    total: float | None = None


class Severidad(str, Enum):
    ERROR = "error"        # bloquea la aprobación automática
    ADVERTENCIA = "advertencia"


class ValidationIssue(BaseModel):
    """Un problema detectado por la capa de validación."""

    campo: str
    mensaje: str
    severidad: Severidad


class Decision(str, Enum):
    AUTO_APROBAR = "auto_aprobar"   # confiable: pasa sin intervención
    REVISAR = "revisar"             # a la cola de revisión humana
    RECHAZAR = "rechazar"           # ilegible/incompleta: reprocesar


class ProcessedInvoice(BaseModel):
    """Resultado completo de pasar una factura por el pipeline."""

    factura: Factura
    issues: list[ValidationIssue] = Field(default_factory=list)
    confianza: float                 # 0–100
    decision: Decision
    extractor: str                   # "llm" | "rule_based"
    fuente: str | None = None        # nombre de archivo u origen

    @property
    def errores(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severidad is Severidad.ERROR]
