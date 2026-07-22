"""
Score de confianza y decisión automática.

La confianza combina dos señales:
  1. Completitud — ¿la extracción rellenó los campos clave?
  2. Coherencia   — ¿la factura pasó las reglas de validación?

Con eso se decide el destino de cada documento. La idea de fondo (y lo que hace
esto "de producción") es que el sistema sea explícito sobre qué tan seguro está:
lo muy confiable se auto-aprueba, lo dudoso va a un humano, y lo ilegible se
rechaza para reprocesar. Nunca se "inventa" una aprobación.
"""

from __future__ import annotations

from .domain.models import (
    Decision,
    Factura,
    ProcessedInvoice,
    Severidad,
    ValidationIssue,
)

# Campos que consideramos indispensables en una factura.
CAMPOS_CLAVE = ("ruc_emisor", "numero", "fecha_emision", "total")

# Umbrales de decisión.
UMBRAL_AUTO = 85.0     # >= se auto-aprueba (si no hay errores)
UMBRAL_RECHAZO = 50.0  # <  se rechaza (extracción demasiado pobre)


def _completitud(f: Factura) -> float:
    """Porcentaje de campos clave que la extracción logró rellenar (0–1)."""
    presentes = sum(getattr(f, c) not in (None, "") for c in CAMPOS_CLAVE)
    return presentes / len(CAMPOS_CLAVE)


def calcular_confianza(f: Factura, issues: list[ValidationIssue]) -> float:
    """Devuelve un score 0–100 a partir de completitud y validación."""
    score = _completitud(f) * 100.0
    for issue in issues:
        # Un error pesa mucho más que una advertencia.
        score -= 25.0 if issue.severidad is Severidad.ERROR else 8.0
    return max(0.0, min(100.0, round(score, 1)))


def decidir(confianza: float, issues: list[ValidationIssue]) -> Decision:
    """Traduce el score y los hallazgos en una decisión operativa."""
    tiene_errores = any(i.severidad is Severidad.ERROR for i in issues)
    if confianza < UMBRAL_RECHAZO:
        return Decision.RECHAZAR
    if confianza >= UMBRAL_AUTO and not tiene_errores:
        return Decision.AUTO_APROBAR
    return Decision.REVISAR


def evaluar(
    factura: Factura,
    issues: list[ValidationIssue],
    extractor: str,
    fuente: str | None = None,
) -> ProcessedInvoice:
    """Arma el resultado final con su score y decisión."""
    confianza = calcular_confianza(factura, issues)
    return ProcessedInvoice(
        factura=factura,
        issues=issues,
        confianza=confianza,
        decision=decidir(confianza, issues),
        extractor=extractor,
        fuente=fuente,
    )
