"""
Extractor determinístico basado en expresiones regulares.

Sirve para dos cosas: (1) es el fallback cuando no hay clave de IA configurada,
para que el sistema nunca se caiga por una dependencia externa; y (2) es un
baseline barato y auditable contra el cual comparar la extracción con IA.

Asume comprobantes con un layout etiquetado (RUC:, Fecha:, Total:, etc.), que
es el caso de las representaciones impresas/PDF de facturas electrónicas SUNAT.
"""

from __future__ import annotations

import re

from ..domain.models import Factura, LineItem


def _buscar(patron: str, texto: str) -> str | None:
    m = re.search(patron, texto, re.IGNORECASE)
    return m.group(1).strip() if m else None


def _monto(patron: str, texto: str) -> float | None:
    raw = _buscar(patron, texto)
    if raw is None:
        return None
    # Normaliza "1,234.56" o "1 234,56" -> 1234.56
    raw = raw.replace(" ", "").replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None


def _parse_items(texto: str) -> list[LineItem]:
    """Lee las líneas de la sección ITEMS (formato: cant | desc | pu | importe)."""
    items: list[LineItem] = []
    bloque = re.search(r"ITEMS?\s*:?(.+?)(?:BASE|SUBTOTAL|OP\.|IGV|TOTAL)",
                       texto, re.IGNORECASE | re.DOTALL)
    if not bloque:
        return items
    for linea in bloque.group(1).splitlines():
        # cantidad | descripción | precio_unit | importe
        m = re.match(
            r"\s*(\d+(?:\.\d+)?)\s*\|\s*(.+?)\s*\|\s*(\d+(?:\.\d+)?)\s*\|\s*(\d+(?:\.\d+)?)\s*$",
            linea,
        )
        if m:
            items.append(LineItem(
                cantidad=float(m.group(1)),
                descripcion=m.group(2).strip(),
                precio_unitario=float(m.group(3)),
                importe=float(m.group(4)),
            ))
    return items


class RuleBasedExtractor:
    nombre = "rule_based"

    def extract(self, texto: str) -> Factura:
        return Factura(
            ruc_emisor=_buscar(r"RUC\s*:?\s*(\d{11})", texto),
            razon_social=_buscar(r"Raz[oó]n Social\s*:?\s*(.+)", texto),
            numero=_buscar(r"(?:N[°º]|Numero|Comprobante)\s*:?\s*([A-Z]\d{3}-\d{6,8})", texto),
            fecha_emision=_buscar(r"Fecha(?:\s*de\s*emisi[oó]n)?\s*:?\s*(\d{4}-\d{2}-\d{2})", texto),
            moneda=_buscar(r"Moneda\s*:?\s*([A-Z]{3})", texto) or "PEN",
            items=_parse_items(texto),
            base_imponible=_monto(r"(?:Base\s*Imponible|Op\.?\s*Gravada|Subtotal)\s*:?\s*S?/?\.?\s*([\d, ]+\.?\d*)", texto),
            igv=_monto(r"IGV\s*(?:\(18%\))?\s*:?\s*S?/?\.?\s*([\d, ]+\.?\d*)", texto),
            total=_monto(r"(?:Importe\s*Total|Total)\s*:?\s*S?/?\.?\s*([\d, ]+\.?\d*)", texto),
        )
