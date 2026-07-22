"""
API REST del servicio. Expone el pipeline por HTTP para integrarlo con otros
sistemas (un ERP, una bandeja de correo, un portal de proveedores). FastAPI
genera además documentación OpenAPI interactiva en /docs.
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .. import __version__
from ..domain.models import ProcessedInvoice
from ..extraction import get_extractor
from ..pipeline import procesar_texto

app = FastAPI(
    title="factura-ai",
    version=__version__,
    description="Procesamiento inteligente de facturas peruanas (IDP): "
                "extracción con IA, validación de negocio y decisión automática.",
)


class ComprobanteIn(BaseModel):
    texto: str = Field(..., min_length=1,
                       description="Texto crudo del comprobante (de un OCR o PDF).")


@app.get("/health")
def health() -> dict:
    """Estado del servicio e indica qué motor de extracción está activo."""
    return {"status": "ok", "version": __version__,
            "extractor": get_extractor().nombre}


@app.post("/facturas/procesar", response_model=ProcessedInvoice)
def procesar(payload: ComprobanteIn) -> ProcessedInvoice:
    """Procesa un comprobante y devuelve los datos extraídos, las validaciones,
    el score de confianza y la decisión (auto-aprobar / revisar / rechazar)."""
    return procesar_texto(payload.texto)
