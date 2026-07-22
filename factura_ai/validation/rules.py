"""
Reglas de validación de negocio sobre una factura ya extraída.

Cada regla es una función pura `Factura -> list[ValidationIssue]`. El validador
las corre todas y junta los hallazgos. Separar las reglas así permite agregar,
quitar o testear cada una de forma aislada — y deja explícito el conocimiento
del dominio (cómo funciona el IGV, qué formato tiene un comprobante) en vez de
esconderlo en un `if` gigante.
"""

from __future__ import annotations

from datetime import date, datetime

from ..domain.models import Factura, Severidad, ValidationIssue
from .ruc import es_ruc_valido

# Tasa de IGV vigente en Perú.
TASA_IGV = 0.18
# Tolerancia por redondeo al comparar montos (S/ 0.10).
TOLERANCIA = 0.10


def _issue(campo: str, mensaje: str, sev: Severidad) -> ValidationIssue:
    return ValidationIssue(campo=campo, mensaje=mensaje, severidad=sev)


def validar_ruc(f: Factura) -> list[ValidationIssue]:
    if not f.ruc_emisor:
        return [_issue("ruc_emisor", "Falta el RUC del emisor", Severidad.ERROR)]
    if not es_ruc_valido(f.ruc_emisor):
        return [_issue("ruc_emisor",
                       f"RUC '{f.ruc_emisor}' inválido (dígito verificador no cuadra)",
                       Severidad.ERROR)]
    return []


def validar_numero(f: Factura) -> list[ValidationIssue]:
    if not f.numero:
        return [_issue("numero", "Falta el número de comprobante", Severidad.ERROR)]
    # Formato serie-correlativo, ej. F001-00001234 o B001-00000042.
    import re
    if not re.match(r"^[A-Z]\d{3}-\d{6,8}$", f.numero.strip()):
        return [_issue("numero",
                       f"Número '{f.numero}' no tiene formato serie-correlativo",
                       Severidad.ADVERTENCIA)]
    return []


def validar_fecha(f: Factura) -> list[ValidationIssue]:
    if not f.fecha_emision:
        return [_issue("fecha_emision", "Falta la fecha de emisión", Severidad.ERROR)]
    try:
        fecha = datetime.strptime(f.fecha_emision.strip(), "%Y-%m-%d").date()
    except ValueError:
        return [_issue("fecha_emision",
                       f"Fecha '{f.fecha_emision}' no está en formato AAAA-MM-DD",
                       Severidad.ERROR)]
    if fecha > date.today():
        return [_issue("fecha_emision", "La fecha de emisión es futura",
                       Severidad.ERROR)]
    return []


def validar_igv(f: Factura) -> list[ValidationIssue]:
    """El IGV debe ser el 18% de la base imponible."""
    if f.base_imponible is None or f.igv is None:
        return []  # la completitud la cubre el scorer; acá solo validamos coherencia
    esperado = round(f.base_imponible * TASA_IGV, 2)
    if abs(f.igv - esperado) > TOLERANCIA:
        return [_issue("igv",
                       f"IGV S/ {f.igv:.2f} no coincide con el 18% de la base "
                       f"(esperado S/ {esperado:.2f})",
                       Severidad.ERROR)]
    return []


def validar_total(f: Factura) -> list[ValidationIssue]:
    """Total = base imponible + IGV."""
    if f.base_imponible is None or f.igv is None or f.total is None:
        return []
    esperado = round(f.base_imponible + f.igv, 2)
    if abs(f.total - esperado) > TOLERANCIA:
        return [_issue("total",
                       f"Total S/ {f.total:.2f} no coincide con base + IGV "
                       f"(esperado S/ {esperado:.2f})",
                       Severidad.ERROR)]
    return []


def validar_suma_items(f: Factura) -> list[ValidationIssue]:
    """La suma de los importes de los ítems debe igualar la base imponible."""
    if not f.items or f.base_imponible is None:
        return []
    suma = round(sum(i.importe for i in f.items), 2)
    if abs(suma - f.base_imponible) > TOLERANCIA:
        return [_issue("items",
                       f"La suma de ítems (S/ {suma:.2f}) no coincide con la "
                       f"base imponible (S/ {f.base_imponible:.2f})",
                       Severidad.ADVERTENCIA)]
    return []


# Todas las reglas activas del pipeline.
REGLAS = (
    validar_ruc,
    validar_numero,
    validar_fecha,
    validar_igv,
    validar_total,
    validar_suma_items,
)


def validar(f: Factura) -> list[ValidationIssue]:
    """Corre todas las reglas y devuelve la lista consolidada de hallazgos."""
    issues: list[ValidationIssue] = []
    for regla in REGLAS:
        issues.extend(regla(f))
    return issues
